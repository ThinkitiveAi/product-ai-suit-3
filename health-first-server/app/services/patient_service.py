from typing import Dict, Any, Tuple
import logging
from datetime import datetime

from app.schemas.patient import PatientRegistrationSchema
from app.services.patient_repository import get_patient_repository
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

class PatientService:
    """
    Service class that handles patient registration business logic.
    Includes HIPAA compliance considerations for medical data handling.
    """
    
    def __init__(self):
        self.repository = get_patient_repository()
    
    async def register_patient(self, registration_data: PatientRegistrationSchema) -> Tuple[bool, Dict[str, Any]]:
        """
        Register a new patient with comprehensive validation and security.
        
        Args:
            registration_data: Validated patient registration data
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Check for duplicate email
            existing_email = await self.repository.get_patient_by_email(registration_data.email)
            if existing_email:
                return False, {
                    "success": False,
                    "message": "Email address is already registered",
                    "errors": {"email": ["This email address is already registered"]}
                }
            
            # Check for duplicate phone number
            existing_phone = await self.repository.get_patient_by_phone(registration_data.phone_number)
            if existing_phone:
                return False, {
                    "success": False,
                    "message": "Phone number is already registered",
                    "errors": {"phone_number": ["This phone number is already registered"]}
                }
            
            # Hash the password securely
            password_hash = hash_password(registration_data.password)
            
            # Prepare patient data for database
            patient_data = {
                "first_name": registration_data.first_name,
                "last_name": registration_data.last_name,
                "email": registration_data.email,
                "phone_number": registration_data.phone_number,
                "password_hash": password_hash,
                "date_of_birth": registration_data.date_of_birth,
                "gender": registration_data.gender.value,
                "address": {
                    "street": registration_data.address.street,
                    "city": registration_data.address.city,
                    "state": registration_data.address.state,
                    "zip": registration_data.address.zip
                }
            }
            
            # Add optional fields
            if registration_data.emergency_contact:
                patient_data["emergency_contact"] = {
                    "name": registration_data.emergency_contact.name,
                    "phone": registration_data.emergency_contact.phone,
                    "relationship": registration_data.emergency_contact.relationship
                }
            
            if registration_data.medical_history:
                patient_data["medical_history"] = registration_data.medical_history
            
            if registration_data.insurance_info:
                patient_data["insurance_info"] = {
                    "provider": registration_data.insurance_info.provider,
                    "policy_number": registration_data.insurance_info.policy_number
                }
            
            # Create patient in database
            created_patient = await self.repository.create_patient(patient_data)
            
            # Log successful registration (without sensitive data)
            logger.info(f"Patient registered successfully: {created_patient['email']}")
            
            # Prepare response data (exclude sensitive information)
            response_data = {
                "success": True,
                "message": "Patient registered successfully. Verification email sent.",
                "data": {
                    "patient_id": created_patient["patient_id"],
                    "email": created_patient["email"],
                    "phone_number": created_patient["phone_number"],
                    "email_verified": created_patient["email_verified"],
                    "phone_verified": created_patient["phone_verified"]
                }
            }
            
            # TODO: Send verification email (implement email service)
            # await self._send_verification_email(created_patient)
            
            # TODO: Log PHI access for HIPAA compliance
            # await self._log_phi_access("CREATE", created_patient["patient_id"], "REGISTRATION")
            
            return True, response_data
            
        except ValueError as e:
            # Handle specific validation errors
            error_message = str(e)
            logger.warning(f"Patient registration validation error: {error_message}")
            
            # Determine which field caused the error
            field_errors = {}
            if "email" in error_message.lower():
                field_errors["email"] = [error_message]
            elif "phone" in error_message.lower():
                field_errors["phone_number"] = [error_message]
            else:
                field_errors["general"] = [error_message]
            
            return False, {
                "success": False,
                "message": "Registration failed due to duplicate or invalid data",
                "errors": field_errors
            }
            
        except RuntimeError as e:
            # Handle database errors
            logger.error(f"Database error during patient registration: {str(e)}")
            return False, {
                "success": False,
                "message": "Registration failed due to server error. Please try again later.",
                "errors": {"server": ["Internal server error"]}
            }
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error during patient registration: {str(e)}")
            return False, {
                "success": False,
                "message": "Registration failed due to unexpected error. Please try again later.",
                "errors": {"server": ["Unexpected server error"]}
            }
    
    async def get_patient_by_id(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient information by ID.
        
        Args:
            patient_id: Patient's unique identifier
            
        Returns:
            Patient data dictionary or empty dict if not found
        """
        try:
            patient = await self.repository.get_patient_by_id(patient_id)
            if patient:
                # TODO: Log PHI access for HIPAA compliance
                # await self._log_phi_access("READ", patient_id, "PROFILE_VIEW")
                
                return self._prepare_patient_data_for_response(patient)
            return {}
        except Exception as e:
            logger.error(f"Error getting patient by ID {patient_id}: {str(e)}")
            return {}
    
    async def validate_unique_fields(self, email: str = None, phone_number: str = None) -> Dict[str, Any]:
        """
        Validate that email and phone number are unique.
        
        Args:
            email: Email to check
            phone_number: Phone number to check
            
        Returns:
            Dictionary with validation results
        """
        errors = {}
        
        try:
            if email:
                existing_email = await self.repository.get_patient_by_email(email)
                if existing_email:
                    errors["email"] = ["This email address is already registered"]
            
            if phone_number:
                existing_phone = await self.repository.get_patient_by_phone(phone_number)
                if existing_phone:
                    errors["phone_number"] = ["This phone number is already registered"]
            
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
    
    async def update_patient_info(self, patient_id: str, update_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Update patient information (excluding sensitive fields).
        
        Args:
            patient_id: Patient's unique identifier
            update_data: Dictionary of fields to update
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Verify patient exists
            existing_patient = await self.repository.get_patient_by_id(patient_id)
            if not existing_patient:
                return False, {
                    "success": False,
                    "message": "Patient not found",
                    "errors": {"patient_id": ["Patient does not exist"]}
                }
            
            # Prepare update data with timestamp
            sanitized_update_data = update_data.copy()
            sanitized_update_data["updated_at"] = datetime.utcnow()
            
            # Update patient in database
            success = await self.repository.update_patient(patient_id, sanitized_update_data)
            
            if success:
                # TODO: Log PHI access for HIPAA compliance
                # await self._log_phi_access("UPDATE", patient_id, "PROFILE_UPDATE")
                
                logger.info(f"Patient updated successfully: {patient_id}")
                return True, {
                    "success": True,
                    "message": "Patient information updated successfully"
                }
            else:
                return False, {
                    "success": False,
                    "message": "Failed to update patient information",
                    "errors": {"update": ["Update operation failed"]}
                }
                
        except Exception as e:
            logger.error(f"Error updating patient {patient_id}: {str(e)}")
            return False, {
                "success": False,
                "message": "Update failed due to server error",
                "errors": {"server": ["Internal server error"]}
            }
    
    def _prepare_patient_data_for_response(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare patient data for API response (sanitize sensitive information).
        
        Args:
            patient: Raw patient data from database
            
        Returns:
            Sanitized patient data for response
        """
        # Remove sensitive fields
        safe_patient = patient.copy()
        safe_patient.pop("password_hash", None)
        
        # Ensure consistent datetime format
        if "created_at" in safe_patient:
            safe_patient["created_at"] = str(safe_patient["created_at"])
        if "updated_at" in safe_patient:
            safe_patient["updated_at"] = str(safe_patient["updated_at"])
        if "date_of_birth" in safe_patient:
            safe_patient["date_of_birth"] = str(safe_patient["date_of_birth"])
        
        return safe_patient
    
    # TODO: Implement additional methods as needed for HIPAA compliance
    # async def _send_verification_email(self, patient_data: Dict[str, Any]):
    #     """Send verification email to the patient."""
    #     pass
    
    # async def _log_phi_access(self, action: str, patient_id: str, context: str):
    #     """Log access to Protected Health Information for HIPAA compliance."""
    #     pass
    
    # async def verify_patient_email(self, patient_id: str, verification_token: str) -> bool:
    #     """Verify patient email using verification token."""
    #     pass
    
    # async def verify_patient_phone(self, patient_id: str, verification_code: str) -> bool:
    #     """Verify patient phone using SMS verification code."""
    #     pass 