from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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
        
        1. Create an API key using the `/api/v1/get_api_key/` endpoint
        2. Use the API key in the `X-API-KEY` header for validation requests
        """,
        contact=openapi.Contact(email="abdelfattah.hamdy234@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('validator.urls')), 
    
    # DRF-YASG URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]