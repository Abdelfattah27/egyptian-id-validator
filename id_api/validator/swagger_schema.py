# swagger_schema.py
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

# Common response schemas
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
                    'raw': openapi.Schema(type=openapi.TYPE_STRING, description='Original ID'),
                    'century_digit': openapi.Schema(type=openapi.TYPE_STRING, description='Century digit (2 or 3)'),
                    'birth_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Birth date in YYYY-MM-DD format'),
                    'governorate_code': openapi.Schema(type=openapi.TYPE_STRING, description='Governorate code'),
                    'governorate_name': openapi.Schema(type=openapi.TYPE_STRING, description='Governorate name'),
                    'serial': openapi.Schema(type=openapi.TYPE_STRING, description='Serial number'),
                    'gender': openapi.Schema(type=openapi.TYPE_STRING, description='Gender (male/female)'),
                    'checksum_ok': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Checksum validation result')
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
                "governorate_code": "21",
                "governorate_name": "Giza",
                "serial": "0001",
                "gender": "male",
                "checksum_ok": True
            }
        }
    }
)

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
            "errors": ["Checksum validation failed."],
            "parsed": None
        }
    }
)

bad_request_response = openapi.Response(
    description="Bad request - invalid input",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'parsed': openapi.Schema(type=openapi.TYPE_FILE)
        }
    )
)

unauthorized_response = openapi.Response(
    description="Unauthorized - missing or invalid API key",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING)
        }
    )
)

throttled_response = openapi.Response(
    description="Too many requests - rate limit exceeded",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING)
        }
    )
)

# Request body schema for ID validation
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

# Request body schema for API key creation
api_key_create_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Name for the API key (for identification)',
            example='My Production API Key'
        ),
        'quota_requests_per_minute': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Maximum requests per minute (default: 10)',
            default=10,
            minimum=1,
            maximum=100
        ),
        'quota_requests_per_day': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Maximum requests per day (default: 1000)',
            default=1000,
            minimum=10,
            maximum=10000
        ),
        'metadata': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Additional metadata for the API key',
            additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
        )
    }
)

# API key creation response schema
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
    )
)