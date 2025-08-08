from typing import Dict, Any, Tuple, Optional
import logging
from app.schemas.auth import PatientLoginSchema
from app.services.patient_repository import get_patient_repository
from app.utils.security import verify_password
from app.utils.jwt_handler import jwt_handler

logger = logging.getLogger(__name__)

class PatientAuthService:
    """
    Service class that handles patient authentication and authorization.
    """
    
    def __init__(self):
        self.repository = get_patient_repository()
    
    async def authenticate_patient(self, login_data: PatientLoginSchema) -> Tuple[bool, Dict[str, Any]]:
        """
        Authenticate patient with email and password.
        
        Args:
            login_data: Patient login credentials
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Get patient by email
            patient = await self.repository.get_patient_by_email(login_data.email)
            
            if not patient:
                logger.warning(f"Login attempt with non-existent email: {login_data.email}")
                return False, {
                    "success": False,
                    "message": "Invalid credentials",
                    "error_code": "INVALID_CREDENTIALS"
                }
            
            # Verify password
            if not verify_password(login_data.password, patient.get("password_hash", "")):
                logger.warning(f"Invalid password for patient: {login_data.email}")
                return False, {
                    "success": False,
                    "message": "Invalid credentials",
                    "error_code": "INVALID_CREDENTIALS"
                }
            
            # Check if account is active
            if not patient.get("is_active", False):
                logger.warning(f"Login attempt for inactive account: {login_data.email}")
                return False, {
                    "success": False,
                    "message": "Account is deactivated. Please contact support.",
                    "error_code": "ACCOUNT_DEACTIVATED"
                }
            
            # Note: Unlike providers, patients don't require verification to log in
            # This allows for a smoother user experience while still tracking verification status
            
            # Generate JWT token
            token_data = jwt_handler.generate_patient_access_token(patient)
            
            # Prepare patient data (without sensitive information)
            patient_data = self._prepare_patient_data(patient)
            
            # Successful authentication
            logger.info(f"Successful login for patient: {login_data.email}")
            
            response_data = {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": token_data["access_token"],
                    "expires_in": token_data["expires_in"],
                    "token_type": token_data["token_type"],
                    "patient": patient_data
                }
            }
            
            return True, response_data
            
        except Exception as e:
            logger.error(f"Authentication error for {login_data.email}: {str(e)}")
            return False, {
                "success": False,
                "message": "Authentication failed due to server error",
                "error_code": "AUTHENTICATION_ERROR"
            }
    
    def _prepare_patient_data(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare patient data for response (remove sensitive information).
        
        Args:
            patient: Raw patient data from database
            
        Returns:
            Sanitized patient data
        """
        # Remove sensitive fields
        safe_patient = patient.copy()
        safe_patient.pop("password_hash", None)
        
        # Ensure consistent datetime format
        if "created_at" in safe_patient:
            safe_patient["created_at"] = str(safe_patient["created_at"])
        if "updated_at" in safe_patient:
            safe_patient["updated_at"] = str(safe_patient["updated_at"])
        
        # Ensure date of birth is string format
        if "date_of_birth" in safe_patient and safe_patient["date_of_birth"]:
            if hasattr(safe_patient["date_of_birth"], 'isoformat'):
                safe_patient["date_of_birth"] = safe_patient["date_of_birth"].isoformat()
            else:
                safe_patient["date_of_birth"] = str(safe_patient["date_of_birth"])
        
        return safe_patient
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT access token for patient.
        
        Args:
            token: JWT token string
            
        Returns:
            Token validation result
        """
        try:
            payload = jwt_handler.verify_access_token(token)
            
            if not payload:
                return {
                    "valid": False,
                    "error": "Invalid or expired token"
                }
            
            # Ensure this is a patient token
            if payload.get("role") != "patient":
                return {
                    "valid": False,
                    "error": "Invalid token type"
                }
            
            # Additional database validation (check if patient still exists and is active)
            patient = await self.repository.get_patient_by_email(payload["email"])
            
            if not patient:
                return {
                    "valid": False,
                    "error": "Patient no longer exists"
                }
            
            if not patient.get("is_active", False):
                return {
                    "valid": False,
                    "error": "Patient account is deactivated"
                }
            
            return {
                "valid": True,
                "patient_id": payload["patient_id"],
                "email": payload["email"],
                "is_active": payload["is_active"],
                "email_verified": payload.get("email_verified", False),
                "phone_verified": payload.get("phone_verified", False),
                "expires_at": payload.get("exp")
            }
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return {
                "valid": False,
                "error": "Token validation failed"
            }
    
    async def get_current_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current patient data by ID.
        
        Args:
            patient_id: Patient's unique identifier
            
        Returns:
            Patient data or None if not found
        """
        try:
            patient = await self.repository.get_patient_by_id(patient_id)
            if patient:
                return self._prepare_patient_data(patient)
            return None
        except Exception as e:
            logger.error(f"Error getting current patient {patient_id}: {str(e)}")
            return None
    
    async def check_patient_verification_status(self, patient_id: str) -> Dict[str, bool]:
        """
        Check patient verification status (email and phone).
        
        Args:
            patient_id: Patient's unique identifier
            
        Returns:
            Dictionary with email_verified and phone_verified status
        """
        try:
            patient = await self.repository.get_patient_by_id(patient_id)
            
            if not patient:
                return {"email_verified": False, "phone_verified": False}
            
            return {
                "email_verified": patient.get("email_verified", False),
                "phone_verified": patient.get("phone_verified", False)
            }
            
        except Exception as e:
            logger.error(f"Error checking verification status for {patient_id}: {str(e)}")
            return {"email_verified": False, "phone_verified": False} 