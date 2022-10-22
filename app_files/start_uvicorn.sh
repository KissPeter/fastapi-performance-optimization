echo "Workers: $WORKERS"
uvicorn --workers="$WORKERS" app:app