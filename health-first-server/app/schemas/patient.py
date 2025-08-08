from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import re
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
import phonenumbers
from dateutil.relativedelta import relativedelta
from app.config import config
from app.utils.security import validate_password_strength, sanitize_input

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class AddressSchema(BaseModel):
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

class EmergencyContactSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Emergency contact name")
    phone: str = Field(..., description="Emergency contact phone number")
    relationship: str = Field(..., min_length=1, max_length=50, description="Relationship to patient")
    
    @field_validator('name', 'relationship')
    @classmethod
    def sanitize_text_fields(cls, v):
        sanitized = sanitize_input(v)
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', sanitized):
            raise ValueError('Name and relationship can only contain letters, spaces, hyphens, apostrophes, and periods')
        return sanitized
    
    @field_validator('phone')
    @classmethod
    def validate_phone_number(cls, v):
        try:
            parsed_number = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError('Invalid phone number format')
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number format. Please use international format (e.g., +1234567890)')

class InsuranceInfoSchema(BaseModel):
    provider: str = Field(..., min_length=1, max_length=100, description="Insurance provider name")
    policy_number: str = Field(..., min_length=1, max_length=50, description="Insurance policy number")
    
    @field_validator('provider', 'policy_number')
    @classmethod
    def sanitize_insurance_fields(cls, v):
        return sanitize_input(v)

class PatientRegistrationSchema(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50, description="Patient's first name")
    last_name: str = Field(..., min_length=2, max_length=50, description="Patient's last name")
    email: EmailStr = Field(..., description="Patient's email address")
    phone_number: str = Field(..., description="Patient's phone number in international format")
    password: str = Field(..., min_length=8, max_length=100, description="Patient's password")
    confirm_password: str = Field(..., description="Password confirmation")
    date_of_birth: date = Field(..., description="Patient's date of birth (YYYY-MM-DD)")
    gender: Gender = Field(..., description="Patient's gender")
    address: AddressSchema = Field(..., description="Patient's address information")
    emergency_contact: Optional[EmergencyContactSchema] = Field(None, description="Emergency contact information")
    medical_history: Optional[List[str]] = Field(None, description="List of medical conditions or history")
    insurance_info: Optional[InsuranceInfoSchema] = Field(None, description="Insurance information")
    
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
            parsed_number = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError('Invalid phone number format')
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
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v):
        today = date.today()
        
        # Check if date is in the future
        if v > today:
            raise ValueError('Date of birth cannot be in the future')
        
        # Calculate age for COPPA compliance (must be at least 13 years old)
        age = relativedelta(today, v).years
        if age < 13:
            raise ValueError('Must be at least 13 years old to register')
        
        # Reasonable upper limit (e.g., 120 years old)
        if age > 120:
            raise ValueError('Invalid date of birth')
        
        return v
    
    @field_validator('medical_history')
    @classmethod
    def validate_medical_history(cls, v):
        if v is not None:
            # Sanitize each medical condition
            sanitized_history = []
            for condition in v:
                if condition:  # Skip empty strings
                    sanitized_condition = sanitize_input(condition.strip())
                    if sanitized_condition:
                        sanitized_history.append(sanitized_condition)
            return sanitized_history if sanitized_history else None
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        if self.password and self.confirm_password and self.password != self.confirm_password:
            raise ValueError('Password and confirm password do not match')
        return self

class PatientResponseSchema(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    date_of_birth: date
    gender: Gender
    address: AddressSchema
    emergency_contact: Optional[EmergencyContactSchema]
    medical_history: Optional[List[str]]
    insurance_info: Optional[InsuranceInfoSchema]
    email_verified: bool
    phone_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class PatientRegistrationResponseSchema(BaseModel):
    success: bool = True
    message: str = "Patient registered successfully. Verification email sent."
    data: Dict[str, Any] = Field(..., description="Response data with patient_id, email, and verification status")

class PatientLoginResponseDataSchema(BaseModel):
    """Schema for patient data in login response (sanitized)."""
    patient_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    date_of_birth: str  # Convert to string for JSON response
    gender: str
    address: Dict[str, str]
    emergency_contact: Optional[Dict[str, str]]
    insurance_info: Optional[Dict[str, str]]
    email_verified: bool
    phone_verified: bool
    is_active: bool
    created_at: str
    updated_at: str

class ErrorResponseSchema(BaseModel):
    success: bool = False
    message: str
    errors: Optional[Dict[str, List[str]]] = None
    
class ValidationErrorResponseSchema(BaseModel):
    success: bool = False
    message: str = "Validation failed"
    errors: Dict[str, List[str]] = Field(..., description="Field-specific validation errors")

class PatientUpdateSchema(BaseModel):
    """Schema for updating patient information (excluding password and sensitive fields)."""
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone_number: Optional[str] = None
    address: Optional[AddressSchema] = None
    emergency_contact: Optional[EmergencyContactSchema] = None
    medical_history: Optional[List[str]] = None
    insurance_info: Optional[InsuranceInfoSchema] = None
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v):
        if v is not None:
            sanitized = sanitize_input(v)
            if not re.match(r'^[A-Za-z\s\-\'\.]+$', sanitized):
                raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
            return sanitized
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        if v is not None:
            try:
                parsed_number = phonenumbers.parse(v, None)
                if not phonenumbers.is_valid_number(parsed_number):
                    raise ValueError('Invalid phone number format')
                return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            except phonenumbers.NumberParseException:
                raise ValueError('Invalid phone number format. Please use international format (e.g., +1234567890)')
        return v 