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

### Synchronous API endpoint with small request / response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1375.63  |         1349.77  |         1305.75  |      1343.72  |
| Time per request [ms] |           72.694 |           74.087 |           76.584 |        74.455 |


#### Nginx - APP via socket

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1321.34  |         1357.39  |         1367.66  |     1348.8    | 0.38 %                   |
| Time per request [ms] |           75.681 |           73.671 |           73.118 |       74.1567 | 0.3 ms                   |

### Asynchronous API endpoint with small request / response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1852.67  |         1918.59  |         1817.32  |      1862.86  |
| Time per request [ms] |           53.976 |           52.122 |           55.026 |        53.708 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1943.55  |         1919.56  |         1923.68  |     1928.93   | 3.55 %                   |
| Time per request [ms] |           51.452 |           52.095 |           51.984 |       51.8437 | 1.86 ms                  |

### Observations
* FastAPI queries per second is 1923 which is slightly better than using ports
* API latency improved as well

### Synchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1863.81  |          818.1   |         1980.61  |     1554.17   |
| Time per request [ms] |           53.654 |          122.235 |           50.489 |       75.4593 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1941.33  |         2197.9   |         1884.56  |      2007.93  | 29.2 %                   |
| Time per request [ms] |           51.511 |           45.498 |           53.063 |        50.024 | 25.44 ms                 |

### Observations
* FastAPI requests per second was above 2000 
* **FastAPI laterncy is lower with nginx communication via socket**


### Asynchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |          803.7   |         1927.06  |          967.89  |     1232.88   |
| Time per request [ms] |          124.425 |           51.893 |          103.317 |       93.2117 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1804.45  |         1829.6   |         1799.19  |     1811.08   | 46.9 %                   |
| Time per request [ms] |           55.418 |           54.657 |           55.581 |       55.2187 | 37.99 ms                 |

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
