import os
import subprocess
import sys

port = os.environ.get("PORT", "8000")

# Strip anything that isn't a number
port = ''.join(filter(str.isdigit, str(port)))
if not port:
    port = "8000"

os.environ["DJANGO_SETTINGS_MODULE"] = "asteroid_tracker.settings"

subprocess.run([
    sys.executable, "-m", "gunicorn",
    "asteroid_tracker.wsgi:application",
    "--bind", f"0.0.0.0:{port}",
    "--workers", "2"
])
