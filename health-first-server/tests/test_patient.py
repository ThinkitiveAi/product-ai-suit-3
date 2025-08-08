import pytest
from datetime import date, datetime
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import json

from app.schemas.patient import PatientRegistrationSchema, Gender, AddressSchema
from app.services.patient_service import PatientService
from app.utils.security import hash_password, verify_password
from main import app

# Test client
client = TestClient(app)

class TestPatientValidation:
    """Test patient schema validation."""
    
    def test_valid_patient_registration_schema(self):
        """Test valid patient registration data."""
        valid_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@email.com",
            "phone_number": "+12125551234",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "address": {
                "street": "456 Main Street",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        schema = PatientRegistrationSchema(**valid_data)
        assert schema.first_name == "Jane"
        assert schema.last_name == "Smith"
        assert schema.email == "jane.smith@email.com"
        assert schema.phone_number == "+12125551234"
        assert schema.gender == Gender.FEMALE
        assert schema.date_of_birth == date(1990, 5, 15)
    
    def test_age_validation_coppa_compliance(self):
        """Test COPPA compliance - minimum age 13."""
        # Test with age < 13 (should fail)
        with pytest.raises(ValueError, match="Must be at least 13 years old"):
            today = date.today()
            too_young_date = date(today.year - 12, today.month, today.day)
            
            PatientRegistrationSchema(
                first_name="Child",
                last_name="User",
                email="child@email.com",
                phone_number="+12125551234",
                password="SecurePassword123!",
                confirm_password="SecurePassword123!",
                date_of_birth=too_young_date,
                gender="male",
                address={
                    "street": "123 Test St",
                    "city": "Test City",
                    "state": "TS",
                    "zip": "12345"
                }
            )
    
    def test_password_strength_validation(self):
        """Test password strength requirements."""
        base_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@email.com",
            "phone_number": "+12125551234",
            "confirm_password": "weak",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "address": {
                "street": "456 Main Street",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        # Test weak password
        with pytest.raises(ValueError):
            PatientRegistrationSchema(**{**base_data, "password": "weak"})
        
        # Test password without uppercase
        with pytest.raises(ValueError):
            PatientRegistrationSchema(**{**base_data, "password": "weakpassword123!"})
        
        # Test password without special character
        with pytest.raises(ValueError):
            PatientRegistrationSchema(**{**base_data, "password": "WeakPassword123"})
    
    def test_phone_number_validation(self):
        """Test phone number format validation."""
        base_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@email.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "address": {
                "street": "456 Main Street",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        # Test invalid phone number
        with pytest.raises(ValueError, match="Invalid phone number format"):
            PatientRegistrationSchema(**{**base_data, "phone_number": "1234567890"})
        
        # Test valid phone number
        schema = PatientRegistrationSchema(**{**base_data, "phone_number": "+12125551234"})
        assert schema.phone_number == "+12125551234"
    
    def test_gender_enum_validation(self):
        """Test gender enum validation."""
        valid_genders = ["male", "female", "other", "prefer_not_to_say"]
        
        for gender in valid_genders:
            data = {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@email.com",
                "phone_number": "+12125551234",
                "password": "SecurePassword123!",
                "confirm_password": "SecurePassword123!",
                "date_of_birth": "1990-05-15",
                "gender": gender,
                "address": {
                    "street": "123 Test St",
                    "city": "Test City",
                    "state": "TS",
                    "zip": "12345"
                }
            }
            schema = PatientRegistrationSchema(**data)
            assert schema.gender.value == gender

class TestPatientService:
    """Test patient service business logic."""
    
    @pytest.mark.asyncio
    async def test_successful_patient_registration(self):
        """Test successful patient registration."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_patient_by_email.return_value = None
        mock_repo.get_patient_by_phone.return_value = None
        mock_repo.create_patient.return_value = {
            "patient_id": "test-id",
            "email": "jane.smith@email.com",
            "phone_number": "+12125551234",
            "email_verified": False,
            "phone_verified": False
        }
        
        service = PatientService()
        service.repository = mock_repo
        
        registration_data = PatientRegistrationSchema(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@email.com",
            phone_number="+12125551234",
            password="SecurePassword123!",
            confirm_password="SecurePassword123!",
            date_of_birth="1990-05-15",
            gender="female",
            address=AddressSchema(
                street="456 Main Street",
                city="Boston",
                state="MA",
                zip="02101"
            )
        )
        
        success, response = await service.register_patient(registration_data)
        
        assert success is True
        assert response["success"] is True
        assert response["data"]["email"] == "jane.smith@email.com"
        assert "password" not in str(response)  # Ensure no password in response
    
    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self):
        """Test registration with duplicate email."""
        mock_repo = AsyncMock()
        mock_repo.get_patient_by_email.return_value = {"email": "jane.smith@email.com"}
        
        service = PatientService()
        service.repository = mock_repo
        
        registration_data = PatientRegistrationSchema(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@email.com",
            phone_number="+12125551234",
            password="SecurePassword123!",
            confirm_password="SecurePassword123!",
            date_of_birth="1990-05-15",
            gender="female",
            address=AddressSchema(
                street="456 Main Street",
                city="Boston",
                state="MA",
                zip="02101"
            )
        )
        
        success, response = await service.register_patient(registration_data)
        
        assert success is False
        assert "already registered" in response["message"]
        assert "email" in response["errors"]

class TestPatientSecurity:
    """Test patient security features."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        # Ensure hash is different from original password
        assert hashed != password
        
        # Ensure verification works
        assert verify_password(password, hashed) is True
        
        # Ensure wrong password fails
        assert verify_password("WrongPassword", hashed) is False
    
    def test_medical_history_sanitization(self):
        """Test medical history input sanitization."""
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@email.com",
            "phone_number": "+12125551234",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "address": {
                "street": "456 Main Street",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            },
            "medical_history": [
                "Diabetes Type 2",
                "",  # Empty string should be filtered
                "   ",  # Whitespace should be filtered
                "High Blood Pressure"
            ]
        }
        
        schema = PatientRegistrationSchema(**data)
        # Empty and whitespace-only entries should be filtered
        assert len(schema.medical_history) == 2
        assert "Diabetes Type 2" in schema.medical_history
        assert "High Blood Pressure" in schema.medical_history

class TestPatientAPI:
    """Test patient API endpoints."""
    
    def test_patient_registration_endpoint(self):
        """Test patient registration API endpoint."""
        # This test requires mocking the database layer
        # For now, testing the endpoint structure
        
        # Test validation endpoint
        response = client.get("/api/v1/patient/validate?email=test@example.com")
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "errors" in data
    
    def test_api_docs_include_patient_endpoints(self):
        """Test that API documentation includes patient endpoints."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi_spec = response.json()
        
        # Check that patient endpoints are included
        paths = openapi_spec.get("paths", {})
        assert "/api/v1/patient/register" in paths
        assert "/api/v1/patient/validate" in paths
        assert "/api/v1/patient/{patient_id}" in paths
    
    def test_root_endpoint_includes_patient_features(self):
        """Test that root endpoint mentions patient registration."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        
        assert "Patient Registration" in data["features"]
        assert "patient_registration" in data["endpoints"]
        assert "HIPAA Compliance" in data["features"]

if __name__ == "__main__":
    pytest.main([__file__]) 