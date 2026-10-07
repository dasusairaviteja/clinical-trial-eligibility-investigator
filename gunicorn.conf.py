"""Single-process deployment; scale only after adding shared storage/limits."""
bind = "0.0.0.0:8000"
workers = 1
worker_class = "gthread"
threads = 4
timeout = 180
graceful_timeout = 190
keepalive = 2
limit_request_line = 2048
limit_request_fields = 40
limit_request_field_size = 4096
accesslog = None
errorlog = "-"
capture_output = True
