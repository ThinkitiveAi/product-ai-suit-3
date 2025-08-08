from typing import Dict, Any, Tuple, Optional
import logging
from app.schemas.auth import ProviderLoginSchema
from app.services.provider_repository import get_provider_repository
from app.utils.security import verify_password
from app.utils.jwt_handler import jwt_handler

logger = logging.getLogger(__name__)

class AuthService:
    """
    Service class that handles provider authentication and authorization.
    """
    
    def __init__(self):
        self.repository = get_provider_repository()
    
    async def authenticate_provider(self, login_data: ProviderLoginSchema) -> Tuple[bool, Dict[str, Any]]:
        """
        Authenticate provider with email and password.
        
        Args:
            login_data: Provider login credentials
            
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            # Get provider by email
            provider = await self.repository.get_provider_by_email(login_data.email)
            
            if not provider:
                logger.warning(f"Login attempt with non-existent email: {login_data.email}")
                return False, {
                    "success": False,
                    "message": "Invalid credentials",
                    "error_code": "INVALID_CREDENTIALS"
                }
            
            # Verify password
            if not verify_password(login_data.password, provider.get("password_hash", "")):
                logger.warning(f"Invalid password for provider: {login_data.email}")
                return False, {
                    "success": False,
                    "message": "Invalid credentials",
                    "error_code": "INVALID_CREDENTIALS"
                }
            
            # Check if account is active
            if not provider.get("is_active", False):
                logger.warning(f"Login attempt for inactive account: {login_data.email}")
                return False, {
                    "success": False,
                    "message": "Account is deactivated. Please contact support.",
                    "error_code": "ACCOUNT_DEACTIVATED"
                }
            
            # Check if account is verified
            verification_status = provider.get("verification_status", "pending")
            if verification_status != "verified":
                logger.warning(f"Login attempt for unverified account: {login_data.email}")
                return False, {
                    "success": False,
                    "message": "Account is not verified. Please verify your account first.",
                    "error_code": "ACCOUNT_NOT_VERIFIED"
                }
            
            # Generate JWT token
            token_data = jwt_handler.generate_access_token(provider)
            
            # Prepare provider data (without sensitive information)
            provider_data = self._prepare_provider_data(provider)
            
            # Successful authentication
            logger.info(f"Successful login for provider: {login_data.email}")
            
            response_data = {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": token_data["access_token"],
                    "expires_in": token_data["expires_in"],
                    "token_type": token_data["token_type"],
                    "provider": provider_data
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
    
    def _prepare_provider_data(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare provider data for response (remove sensitive information).
        
        Args:
            provider: Raw provider data from database
            
        Returns:
            Sanitized provider data
        """
        # Remove sensitive fields
        safe_provider = provider.copy()
        safe_provider.pop("password_hash", None)
        
        # Ensure consistent datetime format
        if "created_at" in safe_provider:
            safe_provider["created_at"] = str(safe_provider["created_at"])
        if "updated_at" in safe_provider:
            safe_provider["updated_at"] = str(safe_provider["updated_at"])
        
        return safe_provider
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT access token.
        
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
            
            # Additional database validation (optional - check if provider still exists and is active)
            provider = await self.repository.get_provider_by_email(payload["email"])
            
            if not provider:
                return {
                    "valid": False,
                    "error": "Provider no longer exists"
                }
            
            if not provider.get("is_active", False):
                return {
                    "valid": False,
                    "error": "Provider account is deactivated"
                }
            
            return {
                "valid": True,
                "provider_id": payload["provider_id"],
                "email": payload["email"],
                "verification_status": payload["verification_status"],
                "is_active": payload["is_active"],
                "specialization": payload.get("specialization"),
                "expires_at": payload.get("exp")
            }
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return {
                "valid": False,
                "error": "Token validation failed"
            }
    
    async def get_current_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current provider data by ID.
        
        Args:
            provider_id: Provider's unique identifier
            
        Returns:
            Provider data or None if not found
        """
        try:
            provider = await self.repository.get_provider_by_id(provider_id)
            if provider:
                return self._prepare_provider_data(provider)
            return None
        except Exception as e:
            logger.error(f"Error getting current provider {provider_id}: {str(e)}")
            return None
    
    async def refresh_provider_verification_status(self, provider_id: str) -> bool:
        """
        Refresh provider verification status from database.
        This can be used to update token claims if verification status changes.
        
        Args:
            provider_id: Provider's unique identifier
            
        Returns:
            True if provider is verified and active, False otherwise
        """
        try:
            provider = await self.repository.get_provider_by_id(provider_id)
            
            if not provider:
                return False
            
            return (
                provider.get("is_active", False) and 
                provider.get("verification_status") == "verified"
            )
            
        except Exception as e:
            logger.error(f"Error refreshing verification status for {provider_id}: {str(e)}")
            return False 