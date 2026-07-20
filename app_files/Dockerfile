FROM python:3.14-slim-bookworm
ENV PIP_NO_CACHE_DIR=yes
ENV DEBIAN_FRONTEND=noninteractive
RUN pip3 install fastapi==0.139.2 uvicorn==0.51.0 gunicorn==26.0.0 orjson==3.11.9 ujson==5.13.0 starlette==1.3.1
RUN apt update && apt install -y --no-install-recommends nginx-light
WORKDIR /src
RUN rm -rf /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY app.py .
COPY gconf.py .
COPY test_json_1MB.json .
COPY start_services.sh .
ENV GUNICORN_CMD_ARGS="-c gconf.py --reuse-port"
EXPOSE 8000 8080-8082
ENTRYPOINT /src/start_services.sh
