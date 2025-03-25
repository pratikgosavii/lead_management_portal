"""
WSGI config for lead_management project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lead_management.settings')

application = get_wsgi_application()
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lead_management.settings')
application = get_wsgi_application()

# For WSGI servers
app = application
