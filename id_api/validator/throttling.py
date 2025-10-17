from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)

class APIKeyRateThrottle(SimpleRateThrottle):
    """
    Throttle class for API key based rate limiting using X-API-Key header
    """
    cache = cache
    scope = 'api_key'
    
    def get_api_key_from_header(self, request):
        """Extract API key from X-API-Key header"""
        return  request.META.get('X_API_KEY') or request.META.get('HTTP_X_API_KEY')

    def get_cache_key(self, request, view):
        """
        Generate cache key based on API key
        """
        api_key_value = self.get_api_key_from_header(request)
        if api_key_value:
            # Use API key as identifier
            ident = api_key_value
        else:
            # Fallback to IP address if no API key
            ident = self.get_ident(request)
            
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
    
    def _get_custom_rate(self, request):
        """
        Determine custom rate based on API key quota
        """
        if hasattr(request.user , 'api_key'):
            minute_quota = request.user.api_key.quota_requests_per_minute
            return f"{minute_quota}/minute"
        
        # Default rate for requests without valid API key
        return '2/minute'
    
    def allow_request(self, request, view):
        """
        Check if the request should be allowed based on rate limits
        """
        # Set custom rate for this request
        custom_rate = self._get_custom_rate(request)
        self.rate = custom_rate
        self.num_requests, self.duration = self.parse_rate(custom_rate)
        
        return super().allow_request(request, view)
    
    def get_ident(self, request):
        """
        Override to include API key in identifier when available
        """
        api_key_value = self.get_api_key_from_header(request)
        if api_key_value:
            return f"apikey_{api_key_value}"
        
        # Fallback to default IP-based identification
        return super().get_ident(request)


class DailyAPIKeyThrottle(APIKeyRateThrottle):
    """
    Daily rate throttle for API keys
    """
    scope = 'api_key_daily'
    
    def _get_custom_rate(self, request):
        """
        Determine daily custom rate based on API key quota
        """
        
        if hasattr(request.user , 'api_key'):
            day_quota = request.user.api_key.quota_requests_per_day
            return f"{day_quota}/day"

        # Default daily rate for requests without valid API key
        return '100/day'
