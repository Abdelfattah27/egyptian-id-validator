from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import permissions
from drf_yasg.views import get_schema_view



schema_view = get_schema_view(
    openapi.Info(
        title="Egyptian National ID Validator API",
        default_version='v1',
        description="""
        A comprehensive API for validating and parsing Egyptian National ID numbers.
        
        ## Features
        
        - **ID Validation**: Validate Egyptian National IDs against official format
        - **Data Extraction**: Extract birth date, gender, governorate from valid IDs
        - **Rate Limiting**: Configurable request limits per API key
        - **Comprehensive Logging**: Detailed audit trail of all validations
        
        ## Authentication
        
        This API uses API Key authentication. Include your API key in the `X-API-KEY` header.
        
        ## National ID Format
        
        Egyptian National IDs consist of 14 digits:
        - **Digits 1-2**: Century code (2=1900s, 3=2000s)
        - **Digits 3-7**: Birth date in YYMMDD format
        - **Digits 8-9**: Governorate code
        - **Digits 10-13**: Serial number
        - **Digit 14**: Check digit (Luhn algorithm)
        
        ## Getting Started
        
        1. Create an API key using the `/api/v1/api-keys/` endpoint
        2. Use the API key in the `X-API-KEY` header for validation requests
        """,
        contact=openapi.Contact(email="abdelfattah.hamdy234@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)



# =============================================================================
# COMMON PARAMETERS
# =============================================================================

limit_parameter = openapi.Parameter(
    'limit',
    openapi.IN_QUERY,
    description="Number of results to return per page (default: 10, max: 100)",
    type=openapi.TYPE_INTEGER,
    default=10
)

offset_parameter = openapi.Parameter(
    'offset', 
    openapi.IN_QUERY,
    description="Starting position for results (default: 0)",
    type=openapi.TYPE_INTEGER,
    default=0
)

api_key_header = openapi.Parameter(
    'X-API-Key',
    openapi.IN_HEADER,
    description="API Key for authentication",
    type=openapi.TYPE_STRING,
    required=True
)

# =============================================================================
# COMMON RESPONSE SCHEMAS
# =============================================================================

# Success response for ID validation
validation_success_response = openapi.Response(
    description="Successful validation response",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the ID is valid'),
            'errors': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='List of validation errors if any'
            ),
            'parsed': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='Parsed ID data if valid',
                properties={
                    'raw': openapi.Schema(type=openapi.TYPE_STRING, description='Original national ID'),
                    'century_digit': openapi.Schema(type=openapi.TYPE_STRING, description='Century digit (2 or 3)'),
                    'birth_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Birth date in YYYY-MM-DD format'),
                    'age': openapi.Schema(type=openapi.TYPE_INTEGER, description='Calculated age from birth date'),
                    'governorate_code': openapi.Schema(type=openapi.TYPE_STRING, description='Governorate code'),
                    'governorate_name': openapi.Schema(type=openapi.TYPE_STRING, description='Governorate name'),
                    'serial': openapi.Schema(type=openapi.TYPE_STRING, description='Serial number'),
                    'gender': openapi.Schema(type=openapi.TYPE_STRING, enum=['male', 'female'], description='Gender'),
                    'checksum_ok': openapi.Schema(type=openapi.TYPE_BOOLEAN, nullable=True, description='Checksum validation result')
                }
            )
        }
    ),
    examples={
        "application/json": {
            "valid": True,
            "errors": [],
            "parsed": {
                "raw": "29001012100018",
                "century_digit": "2",
                "birth_date": "1990-01-01",
                "age": 35,
                "governorate_code": "21",
                "governorate_name": "Giza",
                "serial": "0001",
                "gender": "male",
                "checksum_ok": True
            }
        }
    }
)

# Error response for ID validation
validation_error_response = openapi.Response(
    description="Validation error response",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Always false for errors'),
            'errors': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='List of validation errors'
            ),
            'parsed': openapi.Schema(type=openapi.TYPE_FILE, description='Always null for errors')
        }
    ),
    examples={
        "application/json": {
            "valid": False,
            "errors": ["invalid_length"],
            "parsed": None
        }
    }
)

# Bad request response
bad_request_response = openapi.Response(
    description="Bad request - invalid input",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'parsed': openapi.Schema(type=openapi.TYPE_FILE)
        }
    ),
    examples={
        "application/json": {
            "valid": False,
            "errors": ["Invalid request: national_id"],
            "parsed": None
        }
    }
)

# Unauthorized response
unauthorized_response = openapi.Response(
    description="Unauthorized - missing or invalid API key",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    examples={
        "application/json": {
            "detail": "Authentication credentials were not provided."
        }
    }
)

# Forbidden response
forbidden_response = openapi.Response(
    description="Forbidden - invalid or revoked API key",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    examples={
        "application/json": {
            "detail": "Invalid API key."
        }
    }
)

# Throttled response
throttled_response = openapi.Response(
    description="Too many requests - rate limit exceeded",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    examples={
        "application/json": {
            "detail": "Request was throttled. Expected available in 60 seconds."
        }
    }
)

