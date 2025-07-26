# Gunicorn configuration file for MT5 Trading Server

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_access.log")
errorlog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_error.log")
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "mt5_trading_server"

# Daemon mode
daemon = False

# PID file
pidfile = os.path.join(os.path.dirname(__file__), "logs", "gunicorn.pid")

# User and group (Unix only)
# user = "www-data"
# group = "www-data"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
