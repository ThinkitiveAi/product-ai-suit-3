import pytest
import json
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta
from app.utils.jwt_handler import jwt_handler
from app.services.auth_service import AuthService
from app.schemas.auth import ProviderLoginSchema
from app.utils.security import hash_password

class TestJWTHandler:
    """Test JWT token generation and validation."""
    
    def test_generate_access_token(self):
        """Test JWT token generation."""
        provider_data = {
            "provider_id": "test-provider-id",
            "email": "test@example.com",
            "specialization": "Cardiology",
            "verification_status": "verified",
            "is_active": True
        }
        
        token_data = jwt_handler.generate_access_token(provider_data)
        
        assert "access_token" in token_data
        assert "expires_in" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "Bearer"
        assert token_data["expires_in"] == 3600  # 1 hour
        assert isinstance(token_data["access_token"], str)
    
    def test_verify_valid_token(self):
        """Test JWT token verification with valid token."""
        provider_data = {
            "provider_id": "test-provider-id",
            "email": "test@example.com",
            "specialization": "Cardiology",
            "verification_status": "verified",
            "is_active": True
        }
        
        token_data = jwt_handler.generate_access_token(provider_data)
        token = token_data["access_token"]
        
        payload = jwt_handler.verify_access_token(token)
        
        assert payload is not None
        assert payload["provider_id"] == "test-provider-id"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access_token"
        assert payload["verification_status"] == "verified"
        assert payload["is_active"] is True
    
    def test_verify_invalid_token(self):
        """Test JWT token verification with invalid token."""
        invalid_token = "invalid.jwt.token"
        
        payload = jwt_handler.verify_access_token(invalid_token)
        
        assert payload is None
    
    def test_verify_expired_token(self):
        """Test JWT token verification with expired token."""
        # Create a token that expires immediately
        original_expire = jwt_handler.access_token_expire_hours
        jwt_handler.access_token_expire_hours = -1  # Negative hours = expired
        
        provider_data = {
            "provider_id": "test-provider-id",
            "email": "test@example.com",
            "specialization": "Cardiology",
            "verification_status": "verified",
            "is_active": True
        }
        
        token_data = jwt_handler.generate_access_token(provider_data)
        token = token_data["access_token"]
        
        # Restore original expire time
        jwt_handler.access_token_expire_hours = original_expire
        
        payload = jwt_handler.verify_access_token(token)
        
        assert payload is None
    
    def test_extract_token_from_header(self):
        """Test token extraction from Authorization header."""
        # Valid Bearer token
        valid_header = "Bearer valid.jwt.token"
        token = jwt_handler.extract_token_from_header(valid_header)
        assert token == "valid.jwt.token"
        
        # Invalid format
        invalid_headers = [
            "InvalidFormat token",
            "Bearer",
            "Bearer token1 token2",
            "",
            None
        ]
        
        for header in invalid_headers:
            token = jwt_handler.extract_token_from_header(header)
            assert token is None

