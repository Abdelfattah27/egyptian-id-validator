from rest_framework import authentication
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _
from .models import APIKey
from django.core.cache import cache

import logging
logger = logging.getLogger(__name__)



class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Simple API Key authentication
    """
    
    header = 'X-API-Key'
    

    def get_api_key_data(self, api_key_value):
        """
        Get API key data from cache or database with Redis caching
        """
        if not api_key_value:
            raise exceptions.ValidationError(_('Invalid API key.'))
        
        cache_key = f"api_key_{api_key_value}"
        
        api_key_data = cache.get(cache_key)
        if api_key_data is None:
            
            # Fetch from database
            
            api_key_prefix = api_key_value[:8]
            active_keys = APIKey.objects.filter(revoked=False , prefix_key = api_key_prefix ).defer("created_at" , 'revoked' , 'metadata' , 'last_used_at' )
            for api_key_obj in active_keys:
                
                if api_key_obj.check_key(api_key_value):
                    cache.set(cache_key, api_key_obj, 300)
                    return api_key_obj
                
            logger.warning(f"Invalid API key: {api_key_value}")
            cache.set(cache_key, None, 60)
            
            raise exceptions.ValidationError(_('Invalid API key.'))
            
        
        return api_key_data

    
    def authenticate(self, request):
        api_key = self.get_api_key(request)
        
        if not api_key:
            raise exceptions.AuthenticationFailed("APIKey Required")
        
        try:
            api_key_obj = self.get_api_key_data(api_key)
        except exceptions.ValidationError as e:
            raise exceptions.AuthenticationFailed(e.detail)
        
        # Create a simple user-like object
        user = APIUser(api_key_obj)
        return (user, None)
    
    def get_api_key(self, request):
        """Extract API key from request headers"""
        return request.headers.get(self.header, '').strip()


class APIUser:
    """
    Simple user-like object for API key authentication
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.is_authenticated = True
    
    def __str__(self):
        return f"APIUser-{self.api_key.name}"