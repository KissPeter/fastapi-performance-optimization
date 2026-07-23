---
title: Nginx in front of FastAPI
layout: template
filename: nginx_port_socket.md
---

# Nginx in front of FastAPI

Another topic not strictly FastAPI performance optimization, but has a great benefit for the overall service if used. [Nginx](https://www.nginx.com/) is a versatile service, web server, reverse proxy, WAF and so on.
By using in front of the FastAPI application some functions can be decoupled from Gunicorn (request sanity check, timeout handling, backlogging, extra logging in case of error, app latency measurement and so on)
Typical reverse proxy [configuration](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/#passing-a-request-to-a-proxied-server) uses TCP ports between the app and the web server / reverse proxy but it has negative impact on the concurrency as web server - app communication requires a pair of ports allocated for each connection.
There are 65535 port all together, but some [ranges](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Well-known_ports) are not for this purpose so the concurrency is limited, furthermore a port doesn't become free immediately after a connection is closed
The alternative solution which is mentioned in [Uvicorn](https://www.uvicorn.org/deployment/#running-behind-nginx) documentation suggests using sockets which indeed a better solution with some challenges.

## FastAPI as non-root user
If you run your application as non-root user you need to be sure nginx user can read and write the socket.
Fortunately Gunicorn supports [umask](https://docs.gunicorn.org/en/stable/settings.html#umask). 
The most secure option is dedicating a group to this communication, making nginx's and app's user part of that group and limiting the communication to group read and write (umask 717)

## Measurements

> CI run [29770319196](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29770319196) — Python 3.14, Ubuntu latest.

### Synchronous API endpoint with small request / response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1936.66  |         1868.64  |         1915.02  |      1906.77  |
| Time per request [ms] |           51.635 |           53.515 |           52.219 |        52.4563 |


#### Nginx - APP via socket

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         7476.71  |          6645.0  |         7434.42  |      7185.38  | +276.83%                  |
| Time per request [ms] |           13.375 |           15.049 |           13.451 |        13.9583 | 38.5 ms                  |

### Asynchronous API endpoint with small request / response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2780.52  |         2764.32  |         2777.57  |      2774.14  |
| Time per request [ms] |           35.964 |           36.175 |           36.003 |        36.0473 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         7315.44  |         6159.01  |         7347.77  |      6940.74  | +150.19%                  |
| Time per request [ms] |            13.67 |           16.236 |            13.61 |        14.5053 | 21.54 ms                 |

### Observations
* FastAPI queries per second is 1923 which is slightly better than using ports
* API latency improved as well

### Synchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2885.82  |         2758.47  |         2368.75  |      2671.01  |
| Time per request [ms] |           34.652 |           36.252 |           42.216 |        37.7067 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         6454.11  |         6795.05  |         6942.52  |      6730.56  | +151.99%                  |
| Time per request [ms] |           15.494 |           14.717 |           14.404 |        14.8717 | 22.83 ms                 |

### Observations
* FastAPI requests per second was above 2000 
* **FastAPI laterncy is lower with nginx communication via socket**


### Asynchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2713.03  |         2819.41  |         2761.47  |      2764.64  |
| Time per request [ms] |           36.859 |           35.468 |           36.213 |         36.18 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         6855.33  |         6831.25  |         7037.45  |      6908.01  | +149.87%                  |
| Time per request [ms] |           14.587 |           14.639 |            14.21 |        14.4787 | 21.7 ms                  |

## Verdict

Numbers talk by themselves. Almost any case it well worth changing to socket communication
Sample config is [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/nginx.conf#L31)

# Pro tip:
* If you use [nginx-light](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/Dockerfile#L3) instead of nginx in your Docker build you can save ~100MB container image size.
* This is a full **Nginx config for FastAPI**:

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