# Paginated logs response
paginated_logs_response = openapi.Response(
    description="Paginated validation logs retrieved successfully",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description='Total number of log entries'
            ),
            'next': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_URI,
                description='URL for next page of results, null if no more pages',
                nullable=True
            ),
            'previous': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_URI, 
                description='URL for previous page of results, null if first page',
                nullable=True
            ),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_UUID,
                            description='Unique identifier for the log entry'
                        ),
                        'api_key_name': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Name of the API key used for the request'
                        ),
                        'api_key': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_UUID,
                            description='UUID of the API key used'
                        ),
                        'endpoint': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='API endpoint that was called'
                        ),
                        'method': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            enum=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
                            description='HTTP method used for the request'
                        ),
                        'status_code': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='HTTP status code of the response'
                        ),
                        'response_time': openapi.Schema(
                            type=openapi.TYPE_NUMBER,
                            format=openapi.FORMAT_FLOAT,
                            description='Response time in milliseconds'
                        ),
                        'ip_address': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_IPV4,
                            description='IP address of the client'
                        ),
                        'user_agent': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='User agent string of the client'
                        ),
                        'request_data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Request payload with PII protection',
                            properties={
                                'national_id': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description='Masked national ID (first 8 digits shown)'
                                ),
                                'strict_checksum': openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description='Whether strict checksum validation was enabled'
                                )
                            }
                        ),
                        'response_data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Response data from validation',
                            properties={
                                'valid': openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description='Whether the national ID was valid'
                                ),
                                'errors': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Items(type=openapi.TYPE_STRING),
                                    description='List of validation errors if any'
                                ),
                                'parsed': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description='Parsed national ID data',
                                    nullable=True
                                )
                            }
                        ),
                        'created_at': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_DATETIME,
                            description='Timestamp when the log entry was created'
                        )
                    }
                )
            )
        }
    )
)

# API key creation response
api_key_create_response = openapi.Response(
    description="API key created successfully",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING),
            'api_key': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'key': openapi.Schema(type=openapi.TYPE_STRING, description='The actual API key - store this securely!'),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'quota_requests_per_minute': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'quota_requests_per_day': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'metadata': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        }
    ),
    examples={
        "application/json": {
            "message": "API key created successfully",
            "api_key": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "My Application",
                "key": "raw_api_key_value_here",
                "created_at": "2024-01-15T10:30:00Z",
                "quota_requests_per_minute": 100,
                "quota_requests_per_day": 5000,
                "metadata": {}
            }
        }
    }
)

# =============================================================================
# REQUEST BODY SCHEMAS
# =============================================================================

# Request body for ID validation
validate_id_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['national_id'],
    properties={
        'national_id': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Egyptian National ID number (14 digits)',
            example='29001012100018',
            min_length=14,
            max_length=14
        ),
        'strict_checksum': openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description='Whether to strictly validate checksum (default: false)',
            default=False
        )
    }
)

# Request body for API key creation
api_key_create_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Name for the API key (for identification)',
            example='My Production API Key',
            min_length=1,
            max_length=100
        ),
        'quota_requests_per_minute': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Maximum requests per minute (default: 60)',
            default=60,
            minimum=1,
            maximum=1000
        ),
        'quota_requests_per_day': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Maximum requests per day (default: 1000)',
            default=1000,
            minimum=10,
            maximum=100000
        ),
        'metadata': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Additional metadata for the API key',
            additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
        )
    }
)

# =============================================================================
# SWAGGER AUTO SCHEMA DECORATORS
# =============================================================================

# Decorator for ValidateIDView
validate_id_decorator = swagger_auto_schema(
    operation_description="""
    Validate an Egyptian National ID and extract personal information.
    
    This endpoint validates the provided 14-digit Egyptian National ID and returns
    detailed information including birth date, gender, governorate, and age.
    
    **Authentication**: Required (API Key in X-API-Key header)
    **Rate Limits**: Enforced per API key
    """,
    request_body=validate_id_request_body,
    responses={
        status.HTTP_200_OK: validation_success_response,
        status.HTTP_400_BAD_REQUEST: bad_request_response,
        status.HTTP_403_FORBIDDEN: forbidden_response,
        status.HTTP_429_TOO_MANY_REQUESTS: throttled_response,
    },
    tags=['ID Validation'],
    operation_id="validate_national_id"
)

# Decorator for APIKeyCreateView
api_key_create_decorator = swagger_auto_schema(
    operation_description="""
    Create a new API key for accessing the validation service.
    
    Generates a cryptographically secure API key with customizable rate limits.
    The raw API key is returned only once - store it securely.
    """,
    request_body=api_key_create_request_body,
    responses={
        status.HTTP_201_CREATED: api_key_create_response,
        status.HTTP_400_BAD_REQUEST: bad_request_response,
    },
    tags=['API Keys'],
    operation_id="create_api_key"
)

# Decorator for IDValidationLogAPIView
validation_logs_decorator = swagger_auto_schema(
    operation_description="""
    Retrieve a paginated list of national ID validation logs.
    
    Returns detailed audit trail of all validation requests including request metadata,
    response data, and performance metrics. National IDs are masked for privacy.
    
    **Authentication**: Required (API Key)
    **Permissions**: Users can only see their own logs unless admin
    """,
    manual_parameters=[limit_parameter, offset_parameter],
    responses={
        status.HTTP_200_OK: paginated_logs_response,
    },
    tags=['Validation Logs'],
    operation_id="list_validation_logs"
)