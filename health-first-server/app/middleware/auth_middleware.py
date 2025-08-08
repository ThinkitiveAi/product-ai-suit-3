from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.services.auth_service import AuthService
from app.services.patient_auth_service import PatientAuthService

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()

class AuthMiddleware:
    """Authentication middleware for JWT token validation."""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.patient_auth_service = PatientAuthService()
    
    async def get_current_provider(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Extract and validate JWT token from Authorization header for providers.
        
        Args:
            credentials: Authorization credentials from header
            
        Returns:
            Current provider data
            
        Raises:
            HTTPException: If token is invalid or missing
        """
        try:
            if not credentials or not credentials.credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Authorization token is required",
                        "error_code": "TOKEN_MISSING"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Validate token
            validation_result = await self.auth_service.validate_token(credentials.credentials)
            
            if not validation_result.get("valid", False):
                error_message = validation_result.get("error", "Invalid token")
                logger.warning(f"Token validation failed: {error_message}")
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": error_message,
                        "error_code": "TOKEN_INVALID"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get full provider data
            provider_data = await self.auth_service.get_current_provider(
                validation_result["provider_id"]
            )
            
            if not provider_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Provider not found",
                        "error_code": "PROVIDER_NOT_FOUND"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return provider_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Provider authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Authentication service error",
                    "error_code": "AUTH_SERVICE_ERROR"
                }
            )
    
    async def get_current_patient(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Extract and validate JWT token from Authorization header for patients.
        
        Args:
            credentials: Authorization credentials from header
            
        Returns:
            Current patient data
            
        Raises:
            HTTPException: If token is invalid or missing
        """
        try:
            if not credentials or not credentials.credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Authorization token is required",
                        "error_code": "TOKEN_MISSING"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Validate token
            validation_result = await self.patient_auth_service.validate_token(credentials.credentials)
            
            if not validation_result.get("valid", False):
                error_message = validation_result.get("error", "Invalid token")
                logger.warning(f"Patient token validation failed: {error_message}")
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": error_message,
                        "error_code": "TOKEN_INVALID"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get full patient data
            patient_data = await self.patient_auth_service.get_current_patient(
                validation_result["patient_id"]
            )
            
            if not patient_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Patient not found",
                        "error_code": "PATIENT_NOT_FOUND"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return patient_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Patient authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Authentication service error",
                    "error_code": "AUTH_SERVICE_ERROR"
                }
            )
    
    async def get_optional_current_provider(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Optional[Dict[str, Any]]:
        """
        Optional authentication - returns provider if valid token present, None otherwise.
        
        Args:
            credentials: Optional authorization credentials
            
        Returns:
            Provider data if authenticated, None otherwise
        """
        try:
            if not credentials or not credentials.credentials:
                return None
            
            # Validate token
            validation_result = await self.auth_service.validate_token(credentials.credentials)
            
            if not validation_result.get("valid", False):
                return None
            
            # Get full provider data
            provider_data = await self.auth_service.get_current_provider(
                validation_result["provider_id"]
            )
            
            return provider_data
            
        except Exception as e:
            logger.warning(f"Optional provider authentication failed: {str(e)}")
            return None
    
    async def get_optional_current_patient(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Optional[Dict[str, Any]]:
        """
        Optional authentication - returns patient if valid token present, None otherwise.
        
        Args:
            credentials: Optional authorization credentials
            
        Returns:
            Patient data if authenticated, None otherwise
        """
        try:
            if not credentials or not credentials.credentials:
                return None
            
            # Validate token
            validation_result = await self.patient_auth_service.validate_token(credentials.credentials)
            
            if not validation_result.get("valid", False):
                return None
            
            # Get full patient data
            patient_data = await self.patient_auth_service.get_current_patient(
                validation_result["patient_id"]
            )
            
            return patient_data
            
        except Exception as e:
            logger.warning(f"Optional patient authentication failed: {str(e)}")
            return None

class AuthorizationMiddleware:
    """Authorization middleware for role and permission checks."""
    
    def __init__(self):
        self.auth_middleware = AuthMiddleware()
    
    async def require_verified_provider(
        self,
        current_provider: Dict[str, Any] = Depends(AuthMiddleware().get_current_provider)
    ) -> Dict[str, Any]:
        """
        Require provider to be verified.
        
        Args:
            current_provider: Current provider from authentication
            
        Returns:
            Provider data if verified
            
        Raises:
            HTTPException: If provider is not verified
        """
        verification_status = current_provider.get("verification_status", "pending")
        
        if verification_status != "verified":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Provider account is not verified. Please complete verification first.",
                    "error_code": "PROVIDER_NOT_VERIFIED"
                }
            )
        
        return current_provider
    
    async def require_active_patient(
        self,
        current_patient: Dict[str, Any] = Depends(AuthMiddleware().get_current_patient)
    ) -> Dict[str, Any]:
        """
        Require patient to be active (this is already checked in token validation,
        but provided for consistency).
        
        Args:
            current_patient: Current patient from authentication
            
        Returns:
            Patient data if active
            
        Raises:
            HTTPException: If patient is not active
        """
        if not current_patient.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Patient account is deactivated. Please contact support.",
                    "error_code": "PATIENT_DEACTIVATED"
                }
            )
        
        return current_patient

# Global middleware instances for easy import
auth_middleware = AuthMiddleware()
authorization_middleware = AuthorizationMiddleware()

# Convenience functions for dependency injection
async def get_current_provider(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    return await auth_middleware.get_current_provider(credentials)

async def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    return await auth_middleware.get_current_patient(credentials)

async def get_optional_current_provider(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    return await auth_middleware.get_optional_current_provider(credentials)

async def get_optional_current_patient(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    return await auth_middleware.get_optional_current_patient(credentials)

async def require_verified_provider(
    current_provider: Dict[str, Any] = Depends(get_current_provider)
) -> Dict[str, Any]:
    return await authorization_middleware.require_verified_provider(current_provider)

async def require_active_patient(
    current_patient: Dict[str, Any] = Depends(get_current_patient)
) -> Dict[str, Any]:
    return await authorization_middleware.require_active_patient(current_patient)

async def require_verified_and_active_provider(
    current_provider: Dict[str, Any] = Depends(get_current_provider)
) -> Dict[str, Any]:
    """
    Require provider to be both verified and active.
    
    Args:
        current_provider: Current provider from authentication
        
    Returns:
        Provider data if verified and active
        
    Raises:
        HTTPException: If provider is not verified or active
    """
    # Check if active
    if not current_provider.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Account is deactivated",
                "error_code": "ACCOUNT_DEACTIVATED"
            }
        )
    
    # Check if verified
    verification_status = current_provider.get("verification_status", "pending")
    if verification_status != "verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Account verification required for this operation",
                "error_code": "VERIFICATION_REQUIRED"
            }
        )
    
    return current_provider 