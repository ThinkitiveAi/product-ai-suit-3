import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

class TestProviderRegistrationEndpoint:
    """Test provider registration API endpoint."""
    
    def test_successful_registration(self, client, valid_provider_data):
        """Test successful provider registration."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            # Mock successful registration
            mock_service.register_provider.return_value = (True, {
                "success": True,
                "message": "Provider registered successfully. Verification email sent.",
                "data": {
                    "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "john.doe@clinic.com",
                    "verification_status": "pending"
                }
            })
            
            response = client.post("/api/v1/provider/register", json=valid_provider_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "provider_id" in data["data"]
            assert data["data"]["email"] == valid_provider_data["email"]
    
    def test_validation_error_response(self, client, invalid_provider_data):
        """Test validation error response for invalid data."""
        response = client.post("/api/v1/provider/register", json=invalid_provider_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "errors" in data
        assert isinstance(data["errors"], dict)
    
    def test_duplicate_email_conflict(self, client, valid_provider_data):
        """Test duplicate email conflict response."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            # Mock duplicate email response
            mock_service.register_provider.return_value = (False, {
                "success": False,
                "message": "Email address is already registered",
                "errors": {"email": ["This email address is already registered"]}
            })
            
            response = client.post("/api/v1/provider/register", json=valid_provider_data)
            
            assert response.status_code == 409
            data = response.json()
            assert data["success"] is False
            assert "email" in data["errors"]
    
    def test_duplicate_phone_conflict(self, client, valid_provider_data):
        """Test duplicate phone number conflict response."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            # Mock duplicate phone response
            mock_service.register_provider.return_value = (False, {
                "success": False,
                "message": "Phone number is already registered",
                "errors": {"phone_number": ["This phone number is already registered"]}
            })
            
            response = client.post("/api/v1/provider/register", json=valid_provider_data)
            
            assert response.status_code == 409
            data = response.json()
            assert data["success"] is False
            assert "phone_number" in data["errors"]
    
    def test_duplicate_license_conflict(self, client, valid_provider_data):
        """Test duplicate license number conflict response."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            # Mock duplicate license response
            mock_service.register_provider.return_value = (False, {
                "success": False,
                "message": "License number is already registered",
                "errors": {"license_number": ["This license number is already registered"]}
            })
            
            response = client.post("/api/v1/provider/register", json=valid_provider_data)
            
            assert response.status_code == 409
            data = response.json()
            assert data["success"] is False
            assert "license_number" in data["errors"]
    
    def test_server_error_response(self, client, valid_provider_data):
        """Test server error response."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            # Mock server error response
            mock_service.register_provider.return_value = (False, {
                "success": False,
                "message": "Registration failed due to server error. Please try again later.",
                "errors": {"server": ["Internal server error"]}
            })
            
            response = client.post("/api/v1/provider/register", json=valid_provider_data)
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "server" in data["errors"]
    
    def test_missing_required_fields(self, client):
        """Test response when required fields are missing."""
        incomplete_data = {
            "first_name": "John",
            "email": "john@clinic.com"
            # Missing many required fields
        }
        
        response = client.post("/api/v1/provider/register", json=incomplete_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "errors" in data
    
    def test_invalid_json_format(self, client):
        """Test response for invalid JSON format."""
        response = client.post(
            "/api/v1/provider/register",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422

class TestUniqueFieldValidationEndpoint:
    """Test unique field validation endpoint."""
    
    def test_validate_unique_fields_all_valid(self, client):
        """Test validation endpoint when all fields are unique."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            mock_service.validate_unique_fields.return_value = {
                "is_valid": True,
                "errors": {}
            }
            
            response = client.get(
                "/api/v1/provider/validate",
                params={
                    "email": "new@clinic.com",
                    "phone_number": "+1111111111",
                    "license_number": "NEW123456"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert len(data["errors"]) == 0
    
    def test_validate_unique_fields_with_duplicates(self, client):
        """Test validation endpoint when fields are not unique."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            mock_service.validate_unique_fields.return_value = {
                "is_valid": False,
                "errors": {
                    "email": ["This email address is already registered"]
                }
            }
            
            response = client.get(
                "/api/v1/provider/validate",
                params={"email": "existing@clinic.com"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert "email" in data["errors"]
    
    def test_validate_partial_fields(self, client):
        """Test validation endpoint with only some fields."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            mock_service.validate_unique_fields.return_value = {
                "is_valid": True,
                "errors": {}
            }
            
            response = client.get(
                "/api/v1/provider/validate",
                params={"email": "test@clinic.com"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True

class TestGetProviderEndpoint:
    """Test get provider endpoint."""
    
    def test_get_existing_provider(self, client):
        """Test getting an existing provider."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            mock_provider = {
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@clinic.com",
                "verification_status": "pending"
            }
            mock_service.get_provider_by_id.return_value = mock_provider
            
            response = client.get("/api/v1/provider/550e8400-e29b-41d4-a716-446655440000")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["provider_id"] == "550e8400-e29b-41d4-a716-446655440000"
    
    def test_get_nonexistent_provider(self, client):
        """Test getting a provider that doesn't exist."""
        with patch('app.api.provider_endpoints.provider_service') as mock_service:
            mock_service.get_provider_by_id.return_value = {}
            
            response = client.get("/api/v1/provider/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["message"]

class TestHealthCheckEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health")
        
        # Should return 200 or 503 depending on database status
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database_type" in data 