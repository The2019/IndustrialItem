# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose port 5000
EXPOSE 5000

# Create a startup script that handles both fresh and existing deployments
RUN echo '#!/bin/bash\n\
if [ ! -d "migrations" ]; then\n\
    echo "Migrations directory not found. Initializing..."\n\
    flask db init\n\
    flask db migrate -m "Initial migration"\n\
fi\n\
flask db upgrade\n\
gunicorn --bind 0.0.0.0:5000 app:app' > /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"] 