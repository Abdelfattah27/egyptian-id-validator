from django.urls import path
from . import views

urlpatterns = [
    path('validate/', views.ValidateIDView.as_view(), name='validate-id'),
    path('api-keys/', views.APIKeyCreateView.as_view(), name='api-key-create'),
    path('logs/', views.IDValidationLogAPIView.as_view(), name='logs'),
]