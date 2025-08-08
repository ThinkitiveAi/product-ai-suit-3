# Health First Provider Registration API

A secure and validated provider registration system built with FastAPI, supporting both SQL (MySQL/PostgreSQL) and NoSQL (MongoDB) databases.

## Features

- 🔐 **Secure Authentication**: bcrypt password hashing with 12+ salt rounds
- ✅ **Comprehensive Validation**: Email, phone, password strength, and field validation
- 🗄️ **Multi-Database Support**: MySQL, PostgreSQL, MongoDB, and SQLite fallback
- 🚫 **Security Hardened**: Input sanitization, injection prevention, no password logging
- 📱 **International Phone Support**: E.164 format validation
- 🏥 **Medical Specializations**: Predefined and custom specialization support
- 🧪 **Fully Tested**: Comprehensive unit tests with pytest

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_TYPE=postgresql  # or mysql, mongodb
POSTGRESQL_URL=postgresql+psycopg2://user:password@localhost:5432/healthfirst
MYSQL_URL=mysql+pymysql://user:password@localhost:3306/healthfirst
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=healthfirst

# Security
SECRET_KEY=your-secret-key-change-in-production
BCRYPT_ROUNDS=12

# Debug Mode
DEBUG=true
```

### 3. Run the Application

```bash
python main.py
```

The API will be available at: **http://localhost:8000**

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Setup

The application will automatically:
- Fall back to SQLite if configured databases are unavailable
- Create necessary tables and indexes
- Handle database connection failures gracefully

### For Production

Set up your preferred database:

**PostgreSQL:**
```sql
CREATE DATABASE healthfirst;
CREATE USER healthfirst_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE healthfirst TO healthfirst_user;
```

**MySQL:**
```sql
CREATE DATABASE healthfirst;
CREATE USER 'healthfirst_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON healthfirst.* TO 'healthfirst_user'@'localhost';
```

**MongoDB:**
```bash
# MongoDB will create the database automatically
```

## API Endpoints

### Provider Registration
- **POST** `/api/v1/provider/register` - Register a new provider
- **GET** `/api/v1/provider/validate` - Validate field uniqueness
- **GET** `/api/v1/provider/{provider_id}` - Get provider information

### Health Checks
- **GET** `/` - Basic health check
- **GET** `/health` - Detailed health check with database status

## Example Usage

### Register a Provider

```bash
curl -X POST "http://localhost:8000/api/v1/provider/register" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### Validate Field Uniqueness

```bash
curl "http://localhost:8000/api/v1/provider/validate?email=john.doe@clinic.com"
```

## Validation Rules

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character

### Field Constraints
- **Names**: 2-50 characters, letters with basic punctuation
- **Email**: Valid format, unique
- **Phone**: International E.164 format, unique
- **License**: Alphanumeric only, unique
- **Experience**: 0-50 years
- **Specialization**: Predefined list or custom (3-100 characters)

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test categories
pytest tests/test_validation.py
pytest tests/test_security.py
pytest tests/test_duplicate_scenarios.py
pytest tests/test_api_endpoints.py
```

## Security Features

- **Password Hashing**: bcrypt with configurable salt rounds
- **Input Sanitization**: Prevents XSS and injection attacks
- **Validation**: Comprehensive field and format validation
- **No Sensitive Data Logging**: Passwords never logged or exposed
- **Unique Constraints**: Email, phone, and license number uniqueness

## Error Handling

The API provides detailed error responses:

- **422**: Validation errors with field-specific messages
- **409**: Conflict errors for duplicate data
- **500**: Server errors with user-friendly messages
- **404**: Resource not found

## Development

### Project Structure

```
health-first-server/
├── app/
│   ├── api/                 # API endpoints
│   ├── database/           # Database connections
│   ├── models/             # Data models (SQL & NoSQL)
│   ├── schemas/            # Pydantic validation schemas
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License. 