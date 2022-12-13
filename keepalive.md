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


## What is HTTP keepalive?

When your client and server frequently interacts you should always create [persistent HTTP connection](
https://en.wikipedia.org/wiki/HTTP_persistent_connection)

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/HTTP_persistent_connection.svg/600px-HTTP_persistent_connection.svg.png" alt="HTTP Keepalive">


## Measurements

### Synchronous API endpoint with small request / response

#### Nginx - APP connection, but no keepalive


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |          900.11  |          844.94  |          846.34  |       863.797 |
| Time per request [ms] |          111.098 |          118.351 |          118.156 |       115.868 |


#### Nginx - APP connection with keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |          948.01  |          955.86  |          941.48  |       948.45  | 9.8 %                    |
| Time per request [ms] |          105.485 |          104.617 |          106.215 |       105.439 | 10.43 ms                 |


### Observations
* 9,8% improvement only because we reuse our existing connections

### Asynchronous API endpoint with small request / response

#### Nginx - APP connection, but no keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1495.79  |         1406.19  |         1441.5   |     1447.83   |
| Time per request [ms] |           66.854 |           71.114 |           69.372 |       69.1133 |


#### Nginx - APP connection with keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1630.65  |         1680.86  |         1688.54  |     1666.68   | 15.12 %                  |
| Time per request [ms] |           61.325 |           59.493 |           59.223 |       60.0137 | 9.1 ms                   |

### Observations
* 15% improvement by this simple change for async endpoint

## Verdict

* Regardless of the use case sync / async endpoint we can improve our overall performance with this tiny change. 
* If you use HTTPS connection creation has even higher overhead do the the additional SSL layer

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
![](./test.svg)
