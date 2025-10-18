from django.db import models
import uuid
from django.contrib.auth.hashers import make_password , check_password
class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    hashed_key = models.CharField(max_length=255, editable=False)
    prefix_key = models.CharField(max_length=255, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked = models.BooleanField(default=False)
    quota_requests_per_minute = models.IntegerField(default=10)
    quota_requests_per_day = models.IntegerField(default=100)
    metadata = models.JSONField(default=dict, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    
    class Meta:
        db_table = 'api_keys'
        indexes = [
            models.Index(fields=['hashed_key']),
            models.Index(fields=['revoked']),
        ]
    
    def __str__(self):
        return f"{self.name}"
    
    def set_key(self, raw_key):
        """Hash and store the API key"""
        
        self.hashed_key = make_password(raw_key)
    
    def check_key(self, raw_key):
        """Verify the API key"""
        return check_password(raw_key , self.hashed_key)
    
    def is_active(self):
        return not self.revoked
    

class IDValidationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, null=True, blank=True)
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        
        db_table = 'id_validation_log'
        indexes = [
            models.Index(fields=['api_key', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['status_code']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"
    
        
        
