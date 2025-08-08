from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Dict, Any, Optional
from app.utils.security import sanitize_input

class ProviderLoginSchema(BaseModel):
    email: EmailStr = Field(..., description="Provider's email address")
    password: str = Field(..., min_length=1, description="Provider's password")
    
    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        return sanitize_input(str(v).lower())
    
    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v

class PatientLoginSchema(BaseModel):
    email: EmailStr = Field(..., description="Patient's email address")
    password: str = Field(..., min_length=1, description="Patient's password")
    
    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        return sanitize_input(str(v).lower())
    
    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v

class ProviderDataSchema(BaseModel):
    provider_id: str
    email: EmailStr
    first_name: str
    last_name: str
    specialization: str
    verification_status: str
    is_active: bool

class PatientDataSchema(BaseModel):
    patient_id: str
    email: EmailStr
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    email_verified: bool
    phone_verified: bool
    is_active: bool

class LoginSuccessResponseSchema(BaseModel):
    success: bool = True
    message: str = "Login successful"
    data: Dict[str, Any] = Field(..., description="Login response data including token and user info")

class PatientLoginSuccessResponseSchema(BaseModel):
    success: bool = True
    message: str = "Login successful"
    data: Dict[str, Any] = Field(..., description="Login response data including token and patient info")

class LoginErrorResponseSchema(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None

class TokenValidationSchema(BaseModel):
    token: str = Field(..., description="JWT token to validate") 