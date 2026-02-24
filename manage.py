#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asteroid_tracker.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

# Railway Nixpacks needs this to detect Django
application = None
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asteroid_tracker.settings')
    from asteroid_tracker.wsgi import application
except Exception:
    pass
