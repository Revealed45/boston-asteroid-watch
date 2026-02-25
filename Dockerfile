FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=asteroid_tracker.settings
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--pythonpath", "/app", "asteroid_tracker.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
