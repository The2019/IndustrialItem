# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create upload directory
RUN mkdir -p uploads && chmod 777 uploads

# Create instance directory for SQLite database
RUN mkdir -p instance && chmod 777 instance

# Define volumes
VOLUME /app/uploads

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV HOST=0.0.0.0
ENV PORT=5000
ENV SECRET_KEY=docker-industrial-item-secret

# Expose port
EXPOSE 5000

# Startup script
RUN echo '#!/bin/bash\n\
if [ ! -d "migrations" ]; then\n\
    echo "Initializing database migrations..."\n\
    flask db init\n\
    flask db migrate -m "Initial migration"\n\
    flask db upgrade\n\
else\n\
    echo "Applying database migrations..."\n\
    flask db upgrade\n\
fi\n\
echo "Starting Gunicorn..."\n\
exec gunicorn --bind $HOST:$PORT app:app' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["sh", "/app/start.sh"]