from rest_framework import serializers
from .models import APIKey, IDValidationLog 

class ValidateIDRequestSerializer(serializers.Serializer):
    national_id = serializers.CharField()
    strict_checksum = serializers.BooleanField(default=False, required=False)

class ParsedIDSerializer(serializers.Serializer):
    raw = serializers.CharField()
    century_digit = serializers.CharField()
    birth_date = serializers.DateField(format='iso-8601')
    age = serializers.IntegerField()
    governorate_code = serializers.CharField()
    governorate_name = serializers.CharField()
    serial = serializers.CharField()
    gender = serializers.CharField()
    checksum_ok = serializers.BooleanField(allow_null=True)

class ValidateIDResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField())
    parsed = ParsedIDSerializer(allow_null=True)


class APIKeyCreateSerializer(serializers.ModelSerializer):
    key = serializers.CharField(
        write_only=True,
        required=False,
        help_text="API key value. If not provided, one will be generated automatically."
    )
    
    class Meta:
        model = APIKey
        fields = [
            'name', 'key', 'quota_requests_per_minute', 
            'quota_requests_per_day', 'metadata'
        ]
    
    def create(self, validated_data):
        key_value = validated_data.pop('key', None)
        api_key = APIKey.objects.create(**validated_data)
        
        if key_value:
            api_key.set_key(key_value)
        else:
            # Generate a random key if not provided
            import secrets
            key_value = secrets.token_urlsafe(32)
            api_key.set_key(key_value)
            
            
        api_key.prefix_key = key_value[:8]
        
        
        api_key.save()
        
        # Store the raw key temporarily to return in response
        api_key._raw_key = key_value
        return api_key


class IDValidationLogSerializer(serializers.ModelSerializer):
    api_key_name = serializers.CharField(source='api_key.name', read_only=True)
    
    class Meta:
        model = IDValidationLog
        fields = "__all__"
        read_only_fields = ['id', 'created_at']

