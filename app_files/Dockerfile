FROM python:3.9-bullseye
RUN pip3 install gunicorn==20.1.0 fastapi==0.75.2 uvicorn==0.17.6 orjson==3.6.8
RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y --no-install-recommends nginx-light
WORKDIR /src
COPY nginx.conf /etc/nginx/nginx.conf
COPY app.py .
COPY gconf.py .
COPY test_json_1MB.json .
COPY start_services.sh .
ENV GUNICORN_CMD_ARGS="-c gconf.py --worker-tmp-dir /dev/shm --keep-alive=5 --access-logfile=None --reuse-port"
EXPOSE 8000 8080-8081
ENTRYPOINT /src/start_services.sh
