#!/usr/bin/env bash
exec uvicorn mock_api:app --host 0.0.0.0 --port 8030
