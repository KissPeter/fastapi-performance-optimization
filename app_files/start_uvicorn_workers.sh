#!/bin/sh
echo "Workers: $WORKERS"
uvicorn --workers="$WORKERS" --host 0.0.0.0 --port 8000 app:app
