"""Gunicorn configuration for production container and SPE-01."""
bind = "0.0.0.0:5000"
workers = 2
threads = 2
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
