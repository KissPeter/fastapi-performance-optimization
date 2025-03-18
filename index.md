---
title: FastAPI performance optimisation
layout: template
filename: index.md
---

# FastAPI performance tuning

[FastAPI](https://fastapi.tiangolo.com/) is a great, high performance web framework but far from perfect.
This document is intended to provide some tips and ideas to get the most out of it


## [Fastapi Middleware performance tuning](https://kisspeter.github.io/fastapi-performance-optimization/middleware)
## [Fastapi JSON response classes comparison](https://kisspeter.github.io/fastapi-performance-optimization/json_response_class)
## [Gunicorn workers and threads](https://kisspeter.github.io/fastapi-performance-optimization/workers_and_threads)
## [Nginx in front of FastAPI](https://kisspeter.github.io/fastapi-performance-optimization/nginx_port_socket)
## [Connection keepalive](https://kisspeter.github.io/fastapi-performance-optimization/keepalive)

# Stay tuned for new ideas:
## Sync / async API endpoints
## Connection pool size of external resources
## FastAPI application profiling
### Arbitrary place of code
### Profiling middleware

### Test environment
* All the tests were run on  [GitHub Actions](https://github.com/KissPeter/fastapi-performance-optimization/actions/workflows/performance_tuning_measurements.yml)
* Application is built into a container, you can build it like this:
```shell
docker-compose build
```
* The container has two CPU cores allocated in order to preserve resource for the test client:
```Dockerfile
  app:
    container_name: fastapi-performance-optimization
    build:
      context: app_files
      dockerfile: Dockerfile
    image: fastapi-performance-optimization:latest
    cpus: 2
    restart: always
```
* All the tests were run with the same [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) tool configuration available [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/test_files/compare_container_performance.py#L51)
    * ab config: `ab -q -c 100 -n 1000 -T 'application/json' ...`
* All tests were run 3 times and average has been calculated
* Before test run the container has been pre-warmed with small amount of queries, result didn't count in the measurement
* Versions used for these measurements is in the [Dockerfile](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/Dockerfile)
* Interested in re-running the tests in your environment?
```shell
  git clone git@github.com:KissPeter/fastapi-performance-optimization.git
  pip3 install -r test_files/requirements.txt 
  pytest -vv -rP test_files/
```
