echo "Workers: $WORKERS"
uvicorn --workers="$WORKERS" --host 0.0.0.0 app:app