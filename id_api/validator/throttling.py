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
        return  request.META.get('X_API_KEY') or request.META.get('HTTP_X_API_KEY')

    def get_cache_key(self, request, view):
    
        api_key_value = self.get_api_key_from_header(request)
        if api_key_value:
            ident = api_key_value
        else:
            ident = self.get_ident(request)
            
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
    
    def _get_custom_rate(self, request):

        if hasattr(request.user , 'api_key'):
            minute_quota = request.user.api_key.quota_requests_per_minute
            return f"{minute_quota}/minute"
        
        return '2/minute'
    
    def allow_request(self, request, view):

        custom_rate = self._get_custom_rate(request)
        self.rate = custom_rate
        self.num_requests, self.duration = self.parse_rate(custom_rate)
        
        return super().allow_request(request, view)
    
    def get_ident(self, request):

        api_key_value = self.get_api_key_from_header(request)
        if api_key_value:
            return f"apikey_{api_key_value}"
        
        return super().get_ident(request)


class DailyAPIKeyThrottle(APIKeyRateThrottle):
    scope = 'api_key_daily'
    
    def _get_custom_rate(self, request):
        
        if hasattr(request.user , 'api_key'):
            day_quota = request.user.api_key.quota_requests_per_day
            return f"{day_quota}/day"

        return '100/day'
