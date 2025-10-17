from django.urls import path
from . import views

urlpatterns = [
    path('validate-id/', views.ValidateIDView.as_view(), name='validate-id'),
    path('get_api_key/', views.APIKeyCreateView.as_view(), name='api-key-create'),
]