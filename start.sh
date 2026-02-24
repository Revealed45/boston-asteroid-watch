#!/bin/bash
exec gunicorn asteroid_tracker.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2
