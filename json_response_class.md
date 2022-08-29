---
title: Response class
layout: template
filename: json_response_class.md
--- 

# FastAPI JSON response classes

FastAPI supports custom responses, among them there is support for multiple JSON response implementations. Default is  [JSONResponse](https://fastapi.tiangolo.com/advanced/custom-response/#jsonresponse) but [orjson](https://github.com/ijl/orjson) and [ujson](https://github.com/ultrajson/ultrajson) are available as well.
Both have their [benchmark](https://github.com/ultrajson/ultrajson#benchmarks) / [performance test](https://github.com/ijl/orjson#performance)claiminig they are the fastest, but worths checking for the given usecase.

# JSON response classes test

## Test environment
* All the tests were run on a machine with i5-2520M CPU
* Application is built into a container:
```shell
docker build -f Dockerfile -t fastapi_test:latest .
```
* The container has two CPU cores allocated in order to preserve resource for the test client:
```shell
docker run -p 127.0.0.1:8000:8000 --cpus=1 -it fastapi_test:latest
```
* All the tests were run with the same [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) tool configuration available [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/test_files/run_ab.sh)
* 1MB test json has been generated with strings, floats, ints, arrays, dicts, booleans and dates in it using standard Python json
* Before test run the container has been pre-warmed
