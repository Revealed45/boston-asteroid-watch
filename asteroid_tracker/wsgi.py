import os
import sys

# Add /app to Python path so asteroid_tracker module can be found
sys.path.insert(0, '/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asteroid_tracker.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
