# tasks.py
from celery import shared_task
from .models import IDValidationLog

@shared_task(bind=True, max_retries=3)
def log_validation_task(self, api_key_id, endpoint, method, status_code, response_time, 
                       ip_address, user_agent, request_data, response_data):
    """
    Celery task to log validation results to database
    """
    try:
        IDValidationLog.objects.create(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data,
            response_data=response_data
        )
    except Exception as exc:
        # Retry the task after 30 seconds if it fails
        raise self.retry(countdown=30, exc=exc)