import re
import bcrypt
import logging
from app.config import config

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt directly.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    try:
        # Use bcrypt directly to avoid compatibility issues
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt directly.
    
    Args:
        plain_password: Plain text password
        hashed_password: Previously hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Use bcrypt directly to avoid compatibility issues
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if len(password) < config.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters long")
    
    if len(password) > config.MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be no more than {config.MAX_PASSWORD_LENGTH} characters long")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors

def sanitize_input(input_string: str) -> str:
    """
    Sanitize input string to prevent injection attacks.
    
    Args:
        input_string: Input to sanitize
        
    Returns:
        Sanitized string
    """
    if not input_string:
        return ""
    
    # Remove potential HTML/script tags
    input_string = re.sub(r'<[^>]*>', '', input_string)
    
    # Remove potential SQL injection patterns
    dangerous_patterns = [
        r"('\s*(OR|AND)\s*')",
        r"(--)",
        r"(;)",
        r"(\bDROP\b)",
        r"(\bDELETE\b)",
        r"(\bINSERT\b)",
        r"(\bUPDATE\b)",
        r"(\bSELECT\b)",
        r"(\bUNION\b)"
    ]
    
    for pattern in dangerous_patterns:
        input_string = re.sub(pattern, '', input_string, flags=re.IGNORECASE)
    
    return input_string.strip() 