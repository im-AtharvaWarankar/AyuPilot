import os
from celery import Celery
from celery import shared_task

# Set the default Django settings module for the 'celery' program.
ENV = os.getenv('ENV', None)
if ENV is not None and ENV == "prod":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings.dev')

# Create Celery app - broker URL will be loaded from Django settings
app = Celery('tasks')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.py
app.autodiscover_tasks()


# @app.task(bind=True)
@shared_task
def debug_task(self):
    print("done")
    # print(f'Request: {self.request!r}')
