"""
WSGI config for task_api project.

WSGI is the bridge between the web server (Gunicorn)
and Django. Used in production deployment.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_api.settings')

application = get_wsgi_application()
