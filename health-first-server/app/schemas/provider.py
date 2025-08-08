from datetime import datetime
from enum import Enum
from typing import Optional
import re
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
import phonenumbers
from app.config import config
from app.utils.security import validate_password_strength, sanitize_input

class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class ClinicAddressSchema(BaseModel):
    street: str = Field(..., min_length=1, max_length=200, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=1, max_length=50, description="State name")
    zip: str = Field(..., min_length=1, max_length=20, description="Postal/ZIP code")
    
    @field_validator('street', 'city', 'state')
    @classmethod
    def sanitize_address_fields(cls, v):
        return sanitize_input(v)
    
    @field_validator('zip')
    @classmethod
    def validate_zip_code(cls, v):
        # Basic postal code validation (supports US ZIP and international formats)
        zip_pattern = r'^[A-Za-z0-9\s\-]{3,20}$'
        if not re.match(zip_pattern, v):
            raise ValueError('Invalid postal/ZIP code format')
        return sanitize_input(v)

class ProviderRegistrationSchema(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50, description="Provider's first name")
    last_name: str = Field(..., min_length=2, max_length=50, description="Provider's last name")
    email: EmailStr = Field(..., description="Provider's email address")
    phone_number: str = Field(..., description="Provider's phone number in international format")
    password: str = Field(..., min_length=8, max_length=100, description="Provider's password")
    confirm_password: str = Field(..., description="Password confirmation")
    specialization: str = Field(..., min_length=3, max_length=100, description="Medical specialization")
    license_number: str = Field(..., min_length=1, max_length=50, description="Medical license number")
    years_of_experience: int = Field(..., ge=0, le=50, description="Years of medical experience")
    clinic_address: ClinicAddressSchema = Field(..., description="Clinic address information")
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v):
        sanitized = sanitize_input(v)
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', sanitized):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        return sanitized
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        try:
            # Parse and validate international phone number
            parsed_number = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError('Invalid phone number format')
            # Return in E.164 format
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number format. Please use international format (e.g., +1234567890)')
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v
    
    @field_validator('specialization')
    @classmethod
    def validate_specialization(cls, v):
        sanitized = sanitize_input(v)
        
        # Check if it's in predefined list (case-insensitive)
        predefined_lower = [spec.lower() for spec in config.PREDEFINED_SPECIALIZATIONS]
        if sanitized.lower() in predefined_lower:
            # Return the properly capitalized version
            for spec in config.PREDEFINED_SPECIALIZATIONS:
                if spec.lower() == sanitized.lower():
                    return spec
        
        # If not in predefined list, validate format
        if not re.match(r'^[A-Za-z\s\-&,\.]+$', sanitized):
            raise ValueError('Specialization can only contain letters, spaces, hyphens, commas, periods, and ampersands')
        
        return sanitized
    
    @field_validator('license_number')
    @classmethod
    def validate_license_number(cls, v):
        sanitized = sanitize_input(v)
        if not re.match(r'^[A-Za-z0-9]+$', sanitized):
            raise ValueError('License number must be alphanumeric only')
        return sanitized.upper()  # Store in uppercase for consistency
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        if self.password and self.confirm_password and self.password != self.confirm_password:
            raise ValueError('Password and confirm password do not match')
        return self

class ProviderResponseSchema(BaseModel):
    provider_id: str = Field(..., description="Unique provider identifier")
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    specialization: str
    license_number: str
    years_of_experience: int
    clinic_address: ClinicAddressSchema
    verification_status: VerificationStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class ProviderRegistrationResponseSchema(BaseModel):
    success: bool = True
    message: str = "Provider registered successfully. Verification email sent."
    data: dict = Field(..., description="Response data with provider_id, email, and verification_status")

class ErrorResponseSchema(BaseModel):
    success: bool = False
    message: str
    errors: Optional[dict] = None
    
class ValidationErrorResponseSchema(BaseModel):
    success: bool = False
    message: str = "Validation failed"
    errors: dict = Field(..., description="Field-specific validation errors") 