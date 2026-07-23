#!/usr/bin/env bash
echo "Starting Gunicorn with connection pool endpoints"
echo "EXTERNAL_API_HOST=${EXTERNAL_API_HOST:-http://mock-api:8030}"
echo "CONN_POOL_LIMIT=${CONN_POOL_LIMIT:-100}"
echo "CONN_POOL_KEEPALIVE=${CONN_POOL_KEEPALIVE:-20}"
exec gunicorn app:app -c gconf.py --reuse-port -b 0.0.0.0:8000
