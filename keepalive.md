---
title: Keepalive support
layout: template
filename: keepalive.md
---

# FastAPI connection keepalive

Nobody initializes new connection for each and every query right? :-)
Here is an example how to do it right from the client side:
```python
http_client = urllib3.PoolManager(
            retries=Retry(
                connect=5,
                read=2,
                redirect=5,
                status_forcelist=[429, 500, 501, 502, 503, 504],
                backoff_factor=0.2,
            ),
            timeout=Timeout(connect=5.0, read=10.0),
            num_pools=10,
        )
```
Let's see how to support HTTP connection keep-alive from FastAPI


## What is 

https://en.wikipedia.org/wiki/HTTP_persistent_connection
https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/HTTP_persistent_connection.svg/600px-HTTP_persistent_connection.svg.png

## Measurements

### Synchronous API endpoint with small request / response

#### Nginx - APP via port

#### Nginx - APP via socket

### Observations
* FastAPI queries per second is 1923 which is slightly better than using ports
* API latency improved as well

### Asynchronous API endpoint with 1MB response

#### Nginx - APP via port


#### Nginx - APP via socket



## Verdict


# Pro tip:
* This is a full **Nginx config for FastAPI** with keepalive support:
```shell
user nobody nogroup;
pid /var/run/nginx.pid;
worker_processes 1;  # 1/CPU, to be configured, but Nginx is so powerful, 1 worker can easly handle 1-2k QPS 
events {
  worker_connections 4096; # increase in case of lot of clients
  accept_mutex off; # set to 'on' if nginx worker_processes > 1
  use epoll; # for Linux 2.6+
}

http {
  include mime.types;
  # fallback in case we can't determine a type
  default_type application/octet-stream;
  tcp_nodelay on; # avoid buffer
  access_log off;
  error_log stderr;
  upstream gunicorn {
    # fail_timeout=0 means we always retry an upstream even if it failed
    # to return a good HTTP response
    server unix:/tmp/gunicorn.sock fail_timeout=0;
    keepalive 8;
  }

  server {
    listen                                80;
    server_tokens                         off;
    client_max_body_size                  20M;

    gzip                                  on;
    gzip_proxied                          any;
    gzip_disable                          "msie6";
    gzip_comp_level                       6;
    gzip_min_length                       200; # check your average response size and configure accordingly

    location / {
      proxy_pass                          http://gunicorn;
      proxy_set_header Host               $host;
      proxy_set_header X-Real-IP          $remote_addr;
      proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto  $http_x_forwarded_proto;
      proxy_pass_header                   Server;
      proxy_ignore_client_abort           on;
      proxy_connect_timeout               65s; #  65 here and 60 sec in gconf in order to time out at app side first
      proxy_read_timeout                  65s;
      proxy_send_timeout                  65s;
      proxy_redirect                      off;
      proxy_http_version                  1.1;
      proxy_set_header Connection         "";
      proxy_buffering                     off;
    }
    keepalive_requests                    5000;  
    keepalive_timeout                     120;
    set_real_ip_from                      10.0.0.0/8;
    set_real_ip_from                      172.16.0.0/12;
    set_real_ip_from                      192.168.0.0/16;
    real_ip_header                        X-Forwarded-For;
    real_ip_recursive                     on;
  }
}

```