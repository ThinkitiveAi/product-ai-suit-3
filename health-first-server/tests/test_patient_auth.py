import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
import jwt

from app.services.patient_auth_service import PatientAuthService
from app.schemas.auth import PatientLoginSchema
from app.utils.jwt_handler import jwt_handler
from app.middleware.auth_middleware import get_current_patient
from main import app

class TestPatientAuthService:
    """Test suite for PatientAuthService functionality."""

    @pytest_asyncio.fixture
    async def mock_repository(self):
        """Mock patient repository for testing."""
        mock_repo = AsyncMock()
        return mock_repo

    @pytest_asyncio.fixture 
    async def auth_service(self, mock_repository):
        """Create PatientAuthService instance with mocked repository."""
        with patch('app.services.patient_auth_service.get_patient_repository', return_value=mock_repository):
            service = PatientAuthService()
            service.repository = mock_repository
            return service

    @pytest_asyncio.fixture
    async def sample_patient(self):
        """Sample patient data for testing."""
        return {
            "patient_id": "test-patient-123",
            "email": "jane.smith@email.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewrBkOxK2cDamN/.",  # "password123"
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "phone_number": "+1234567890",
            "address": {
                "street": "123 Main St",
                "city": "Anytown", 
                "state": "CA",
                "zip": "12345"
            },
            "email_verified": True,
            "phone_verified": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

    @pytest.mark.asyncio
    async def test_authenticate_patient_success(self, auth_service, mock_repository, sample_patient):
        """Test successful patient authentication."""
        # Arrange
        login_data = PatientLoginSchema(email="jane.smith@email.com", password="password123")
        mock_repository.get_patient_by_email.return_value = sample_patient

        with patch('app.services.patient_auth_service.verify_password', return_value=True), \
             patch('app.utils.jwt_handler.jwt_handler.generate_patient_access_token') as mock_jwt:
            
            mock_jwt.return_value = {
                "access_token": "test-token",
                "expires_in": 1800,
                "token_type": "Bearer"
            }

            # Act
            success, response_data = await auth_service.authenticate_patient(login_data)

            # Assert
            assert success is True
            assert response_data["success"] is True
            assert response_data["message"] == "Login successful"
            assert "access_token" in response_data["data"]
            assert "patient" in response_data["data"]
            assert "password_hash" not in response_data["data"]["patient"]

    @pytest.mark.asyncio
    async def test_authenticate_patient_invalid_email(self, auth_service, mock_repository):
        """Test authentication with non-existent email."""
        # Arrange
        login_data = PatientLoginSchema(email="nonexistent@email.com", password="password123")
        mock_repository.get_patient_by_email.return_value = None

        # Act
        success, response_data = await auth_service.authenticate_patient(login_data)

        # Assert
        assert success is False
        assert response_data["success"] is False
        assert response_data["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_authenticate_patient_invalid_password(self, auth_service, mock_repository, sample_patient):
        """Test authentication with invalid password."""
        # Arrange
        login_data = PatientLoginSchema(email="jane.smith@email.com", password="wrongpassword")
        mock_repository.get_patient_by_email.return_value = sample_patient

        with patch('app.services.patient_auth_service.verify_password', return_value=False):
            # Act
            success, response_data = await auth_service.authenticate_patient(login_data)

            # Assert
            assert success is False
            assert response_data["success"] is False
            assert response_data["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_authenticate_patient_inactive_account(self, auth_service, mock_repository, sample_patient):
        """Test authentication with inactive account."""
        # Arrange
        login_data = PatientLoginSchema(email="jane.smith@email.com", password="password123")
        sample_patient["is_active"] = False
        mock_repository.get_patient_by_email.return_value = sample_patient

        with patch('app.services.patient_auth_service.verify_password', return_value=True):
            # Act
            success, response_data = await auth_service.authenticate_patient(login_data)

            # Assert
            assert success is False
            assert response_data["success"] is False
            assert response_data["error_code"] == "ACCOUNT_DEACTIVATED"

    @pytest.mark.asyncio
    async def test_validate_token_success(self, auth_service, mock_repository, sample_patient):
        """Test successful token validation."""
        # Arrange
        valid_token = "valid-jwt-token"
        mock_payload = {
            "patient_id": "test-patient-123",
            "email": "jane.smith@email.com",
            "role": "patient",
            "is_active": True,
            "email_verified": True,
            "phone_verified": False,
            "exp": (datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()
        }
        
        mock_repository.get_patient_by_email.return_value = sample_patient

        with patch('app.utils.jwt_handler.jwt_handler.verify_access_token', return_value=mock_payload):
            # Act
            result = await auth_service.validate_token(valid_token)

            # Assert
            assert result["valid"] is True
            assert result["patient_id"] == "test-patient-123"
            assert result["email"] == "jane.smith@email.com"

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, auth_service):
        """Test token validation with invalid token."""
        # Arrange
        invalid_token = "invalid-jwt-token"

        with patch('app.utils.jwt_handler.jwt_handler.verify_access_token', return_value=None):
            # Act
            result = await auth_service.validate_token(invalid_token)

            # Assert
            assert result["valid"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_validate_token_wrong_role(self, auth_service):
        """Test token validation with provider token (wrong role)."""
        # Arrange
        provider_token = "provider-jwt-token"
        mock_payload = {
            "provider_id": "test-provider-123",
            "email": "doctor@clinic.com",
            "role": "provider",
            "is_active": True,
            "verification_status": "verified"
        }

        with patch('app.utils.jwt_handler.jwt_handler.verify_access_token', return_value=mock_payload):
            # Act
            result = await auth_service.validate_token(provider_token)

            # Assert
            assert result["valid"] is False
            assert result["error"] == "Invalid token type"

    @pytest.mark.asyncio
    async def test_get_current_patient_success(self, auth_service, mock_repository, sample_patient):
        """Test getting current patient data."""
        # Arrange
        patient_id = "test-patient-123"
        mock_repository.get_patient_by_id.return_value = sample_patient

        # Act
        result = await auth_service.get_current_patient(patient_id)

        # Assert
        assert result is not None
        assert result["patient_id"] == patient_id
        assert "password_hash" not in result

    @pytest.mark.asyncio
    async def test_get_current_patient_not_found(self, auth_service, mock_repository):
        """Test getting current patient when patient doesn't exist."""
        # Arrange
        patient_id = "nonexistent-patient"
        mock_repository.get_patient_by_id.return_value = None

        # Act
        result = await auth_service.get_current_patient(patient_id)

        # Assert
        assert result is None

class TestJWTHandler:
    """Test suite for JWT handler patient token functionality."""

    def test_generate_patient_access_token(self, sample_patient):
        """Test patient access token generation."""
        # Act
        token_data = jwt_handler.generate_patient_access_token(sample_patient)

        # Assert
        assert "access_token" in token_data
        assert token_data["expires_in"] == 1800  # 30 minutes in seconds
        assert token_data["token_type"] == "Bearer"

        # Decode token to verify payload
        decoded = jwt.decode(
            token_data["access_token"], 
            jwt_handler.secret_key, 
            algorithms=[jwt_handler.algorithm]
        )
        assert decoded["role"] == "patient"
        assert decoded["patient_id"] == sample_patient["patient_id"]
        assert decoded["email"] == sample_patient["email"]

    def test_verify_patient_access_token(self, sample_patient):
        """Test patient access token verification."""
        # Arrange
        token_data = jwt_handler.generate_patient_access_token(sample_patient)
        token = token_data["access_token"]

        # Act
        payload = jwt_handler.verify_access_token(token)

        # Assert
        assert payload is not None
        assert payload["role"] == "patient"
        assert payload["patient_id"] == sample_patient["patient_id"]
        assert payload["email"] == sample_patient["email"]

    def test_verify_expired_patient_token(self, sample_patient):
        """Test verification of expired patient token."""
        # Arrange - create token with past expiry
        expire = datetime.now(timezone.utc) - timedelta(minutes=5)  # 5 minutes ago
        payload = {
            "patient_id": sample_patient["patient_id"],
            "email": sample_patient["email"],
            "role": "patient",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access_token"
        }
        expired_token = jwt.encode(payload, jwt_handler.secret_key, algorithm=jwt_handler.algorithm)

        # Act
        result = jwt_handler.verify_access_token(expired_token)

        # Assert
        assert result is None

class TestPatientAuthEndpoints:
    """Test suite for patient authentication endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def valid_login_data(self):
        """Valid login data for testing."""
        return {
            "email": "jane.smith@email.com", 
            "password": "password123"
        }

    @pytest.fixture
    def sample_patient_for_endpoint(self):
        """Sample patient data for endpoint testing."""
        return {
            "patient_id": "test-patient-123",
            "email": "jane.smith@email.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewrBkOxK2cDamN/.",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "phone_number": "+1234567890",
            "email_verified": True,
            "phone_verified": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

    def test_patient_login_success(self, client, valid_login_data, sample_patient_for_endpoint):
        """Test successful patient login endpoint."""
        with patch('app.services.patient_auth_service.PatientAuthService.authenticate_patient') as mock_auth:
            mock_auth.return_value = (True, {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": "test-token",
                    "expires_in": 1800,
                    "token_type": "Bearer",
                    "patient": sample_patient_for_endpoint
                }
            })

            # Act
            response = client.post("/api/v1/patient/login", json=valid_login_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
            assert "patient" in data["data"]

    def test_patient_login_invalid_credentials(self, client, valid_login_data):
        """Test patient login with invalid credentials."""
        with patch('app.services.patient_auth_service.PatientAuthService.authenticate_patient') as mock_auth:
            mock_auth.return_value = (False, {
                "success": False,
                "message": "Invalid credentials",
                "error_code": "INVALID_CREDENTIALS"
            })

            # Act
            response = client.post("/api/v1/patient/login", json=valid_login_data)

            # Assert
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_patient_login_validation_error(self, client):
        """Test patient login with validation errors."""
        # Arrange
        invalid_data = {
            "email": "invalid-email",
            "password": ""
        }

        # Act
        response = client.post("/api/v1/patient/login", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_validate_patient_token_endpoint(self, client):
        """Test patient token validation endpoint."""
        with patch('app.services.patient_auth_service.PatientAuthService.validate_token') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "patient_id": "test-patient-123",
                "email": "jane.smith@email.com"
            }

            # Act
            response = client.post("/api/v1/patient/validate-token", json={"token": "test-token"})

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["valid"] is True

    def test_get_patient_profile_success(self, client, sample_patient_for_endpoint):
        """Test getting patient profile with valid token."""
        with patch('app.middleware.auth_middleware.get_current_patient') as mock_get_patient:
            mock_get_patient.return_value = sample_patient_for_endpoint

            # Act
            response = client.get(
                "/api/v1/patient/profile",
                headers={"Authorization": "Bearer test-token"}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "patient_id" in data["data"]

    def test_get_patient_profile_unauthorized(self, client):
        """Test getting patient profile without token."""
        # Act
        response = client.get("/api/v1/patient/profile")

        # Assert
        assert response.status_code == 401

class TestPatientAuthMiddleware:
    """Test suite for patient authentication middleware."""

    @pytest.fixture
    def mock_credentials(self):
        """Mock HTTP authorization credentials."""
        mock_creds = MagicMock()
        mock_creds.credentials = "valid-token"
        return mock_creds

    @pytest.mark.asyncio
    async def test_get_current_patient_success(self, mock_credentials, sample_patient):
        """Test successful patient authentication middleware."""
        with patch('app.services.patient_auth_service.PatientAuthService.validate_token') as mock_validate, \
             patch('app.services.patient_auth_service.PatientAuthService.get_current_patient') as mock_get_patient:
            
            mock_validate.return_value = {
                "valid": True,
                "patient_id": "test-patient-123"
            }
            mock_get_patient.return_value = sample_patient

            from app.middleware.auth_middleware import AuthMiddleware
            middleware = AuthMiddleware()

            # Act
            result = await middleware.get_current_patient(mock_credentials)

            # Assert
            assert result == sample_patient

    @pytest.mark.asyncio 
    async def test_get_current_patient_invalid_token(self, mock_credentials):
        """Test patient authentication middleware with invalid token."""
        with patch('app.services.patient_auth_service.PatientAuthService.validate_token') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "error": "Invalid token"
            }

            from app.middleware.auth_middleware import AuthMiddleware
            middleware = AuthMiddleware()

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await middleware.get_current_patient(mock_credentials)
            
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_patient_missing_credentials(self):
        """Test patient authentication middleware with missing credentials."""
        from app.middleware.auth_middleware import AuthMiddleware
        middleware = AuthMiddleware()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await middleware.get_current_patient(None)
        
        assert exc_info.value.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__]) 