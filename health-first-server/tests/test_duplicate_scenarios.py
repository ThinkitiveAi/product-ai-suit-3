import pytest
from unittest.mock import AsyncMock
from app.services.provider_service import ProviderService
from app.schemas.provider import ProviderRegistrationSchema

class TestDuplicateScenarios:
    """Test duplicate validation scenarios."""
    
    @pytest.mark.asyncio
    async def test_duplicate_email_detection(self, provider_service_with_mock_repo, valid_provider_data):
        """Test that duplicate email addresses are detected."""
        # Mock repository to return existing provider with same email
        existing_provider = {
            "provider_id": "existing-id",
            "email": "john.doe@clinic.com",
            "phone_number": "+9999999999",
            "license_number": "EXISTING123"
        }
        
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = existing_provider
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = None
        
        # Attempt registration
        registration_data = ProviderRegistrationSchema(**valid_provider_data)
        success, response = await provider_service_with_mock_repo.register_provider(registration_data)
        
        # Should fail due to duplicate email
        assert not success
        assert "email" in response["errors"]
        assert "already registered" in response["errors"]["email"][0]
    
    @pytest.mark.asyncio
    async def test_duplicate_phone_detection(self, provider_service_with_mock_repo, valid_provider_data):
        """Test that duplicate phone numbers are detected."""
        # Mock repository to return existing provider with same phone
        existing_provider = {
            "provider_id": "existing-id",
            "email": "different@clinic.com",
            "phone_number": "+1234567890",
            "license_number": "EXISTING123"
        }
        
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = existing_provider
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = None
        
        # Attempt registration
        registration_data = ProviderRegistrationSchema(**valid_provider_data)
        success, response = await provider_service_with_mock_repo.register_provider(registration_data)
        
        # Should fail due to duplicate phone
        assert not success
        assert "phone_number" in response["errors"]
        assert "already registered" in response["errors"]["phone_number"][0]
    
    @pytest.mark.asyncio
    async def test_duplicate_license_detection(self, provider_service_with_mock_repo, valid_provider_data):
        """Test that duplicate license numbers are detected."""
        # Mock repository to return existing provider with same license
        existing_provider = {
            "provider_id": "existing-id",
            "email": "different@clinic.com",
            "phone_number": "+9999999999",
            "license_number": "MD123456789"
        }
        
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = existing_provider
        
        # Attempt registration
        registration_data = ProviderRegistrationSchema(**valid_provider_data)
        success, response = await provider_service_with_mock_repo.register_provider(registration_data)
        
        # Should fail due to duplicate license
        assert not success
        assert "license_number" in response["errors"]
        assert "already registered" in response["errors"]["license_number"][0]
    
    @pytest.mark.asyncio
    async def test_multiple_duplicates_detection(self, provider_service_with_mock_repo, valid_provider_data):
        """Test detection when multiple fields are duplicated."""
        # Mock repository to return existing providers for multiple fields
        existing_email_provider = {
            "provider_id": "existing-email-id",
            "email": "john.doe@clinic.com"
        }
        existing_phone_provider = {
            "provider_id": "existing-phone-id", 
            "phone_number": "+1234567890"
        }
        
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = existing_email_provider
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = existing_phone_provider
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = None
        
        # Attempt registration
        registration_data = ProviderRegistrationSchema(**valid_provider_data)
        success, response = await provider_service_with_mock_repo.register_provider(registration_data)
        
        # Should fail due to duplicate email (first check)
        assert not success
        assert "email" in response["errors"]
    
    @pytest.mark.asyncio
    async def test_successful_registration_no_duplicates(self, provider_service_with_mock_repo, valid_provider_data, mock_created_provider):
        """Test successful registration when no duplicates exist."""
        # Mock repository to return None for all duplicate checks
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = None
        provider_service_with_mock_repo.repository.create_provider.return_value = mock_created_provider
        
        # Attempt registration
        registration_data = ProviderRegistrationSchema(**valid_provider_data)
        success, response = await provider_service_with_mock_repo.register_provider(registration_data)
        
        # Should succeed
        assert success
        assert response["success"] is True
        assert "provider_id" in response["data"]
        assert response["data"]["email"] == valid_provider_data["email"]
    
    @pytest.mark.asyncio
    async def test_validate_unique_fields_all_valid(self, provider_service_with_mock_repo):
        """Test unique field validation when all fields are unique."""
        # Mock repository to return None (no existing providers)
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = None
        
        result = await provider_service_with_mock_repo.validate_unique_fields(
            email="new@clinic.com",
            phone_number="+1111111111",
            license_number="NEW123456"
        )
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_unique_fields_email_duplicate(self, provider_service_with_mock_repo):
        """Test unique field validation when email is duplicate."""
        # Mock repository to return existing provider for email
        existing_provider = {"provider_id": "existing-id", "email": "existing@clinic.com"}
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = existing_provider
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = None
        
        result = await provider_service_with_mock_repo.validate_unique_fields(
            email="existing@clinic.com",
            phone_number="+1111111111",
            license_number="NEW123456"
        )
        
        assert result["is_valid"] is False
        assert "email" in result["errors"]
        assert "already registered" in result["errors"]["email"][0]
    
    @pytest.mark.asyncio
    async def test_validate_unique_fields_partial_check(self, provider_service_with_mock_repo):
        """Test unique field validation with only some fields provided."""
        # Mock repository 
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = None
        
        # Test with only email
        result = await provider_service_with_mock_repo.validate_unique_fields(email="new@clinic.com")
        assert result["is_valid"] is True
        
        # Verify only email check was called
        provider_service_with_mock_repo.repository.get_provider_by_email.assert_called_once_with("new@clinic.com")
        provider_service_with_mock_repo.repository.get_provider_by_phone.assert_not_called()
        provider_service_with_mock_repo.repository.get_provider_by_license.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_case_insensitive_email_duplicate(self, provider_service_with_mock_repo, valid_provider_data):
        """Test that email duplicates are detected regardless of case."""
        # Note: This test assumes the database handles case-insensitive email lookups
        # In a real implementation, you might want to normalize emails to lowercase
        
        existing_provider = {
            "provider_id": "existing-id",
            "email": "JOHN.DOE@CLINIC.COM",  # Different case
            "phone_number": "+9999999999",
            "license_number": "EXISTING123"
        }
        
        provider_service_with_mock_repo.repository.get_provider_by_email.return_value = existing_provider
        provider_service_with_mock_repo.repository.get_provider_by_phone.return_value = None
        provider_service_with_mock_repo.repository.get_provider_by_license.return_value = None
        
        # Attempt registration with lowercase email
        registration_data = ProviderRegistrationSchema(**valid_provider_data)
        success, response = await provider_service_with_mock_repo.register_provider(registration_data)
        
        # Should still detect duplicate (case-insensitive)
        assert not success
        assert "email" in response["errors"] 