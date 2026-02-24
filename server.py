import os
import django
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asteroid_tracker.settings")
django.setup()

port = os.environ.get("PORT", "8000").strip()
try:
    port = int(port)
except ValueError:
    port = 8000

call_command("runserver", f"0.0.0.0:{port}", "--noreload")
