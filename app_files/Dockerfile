FROM python:3.9-bullseye
RUN pip3 install gunicorn==20.1.0 fastapi==0.75.2 uvicorn==0.17.6 orjson==3.6.8
WORKDIR /SRC
COPY app.py .
COPY gconf.py .
COPY test_json_1MB.json .
ENV GUNICORN_CMD_ARGS="-c gconf.py --worker-tmp-dir /dev/shm --keep-alive=5 --access-logfile=None --reuse-port"
EXPOSE 8000
ENTRYPOINT ["gunicorn", "app:app"]
