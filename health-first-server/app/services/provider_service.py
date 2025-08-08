from typing import Dict, Any, Tuple
import logging

from app.schemas.provider import ProviderRegistrationSchema, VerificationStatus
from app.services.provider_repository import get_provider_repository
from app.utils.security import hash_password
from app.config import config

logger = logging.getLogger(__name__)

class ProviderService:
    """
    Service class that handles provider registration business logic.
    """
    
    def __init__(self):
        self.repository = get_provider_repository()
    
    async def register_provider(self, registration_data: ProviderRegistrationSchema) -> Tuple[bool, Dict[str, Any]]:
        """
        Register a new provider with comprehensive validation and security.
        
        Args:
            registration_data: Validated provider registration data
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Check for duplicate email
            existing_email = await self.repository.get_provider_by_email(registration_data.email)
            if existing_email:
                return False, {
                    "success": False,
                    "message": "Email address is already registered",
                    "errors": {"email": ["This email address is already registered"]}
                }
            
            # Check for duplicate phone number
            existing_phone = await self.repository.get_provider_by_phone(registration_data.phone_number)
            if existing_phone:
                return False, {
                    "success": False,
                    "message": "Phone number is already registered",
                    "errors": {"phone_number": ["This phone number is already registered"]}
                }
            
            # Check for duplicate license number
            existing_license = await self.repository.get_provider_by_license(registration_data.license_number)
            if existing_license:
                return False, {
                    "success": False,
                    "message": "License number is already registered",
                    "errors": {"license_number": ["This license number is already registered"]}
                }
            
            # Hash the password
            password_hash = hash_password(registration_data.password)
            
            # Prepare provider data for database
            provider_data = {
                "first_name": registration_data.first_name,
                "last_name": registration_data.last_name,
                "email": registration_data.email,
                "phone_number": registration_data.phone_number,
                "password_hash": password_hash,
                "specialization": registration_data.specialization,
                "license_number": registration_data.license_number,
                "years_of_experience": registration_data.years_of_experience,
                "clinic_address": {
                    "street": registration_data.clinic_address.street,
                    "city": registration_data.clinic_address.city,
                    "state": registration_data.clinic_address.state,
                    "zip": registration_data.clinic_address.zip
                }
            }
            
            # Create provider in database
            created_provider = await self.repository.create_provider(provider_data)
            
            # Log successful registration (without sensitive data)
            logger.info(f"Provider registered successfully: {created_provider['email']}")
            
            # Prepare response data
            response_data = {
                "success": True,
                "message": "Provider registered successfully. Verification email sent.",
                "data": {
                    "provider_id": created_provider["provider_id"],
                    "email": created_provider["email"],
                    "verification_status": created_provider["verification_status"]
                }
            }
            
            # TODO: Send verification email (implement email service)
            # await self._send_verification_email(created_provider)
            
            return True, response_data
            
        except ValueError as e:
            # Handle specific validation errors
            error_message = str(e)
            logger.warning(f"Provider registration validation error: {error_message}")
            
            # Determine which field caused the error
            field_errors = {}
            if "email" in error_message.lower():
                field_errors["email"] = [error_message]
            elif "phone" in error_message.lower():
                field_errors["phone_number"] = [error_message]
            elif "license" in error_message.lower():
                field_errors["license_number"] = [error_message]
            else:
                field_errors["general"] = [error_message]
            
            return False, {
                "success": False,
                "message": "Registration failed due to duplicate or invalid data",
                "errors": field_errors
            }
            
        except RuntimeError as e:
            # Handle database errors
            logger.error(f"Database error during provider registration: {str(e)}")
            return False, {
                "success": False,
                "message": "Registration failed due to server error. Please try again later.",
                "errors": {"server": ["Internal server error"]}
            }
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error during provider registration: {str(e)}")
            return False, {
                "success": False,
                "message": "Registration failed due to unexpected error. Please try again later.",
                "errors": {"server": ["Unexpected server error"]}
            }
    
    async def get_provider_by_id(self, provider_id: str) -> Dict[str, Any]:
        """
        Get provider information by ID.
        
        Args:
            provider_id: Provider's unique identifier
            
        Returns:
            Provider data dictionary or empty dict if not found
        """
        try:
            provider = await self.repository.get_provider_by_id(provider_id)
            if provider:
                # Remove sensitive information before returning
                provider_copy = provider.copy()
                if 'password_hash' in provider_copy:
                    del provider_copy['password_hash']
                return provider_copy
            return {}
        except Exception as e:
            logger.error(f"Error getting provider by ID {provider_id}: {str(e)}")
            return {}
    
    async def validate_unique_fields(self, email: str = None, phone_number: str = None, license_number: str = None) -> Dict[str, Any]:
        """
        Validate that email, phone, and license number are unique.
        
        Args:
            email: Email to check
            phone_number: Phone number to check
            license_number: License number to check
            
        Returns:
            Dictionary with validation results
        """
        errors = {}
        
        try:
            if email:
                existing_email = await self.repository.get_provider_by_email(email)
                if existing_email:
                    errors["email"] = ["This email address is already registered"]
            
            if phone_number:
                existing_phone = await self.repository.get_provider_by_phone(phone_number)
                if existing_phone:
                    errors["phone_number"] = ["This phone number is already registered"]
            
            if license_number:
                existing_license = await self.repository.get_provider_by_license(license_number)
                if existing_license:
                    errors["license_number"] = ["This license number is already registered"]
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error validating unique fields: {str(e)}")
            return {
                "is_valid": False,
                "errors": {"server": ["Unable to validate uniqueness. Please try again."]}
            }
    
    # TODO: Implement additional methods as needed
    # async def _send_verification_email(self, provider_data: Dict[str, Any]):
    #     """Send verification email to the provider."""
    #     pass
    
    # async def verify_provider(self, provider_id: str, verification_token: str) -> bool:
    #     """Verify provider account using verification token."""
    #     pass
    
    # async def update_verification_status(self, provider_id: str, status: VerificationStatus) -> bool:
    #     """Update provider verification status."""
    #     pass 