class TestAuthService:
    """Test authentication service functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self):
        """Test successful provider authentication."""
        # Mock provider data
        provider_data = {
            "provider_id": "test-id",
            "email": "test@example.com",
            "password_hash": hash_password("SecurePassword123!"),
            "verification_status": "verified",
            "is_active": True,
            "first_name": "John",
            "last_name": "Doe",
            "specialization": "Cardiology"
        }
        
        auth_service = AuthService()
        
        with patch.object(auth_service.repository, 'get_provider_by_email', return_value=provider_data):
            login_data = ProviderLoginSchema(
                email="test@example.com",
                password="SecurePassword123!"
            )
            
            success, response = await auth_service.authenticate_provider(login_data)
            
            assert success is True
            assert response["success"] is True
            assert "access_token" in response["data"]
            assert response["data"]["token_type"] == "Bearer"
            assert "provider" in response["data"]
            
            # Ensure password_hash is not in response
            assert "password_hash" not in str(response)
    
    @pytest.mark.asyncio
    async def test_authentication_invalid_email(self):
        """Test authentication with non-existent email."""
        auth_service = AuthService()
        
        with patch.object(auth_service.repository, 'get_provider_by_email', return_value=None):
            login_data = ProviderLoginSchema(
                email="nonexistent@example.com",
                password="password123"
            )
            
            success, response = await auth_service.authenticate_provider(login_data)
            
            assert success is False
            assert response["error_code"] == "INVALID_CREDENTIALS"
    
    @pytest.mark.asyncio
    async def test_authentication_invalid_password(self):
        """Test authentication with wrong password."""
        provider_data = {
            "provider_id": "test-id",
            "email": "test@example.com",
            "password_hash": hash_password("CorrectPassword123!"),
            "verification_status": "verified",
            "is_active": True
        }
        
        auth_service = AuthService()
        
        with patch.object(auth_service.repository, 'get_provider_by_email', return_value=provider_data):
            login_data = ProviderLoginSchema(
                email="test@example.com",
                password="WrongPassword123!"
            )
            
            success, response = await auth_service.authenticate_provider(login_data)
            
            assert success is False
            assert response["error_code"] == "INVALID_CREDENTIALS"
    
    @pytest.mark.asyncio
    async def test_authentication_inactive_account(self):
        """Test authentication with inactive account."""
        provider_data = {
            "provider_id": "test-id",
            "email": "test@example.com",
            "password_hash": hash_password("SecurePassword123!"),
            "verification_status": "verified",
            "is_active": False  # Inactive account
        }
        
        auth_service = AuthService()
        
        with patch.object(auth_service.repository, 'get_provider_by_email', return_value=provider_data):
            login_data = ProviderLoginSchema(
                email="test@example.com",
                password="SecurePassword123!"
            )
            
            success, response = await auth_service.authenticate_provider(login_data)
            
            assert success is False
            assert response["error_code"] == "ACCOUNT_DEACTIVATED"
    
    @pytest.mark.asyncio
    async def test_authentication_unverified_account(self):
        """Test authentication with unverified account."""
        provider_data = {
            "provider_id": "test-id",
            "email": "test@example.com",
            "password_hash": hash_password("SecurePassword123!"),
            "verification_status": "pending",  # Unverified account
            "is_active": True
        }
        
        auth_service = AuthService()
        
        with patch.object(auth_service.repository, 'get_provider_by_email', return_value=provider_data):
            login_data = ProviderLoginSchema(
                email="test@example.com",
                password="SecurePassword123!"
            )
            
            success, response = await auth_service.authenticate_provider(login_data)
            
            assert success is False
            assert response["error_code"] == "ACCOUNT_NOT_VERIFIED"
    
    @pytest.mark.asyncio
    async def test_token_validation_valid_token(self):
        """Test token validation with valid token."""
        provider_data = {
            "provider_id": "test-id",
            "email": "test@example.com",
            "specialization": "Cardiology",
            "verification_status": "verified",
            "is_active": True
        }
        
        token_data = jwt_handler.generate_access_token(provider_data)
        token = token_data["access_token"]
        
        auth_service = AuthService()
        
        with patch.object(auth_service.repository, 'get_provider_by_email', return_value=provider_data):
            result = await auth_service.validate_token(token)
            
            assert result["valid"] is True
            assert result["provider_id"] == "test-id"
            assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_token_validation_invalid_token(self):
        """Test token validation with invalid token."""
        auth_service = AuthService()
        
        result = await auth_service.validate_token("invalid.token")
        
        assert result["valid"] is False
        assert "error" in result

class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_login_endpoint_success(self, client):
        """Test successful login endpoint."""
        with patch('app.api.auth_endpoints.auth_service') as mock_service:
            mock_service.authenticate_provider.return_value = (True, {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": "test.jwt.token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "provider": {
                        "provider_id": "test-id",
                        "email": "test@example.com",
                        "verification_status": "verified"
                    }
                }
            })
            
            login_data = {
                "email": "test@example.com",
                "password": "SecurePassword123!"
            }
            
            response = client.post("/api/v1/provider/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
    
    def test_login_endpoint_invalid_credentials(self, client):
        """Test login endpoint with invalid credentials."""
        with patch('app.api.auth_endpoints.auth_service') as mock_service:
            mock_service.authenticate_provider.return_value = (False, {
                "success": False,
                "message": "Invalid credentials",
                "error_code": "INVALID_CREDENTIALS"
            })
            
            login_data = {
                "email": "test@example.com",
                "password": "wrongpassword"
            }
            
            response = client.post("/api/v1/provider/login", json=login_data)
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "INVALID_CREDENTIALS"
    
    def test_login_endpoint_validation_error(self, client):
        """Test login endpoint with validation errors."""
        invalid_data = {
            "email": "invalid-email",
            "password": ""
        }
        
        response = client.post("/api/v1/provider/login", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "errors" in data
    
    def test_verify_token_endpoint(self, client):
        """Test token verification endpoint."""
        with patch('app.api.auth_endpoints.get_optional_current_provider') as mock_dep:
            mock_dep.return_value = {
                "provider_id": "test-id",
                "email": "test@example.com",
                "verification_status": "verified",
                "is_active": True
            }
            
            response = client.get("/api/v1/provider/verify-token")
            
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
    
    def test_me_endpoint_authenticated(self, client):
        """Test /me endpoint with authentication."""
        with patch('app.api.auth_endpoints.get_current_provider') as mock_dep:
            mock_dep.return_value = {
                "provider_id": "test-id",
                "email": "test@example.com",
                "first_name": "John",
                "last_name": "Doe"
            }
            
            response = client.get("/api/v1/provider/me")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["email"] == "test@example.com"
    
    def test_logout_endpoint(self, client):
        """Test logout endpoint."""
        with patch('app.api.auth_endpoints.get_current_provider') as mock_dep:
            mock_dep.return_value = {
                "provider_id": "test-id",
                "email": "test@example.com"
            }
            
            response = client.post("/api/v1/provider/logout")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Logout successful" 