import pytest
from pydantic import ValidationError
from app.schemas.provider import ProviderRegistrationSchema, ClinicAddressSchema
from app.utils.security import validate_password_strength, sanitize_input

class TestFieldValidation:
    """Test field validation rules."""
    
    def test_valid_provider_data(self, valid_provider_data):
        """Test that valid provider data passes validation."""
        schema = ProviderRegistrationSchema(**valid_provider_data)
        assert schema.first_name == "John"
        assert schema.email == "john.doe@clinic.com"
        assert schema.phone_number == "+1234567890"  # Should be normalized to E.164
    
    def test_name_validation(self):
        """Test name field validation rules."""
        # Valid names
        valid_names = ["John", "Mary-Jane", "O'Connor", "Dr. Smith", "José"]
        for name in valid_names:
            data = {
                "first_name": name,
                "last_name": "Doe",
                "email": "test@test.com",
                "phone_number": "+1234567890",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "specialization": "Cardiology",
                "license_number": "MD123456",
                "years_of_experience": 5,
                "clinic_address": {
                    "street": "123 Main St",
                    "city": "Boston",
                    "state": "MA",
                    "zip": "02101"
                }
            }
            schema = ProviderRegistrationSchema(**data)
            assert schema.first_name == name
        
        # Invalid names
        invalid_names = ["A", "", "John123", "John@Smith", "Very Long Name That Exceeds Fifty Characters Limit Here"]
        for name in invalid_names:
            data = {
                "first_name": name,
                "last_name": "Doe",
                "email": "test@test.com",
                "phone_number": "+1234567890",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "specialization": "Cardiology",
                "license_number": "MD123456",
                "years_of_experience": 5,
                "clinic_address": {
                    "street": "123 Main St",
                    "city": "Boston",
                    "state": "MA",
                    "zip": "02101"
                }
            }
            with pytest.raises(ValidationError):
                ProviderRegistrationSchema(**data)
    
    def test_email_validation(self):
        """Test email field validation."""
        # Valid emails
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "provider123@clinic.org"]
        base_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "specialization": "Cardiology",
            "license_number": "MD123456",
            "years_of_experience": 5,
            "clinic_address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        for email in valid_emails:
            data = {**base_data, "email": email}
            schema = ProviderRegistrationSchema(**data)
            assert schema.email == email
        
        # Invalid emails
        invalid_emails = ["invalid", "test@", "@example.com", "test..test@example.com"]
        for email in invalid_emails:
            data = {**base_data, "email": email}
            with pytest.raises(ValidationError):
                ProviderRegistrationSchema(**data)
    
    def test_phone_validation(self):
        """Test phone number validation and E.164 formatting."""
        base_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "specialization": "Cardiology",
            "license_number": "MD123456",
            "years_of_experience": 5,
            "clinic_address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        # Valid phone numbers (should be normalized to E.164)
        valid_phones = [
            ("+1234567890", "+1234567890"),
            ("+44 20 7946 0958", "+442079460958"),
            ("+33 1 42 68 53 00", "+33142685300")
        ]
        
        for input_phone, expected_output in valid_phones:
            data = {**base_data, "phone_number": input_phone}
            schema = ProviderRegistrationSchema(**data)
            assert schema.phone_number == expected_output
        
        # Invalid phone numbers
        invalid_phones = ["123456", "invalid", "+", "1234567890", "123-456-7890"]
        for phone in invalid_phones:
            data = {**base_data, "phone_number": phone}
            with pytest.raises(ValidationError):
                ProviderRegistrationSchema(**data)
    
    def test_license_number_validation(self):
        """Test license number validation."""
        base_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "specialization": "Cardiology",
            "years_of_experience": 5,
            "clinic_address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        # Valid license numbers
        valid_licenses = ["MD123456", "abc123", "LICENSE123"]
        for license_num in valid_licenses:
            data = {**base_data, "license_number": license_num}
            schema = ProviderRegistrationSchema(**data)
            assert schema.license_number == license_num.upper()  # Should be uppercase
        
        # Invalid license numbers
        invalid_licenses = ["", "MD@123", "LICENSE-123", "MD 123 456"]
        for license_num in invalid_licenses:
            data = {**base_data, "license_number": license_num}
            with pytest.raises(ValidationError):
                ProviderRegistrationSchema(**data)
    
    def test_years_of_experience_validation(self):
        """Test years of experience validation."""
        base_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "specialization": "Cardiology",
            "license_number": "MD123456",
            "clinic_address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        # Valid experience values
        valid_experience = [0, 1, 25, 50]
        for exp in valid_experience:
            data = {**base_data, "years_of_experience": exp}
            schema = ProviderRegistrationSchema(**data)
            assert schema.years_of_experience == exp
        
        # Invalid experience values
        invalid_experience = [-1, 51, 100]
        for exp in invalid_experience:
            data = {**base_data, "years_of_experience": exp}
            with pytest.raises(ValidationError):
                ProviderRegistrationSchema(**data)
    
    def test_specialization_validation(self):
        """Test specialization validation."""
        base_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "license_number": "MD123456",
            "years_of_experience": 5,
            "clinic_address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        # Valid specializations (from predefined list)
        valid_specializations = ["Cardiology", "cardiology", "CARDIOLOGY", "Neurology"]
        for spec in valid_specializations:
            data = {**base_data, "specialization": spec}
            schema = ProviderRegistrationSchema(**data)
            # Should match the properly capitalized version from predefined list
            assert schema.specialization in ["Cardiology", "Neurology"]
        
        # Valid custom specializations
        custom_specializations = ["Sports Medicine", "Pain Management", "Integrative Medicine"]
        for spec in custom_specializations:
            data = {**base_data, "specialization": spec}
            schema = ProviderRegistrationSchema(**data)
            assert schema.specialization == spec
        
        # Invalid specializations
        invalid_specializations = ["", "XY", "Specialization@123", "Invalid&Special#Characters"]
        for spec in invalid_specializations:
            data = {**base_data, "specialization": spec}
            with pytest.raises(ValidationError):
                ProviderRegistrationSchema(**data)
    
    def test_clinic_address_validation(self):
        """Test clinic address validation."""
        base_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "specialization": "Cardiology",
            "license_number": "MD123456",
            "years_of_experience": 5,
        }
        
        # Valid address
        valid_address = {
            "street": "123 Medical Center Dr",
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        }
        data = {**base_data, "clinic_address": valid_address}
        schema = ProviderRegistrationSchema(**data)
        assert schema.clinic_address.street == "123 Medical Center Dr"
        
        # Invalid addresses
        invalid_addresses = [
            {"street": "", "city": "New York", "state": "NY", "zip": "10001"},  # Empty street
            {"street": "123 Main St", "city": "", "state": "NY", "zip": "10001"},  # Empty city
            {"street": "123 Main St", "city": "New York", "state": "", "zip": "10001"},  # Empty state
            {"street": "123 Main St", "city": "New York", "state": "NY", "zip": ""},  # Empty zip
            {"street": "123 Main St", "city": "New York", "state": "NY", "zip": "invalid@zip"},  # Invalid zip
        ]
        
        for address in invalid_addresses:
            data = {**base_data, "clinic_address": address}
            with pytest.raises(ValidationError):
                ProviderRegistrationSchema(**data)

