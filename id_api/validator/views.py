import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from .serializers import ValidateIDRequestSerializer, ValidateIDResponseSerializer , APIKeyCreateSerializer  , IDValidationLogSerializer
from .helper import EgyptianIDValidator
from .tasks import log_validation_task  
from .throttling import APIKeyRateThrottle , DailyAPIKeyThrottle 
from .models import APIKey , IDValidationLog
from .authentication import APIKeyAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .swagger_schema import api_key_create_response ,validate_id_request_body ,validation_success_response , unauthorized_response, bad_request_response, throttled_response ,api_key_create_request_body
from rest_framework.pagination import LimitOffsetPagination
from .swagger_schema import (
    validate_id_decorator,
    api_key_create_decorator, 
    validation_logs_decorator
)

class ValidationLogPagination(LimitOffsetPagination):
    """
    Custom pagination for validation logs
    """
    default_limit = 10
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    
    
class IDValidationLogAPIView(generics.ListAPIView) : 
    queryset = IDValidationLog.objects.all().order_by("-created_at")
    serializer_class = IDValidationLogSerializer
    pagination_class = ValidationLogPagination
    
    @validation_logs_decorator
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ValidateIDView(APIView):
    """
    API endpoint for validating Egyptian National IDs
    """
    throttle_classes =[APIKeyRateThrottle , DailyAPIKeyThrottle]
    authentication_classes = [APIKeyAuthentication]
    
    
    @validate_id_decorator
    def post(self, request):
        start_time = time.time()
        
        # Validate request data
        serializer = ValidateIDRequestSerializer(data=request.data)
        if not serializer.is_valid():
            response_time = self._calculate_response_time(start_time)
            return self._build_error_response(
                status.HTTP_400_BAD_REQUEST,
                request,
                [f"Invalid request: {', '.join(serializer.errors.keys())}"],
                response_time
            )
        
        national_id = serializer.validated_data['national_id']
        strict_checksum = serializer.validated_data.get('strict_checksum', False)
        
        # Validate and parse ID
        is_valid, errors, parsed_data = EgyptianIDValidator.validate_and_parse(
            national_id, strict_checksum
        )
        
        # Calculate response time before building response
        response_time = self._calculate_response_time(start_time)
        
        # Prepare response
        response_data = {
            "valid": is_valid,
            "errors": errors,
            "parsed": parsed_data if is_valid else None
        }
        
        # Log the validation asynchronously using Celery
        self._log_validation_async(
            request, national_id, strict_checksum, is_valid, 
            errors, parsed_data, response_data, response_time, status.HTTP_200_OK
        )
        status_number = status.HTTP_200_OK
        if errors : 
            status_number = status.HTTP_400_BAD_REQUEST
            
        
        # Validate response format
        response_serializer = ValidateIDResponseSerializer(data=response_data)
        if response_serializer.is_valid():
            return Response(response_serializer.validated_data , status=status_number)
        else:
            return self._build_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                request,
                ["internal_validation_error"],
                response_time
            )
    
    def _calculate_response_time(self, start_time):
        """Calculate response time in milliseconds"""
        return (time.time() - start_time) * 1000  # Convert to milliseconds
    
    def _build_error_response(self, status_code, request, errors, response_time):
        """Build error response and log it"""
        response_data = {
            "valid": False,
            "errors": errors,
            "parsed": None
        }
        
        # Log the error validation
        self._log_error_validation(request, response_data, response_time, status_code)
        
        return Response(response_data, status=status_code)
    
    def _log_error_validation(self, request, response_data, response_time, status_code):
        """Log error validation asynchronously"""
        try:
            client_ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Prepare request data for logging (masked since validation failed)
            request_log_data = {
                "national_id": "****",  # Masked for errors
                "strict_checksum": request.data.get('strict_checksum', False)
            }
            
            # Get API key info if available
            api_key_id = self._get_api_key_id(request)
            
            # Send to Celery worker for async processing
            log_validation_task.delay(
                api_key_id=api_key_id,
                endpoint=request.path,
                method=request.method,
                status_code=status_code,
                response_time=response_time,
                ip_address=client_ip,
                user_agent=user_agent,
                request_data=request_log_data,
                response_data=response_data
            )
        except Exception:
            # Logging failures shouldn't break the API
            pass
    
    def _log_validation_async(self, request, national_id, strict_checksum, is_valid, 
                            errors, parsed_data, response_data, response_time, status_code):
        """Log validation request asynchronously using Celery"""
        try:
            client_ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Prepare request and response data for logging
            request_log_data = {
                "national_id": national_id[:8] + "****" if is_valid else national_id,  # Mask sensitive data
                "strict_checksum": strict_checksum
            }
            
            # Get API key info if available
            api_key_id = self._get_api_key_id(request)
            
            # Send to Celery worker for async processing with new signature
            log_validation_task.delay(
                api_key_id=api_key_id,
                endpoint=request.path,
                method=request.method,
                status_code=status_code,
                response_time=response_time,
                ip_address=client_ip,
                user_agent=user_agent,
                request_data=request_log_data,
                response_data=response_data
            )
        except Exception:
            # Logging failures shouldn't break the API
            pass
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_api_key_id(self, request):
        """Extract API key ID from request if available"""

        api_key = getattr(request.user, 'api_key', None)
        return str(api_key.id) if api_key else None
    
    
    

class APIKeyCreateView(generics.CreateAPIView):
    """
    Endpoint to create a new API key
    """
    queryset = APIKey.objects.all()
    serializer_class = APIKeyCreateSerializer
    permission_classes = []
    
    @api_key_create_decorator
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        api_key = serializer.save()
        
        # Prepare response data
        response_data = {
            'message': 'API key created successfully',
            'api_key': {
                'id': api_key.id,
                'name': api_key.name,
                'key': api_key._raw_key,
                'created_at': api_key.created_at,
                'quota_requests_per_minute': api_key.quota_requests_per_minute,
                'quota_requests_per_day': api_key.quota_requests_per_day,
                'metadata': api_key.metadata
            }        
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)