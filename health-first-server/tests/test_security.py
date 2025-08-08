import pytest
from app.utils.security import hash_password, verify_password, validate_password_strength

class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        # Verify hash is not the original password
        assert hashed != password
        
        # Verify hash starts with bcrypt identifier
        assert hashed.startswith("$2b$")
        
        # Verify hash is consistent length (bcrypt hashes are 60 characters)
        assert len(hashed) == 60
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        
        # Verify wrong password fails
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "SecurePassword123!"
        password2 = "DifferentPassword456@"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        # Different passwords should have different hashes
        assert hash1 != hash2
    
    def test_same_password_different_salts(self):
        """Test that the same password produces different hashes due to salting."""
        password = "SecurePassword123!"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Same password should have different hashes due to random salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

class TestPasswordStrength:
    """Test password strength validation."""
    
    def test_minimum_length_requirement(self):
        """Test minimum length requirement."""
        # Too short
        is_valid, errors = validate_password_strength("Pass1!")
        assert not is_valid
        assert any("at least 8 characters" in error for error in errors)
        
        # Exactly 8 characters
        is_valid, errors = validate_password_strength("Pass123!")
        assert is_valid
    
    def test_maximum_length_requirement(self):
        """Test maximum length requirement."""
        # Create a password longer than 100 characters
        long_password = "P" * 95 + "123!@"  # 101 characters
        is_valid, errors = validate_password_strength(long_password)
        assert not is_valid
        assert any("no more than 100 characters" in error for error in errors)
    
    def test_uppercase_requirement(self):
        """Test uppercase letter requirement."""
        # No uppercase
        is_valid, errors = validate_password_strength("password123!")
        assert not is_valid
        assert any("uppercase letter" in error for error in errors)
        
        # With uppercase
        is_valid, errors = validate_password_strength("Password123!")
        assert is_valid
    
    def test_lowercase_requirement(self):
        """Test lowercase letter requirement."""
        # No lowercase
        is_valid, errors = validate_password_strength("PASSWORD123!")
        assert not is_valid
        assert any("lowercase letter" in error for error in errors)
        
        # With lowercase
        is_valid, errors = validate_password_strength("Password123!")
        assert is_valid
    
    def test_digit_requirement(self):
        """Test digit requirement."""
        # No digit
        is_valid, errors = validate_password_strength("Password!")
        assert not is_valid
        assert any("digit" in error for error in errors)
        
        # With digit
        is_valid, errors = validate_password_strength("Password1!")
        assert is_valid
    
    def test_special_character_requirement(self):
        """Test special character requirement."""
        # No special character
        is_valid, errors = validate_password_strength("Password123")
        assert not is_valid
        assert any("special character" in error for error in errors)
        
        # With various special characters
        special_chars = "!@#$%^&*(),.?\":{}|<>"
        for char in special_chars:
            password = f"Password123{char}"
            is_valid, errors = validate_password_strength(password)
            assert is_valid, f"Password with '{char}' should be valid"
    
    def test_comprehensive_weak_passwords(self):
        """Test various weak password patterns."""
        weak_passwords = [
            "12345678",           # Only digits
            "password",           # Only lowercase
            "PASSWORD",           # Only uppercase
            "Password",           # Missing digit and special char
            "Password123",        # Missing special char
            "Password!",          # Missing digit
            "pass123!",           # Missing uppercase
            "PASS123!",           # Missing lowercase
            "",                   # Empty
            "P@1",                # Too short but has all types
        ]
        
        for password in weak_passwords:
            is_valid, errors = validate_password_strength(password)
            assert not is_valid, f"Password '{password}' should be invalid"
            assert len(errors) > 0, f"Password '{password}' should have error messages"
    
    def test_comprehensive_strong_passwords(self):
        """Test various strong password patterns."""
        strong_passwords = [
            "SecurePass123!",
            "MyStr0ng#P@ssw0rd",
            "Complex@Password1",
            "Valid123$Password",
            "Tr0ub4dor&3",
            "xkcd927!Correct",
            "P@ssw0rd2024!",
            "MyC0mplex#Pass"
        ]
        
        for password in strong_passwords:
            is_valid, errors = validate_password_strength(password)
            assert is_valid, f"Password '{password}' should be valid, but got errors: {errors}"
            assert len(errors) == 0, f"Strong password should have no errors: {errors}" 