#!/bin/bash

# Production run script optimized for Safari compatibility

# Create directories if they don't exist
mkdir -p uploads
mkdir -p /tmp/flask_session
mkdir -p instance

# Set environment variables
export FLASK_ENV=production
export FLASK_APP=app.py

# Clear any cached files
find /tmp/flask_session -type f -delete

# Start Gunicorn with our configuration
gunicorn -c gunicorn_config.py app:app 