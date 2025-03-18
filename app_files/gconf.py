import os

#
if os.getenv('SOCKET'):
    if os.getenv('KEEPALIVE'):
        bind = 'unix:/tmp/gunicorn_keepalive.sock'
    else:
        bind = 'unix:/tmp/gunicorn.sock'
else:
    bind = '0.0.0.0:8000'

workers = os.getenv('WORKERS', 2)
threads = os.getenv('THREADS', 1)
# backlog - The number of pending connections.
backlog = 64
# Workers silent for more than this many seconds are killed and restarted.
timeout = 60
# Timeout for graceful workers restart.
graceful_timeout = 30
# The number of seconds to wait for requests on a Keep-Alive connection.
keepalive = 5
# The maximum number of requests a worker will process before restarting.
max_requests = 0
max_requests_jitter = 0
worker_class = 'uvicorn.workers.UvicornWorker'
worker_tmp_dir = '/dev/shm'

if os.getenv('KEEPALIVE'):
    # Workers silent for more than this many seconds are killed and restarted.
    timeout = 60
    # Timeout for graceful workers restart.
    graceful_timeout = 30
    # The number of seconds to wait for requests on a Keep-Alive connection.
    keepalive = 120
    # The maximum number of requests a worker will process before restarting.
    max_requests = 0
    max_requests_jitter = 0