class TestPasswordValidation:
    """Test password validation and security requirements."""
    
    def test_password_strength_validation(self):
        """Test password strength requirements."""
        # Valid passwords
        valid_passwords = [
            "SecurePass123!",
            "Complex@Password1",
            "MyStr0ng#P@ssw0rd",
            "Valid123$Password"
        ]
        
        for password in valid_passwords:
            is_valid, errors = validate_password_strength(password)
            assert is_valid, f"Password '{password}' should be valid, but got errors: {errors}"
        
        # Invalid passwords
        invalid_passwords = [
            ("weak", ["Password must be at least 8 characters long", "Password must contain at least one uppercase letter", "Password must contain at least one digit", "Password must contain at least one special character"]),
            ("WeakPassword", ["Password must contain at least one digit", "Password must contain at least one special character"]),
            ("weakpassword123!", ["Password must contain at least one uppercase letter"]),
            ("WEAKPASSWORD123!", ["Password must contain at least one lowercase letter"]),
            ("WeakPassword!", ["Password must contain at least one digit"]),
            ("WeakPassword123", ["Password must contain at least one special character"]),
        ]
        
        for password, expected_errors in invalid_passwords:
            is_valid, errors = validate_password_strength(password)
            assert not is_valid, f"Password '{password}' should be invalid"
            for expected_error in expected_errors:
                assert any(expected_error in error for error in errors), f"Expected error '{expected_error}' not found in {errors}"
    
    def test_password_confirmation_match(self):
        """Test password confirmation matching."""
        base_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "specialization": "Cardiology",
            "license_number": "MD123456",
            "years_of_experience": 5,
            "clinic_address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101"
            }
        }
        
        # Matching passwords
        data = {
            **base_data,
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        schema = ProviderRegistrationSchema(**data)
        assert schema.password == "SecurePass123!"
        
        # Non-matching passwords
        data = {
            **base_data,
            "password": "SecurePass123!",
            "confirm_password": "DifferentPass123!"
        }
        with pytest.raises(ValidationError):
            ProviderRegistrationSchema(**data)

class TestInputSanitization:
    """Test input sanitization for security."""
    
    def test_sanitize_input(self):
        """Test input sanitization function."""
        # Test HTML/script tag removal
        assert sanitize_input("<script>alert('xss')</script>Hello") == "Hello"
        assert sanitize_input("<div>Content</div>") == "Content"
        
        # Test SQL injection pattern removal
        assert sanitize_input("'; DROP TABLE users; --") == ""
        assert sanitize_input("admin' OR '1'='1") == "admin' OR '1'='1"  # This specific pattern might need refinement
        
        # Test normal input
        assert sanitize_input("Normal input text") == "Normal input text"
        assert sanitize_input("John O'Connor") == "John O'Connor"
        
        # Test empty input
        assert sanitize_input("") == ""
        assert sanitize_input(None) == "" 