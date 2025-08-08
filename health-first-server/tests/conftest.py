import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from app.services.provider_service import ProviderService
from app.services.provider_repository import ProviderRepositoryInterface

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client() -> TestClient:
    """Create a test client for FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_provider_repository() -> AsyncMock:
    """Create a mock provider repository."""
    mock_repo = AsyncMock(spec=ProviderRepositoryInterface)
    return mock_repo

@pytest.fixture
def provider_service_with_mock_repo(mock_provider_repository) -> ProviderService:
    """Create a provider service with mocked repository."""
    service = ProviderService()
    service.repository = mock_provider_repository
    return service

@pytest.fixture
def valid_provider_data() -> dict:
    """Valid provider registration data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@clinic.com",
        "phone_number": "+1234567890",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "specialization": "Cardiology",
        "license_number": "MD123456789",
        "years_of_experience": 10,
        "clinic_address": {
            "street": "123 Medical Center Dr",
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        }
    }

@pytest.fixture
def invalid_provider_data() -> dict:
    """Invalid provider registration data for testing."""
    return {
        "first_name": "A",  # Too short
        "last_name": "",    # Empty
        "email": "invalid-email",  # Invalid format
        "phone_number": "123",     # Invalid format
        "password": "weak",        # Too weak
        "confirm_password": "different",  # Doesn't match
        "specialization": "XY",    # Too short
        "license_number": "MD@123", # Contains special characters
        "years_of_experience": -1,  # Negative
        "clinic_address": {
            "street": "",  # Empty
            "city": "",    # Empty
            "state": "",   # Empty
            "zip": "invalid123456789"  # Too long
        }
    }

@pytest.fixture
def duplicate_provider_data() -> dict:
    """Provider data that would cause duplicate conflicts."""
    return {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "existing@clinic.com",  # Duplicate email
        "phone_number": "+9876543210",   # Duplicate phone
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "specialization": "Neurology",
        "license_number": "EXISTING123",  # Duplicate license
        "years_of_experience": 15,
        "clinic_address": {
            "street": "456 Health Ave",
            "city": "Boston",
            "state": "MA",
            "zip": "02101"
        }
    }

@pytest.fixture
def mock_created_provider() -> dict:
    """Mock created provider response."""
    return {
        "provider_id": "550e8400-e29b-41d4-a716-446655440000",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@clinic.com",
        "phone_number": "+1234567890",
        "specialization": "Cardiology",
        "license_number": "MD123456789",
        "years_of_experience": 10,
        "clinic_address": {
            "street": "123 Medical Center Dr",
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        },
        "verification_status": "pending",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    } 