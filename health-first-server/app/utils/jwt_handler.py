import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import logging
from app.config import config

logger = logging.getLogger(__name__)

class JWTHandler:
    """Handle JWT token generation and validation."""
    
    def __init__(self):
        self.secret_key = config.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_hours = 1
        self.patient_access_token_expire_minutes = 30  # 30 minutes for patients as requested
        
    def generate_access_token(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JWT access token for provider.
        
        Args:
            provider_data: Provider information
            
        Returns:
            Dictionary containing token and metadata
        """
        try:
            # Set expiration time
            expire = datetime.now(timezone.utc) + timedelta(hours=self.access_token_expire_hours)
            
            # Prepare token payload
            payload = {
                "provider_id": provider_data["provider_id"],
                "email": provider_data["email"],
                "specialization": provider_data["specialization"],
                "verification_status": provider_data["verification_status"],
                "is_active": provider_data["is_active"],
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access_token",
                "role": "provider"
            }
            
            # Generate token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Access token generated for provider: {provider_data['email']}")
            
            return {
                "access_token": token,
                "expires_in": self.access_token_expire_hours * 3600,  # Convert to seconds
                "token_type": "Bearer",
                "expires_at": expire.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating access token: {str(e)}")
            raise RuntimeError("Failed to generate access token")
    
    def generate_patient_access_token(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JWT access token for patient.
        
        Args:
            patient_data: Patient information
            
        Returns:
            Dictionary containing token and metadata
        """
        try:
            # Set expiration time (30 minutes as requested)
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.patient_access_token_expire_minutes)
            
            # Prepare token payload
            payload = {
                "patient_id": patient_data["patient_id"],
                "email": patient_data["email"],
                "is_active": patient_data["is_active"],
                "email_verified": patient_data.get("email_verified", False),
                "phone_verified": patient_data.get("phone_verified", False),
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access_token",
                "role": "patient"
            }
            
            # Generate token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Access token generated for patient: {patient_data['email']}")
            
            return {
                "access_token": token,
                "expires_in": self.patient_access_token_expire_minutes * 60,  # Convert to seconds
                "token_type": "Bearer",
                "expires_at": expire.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating patient access token: {str(e)}")
            raise RuntimeError("Failed to generate patient access token")
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT access token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            # Verify token type
            if payload.get("type") != "access_token":
                logger.warning("Invalid token type")
                return None
            
            # Check role and required fields based on role
            role = payload.get("role")
            if role == "provider":
                required_fields = ["provider_id", "email", "verification_status", "is_active"]
            elif role == "patient":
                required_fields = ["patient_id", "email", "is_active"]
            else:
                logger.warning("Invalid or missing role in token")
                return None
            
            if not all(field in payload for field in required_fields):
                logger.warning("Token missing required fields")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    def extract_token_from_header(self, authorization_header: str) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            authorization_header: Authorization header value
            
        Returns:
            JWT token string or None if invalid format
        """
        if not authorization_header:
            return None
        
        # Expected format: "Bearer <token>"
        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    def get_token_payload_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token payload without verification (for debugging/logging).
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid format
        """
        try:
            return jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
        except Exception:
            return None

# Global JWT handler instance
jwt_handler = JWTHandler() 