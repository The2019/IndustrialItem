"""
Gunicorn configuration optimized for Safari compatibility
"""

import multiprocessing
import os

# Basic configuration
bind = "0.0.0.0:5000"  # Update with your preferred port
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"  # Asynchronous worker model good for mixed workloads
worker_connections = 1000

# Timeouts - increase these values for Safari
timeout = 120  # Longer timeout to handle Safari's delayed requests
keepalive = 5  # How long to wait for requests on a Keep-Alive connection

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = "info"

# Miscellaneous
daemon = False
reload = False  # Set to True for development

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Advanced settings
forwarded_allow_ips = "*"  # Accept X-Forwarded-For from all IPs
proxy_protocol = False
proxy_allow_ips = "*"

# Additional headers for Safari compatibility
raw_env = [
    "HTTP_CACHE_CONTROL=no-cache, no-store, must-revalidate",
    "HTTP_PRAGMA=no-cache",
    "HTTP_EXPIRES=0"
]

# Set up tmp directory for session files
if not os.path.exists('/tmp/flask_session'):
    os.makedirs('/tmp/flask_session') 