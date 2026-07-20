#!/bin/sh
echo "Workers: $WORKERS"
fastapi run --host 0.0.0.0 --port 8000 --workers "$WORKERS" --app app
