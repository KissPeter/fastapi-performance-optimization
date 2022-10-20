FROM python:3.10.8-bullseye
RUN pip3 install starlette==0.20.4 gunicorn==20.1.0 fastapi==0.85.1 uvicorn==0.19.0 orjson==3.8.0 ujson==5.5.0
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
