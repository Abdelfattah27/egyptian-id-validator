import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'id_api.settings')

# Create Celery app
app = Celery('id_api')

# Load config from Django settings using CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all Django apps
app.autodiscover_tasks()
