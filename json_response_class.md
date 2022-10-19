---
title: Response class
layout: template
filename: json_response_class.md
--- 

# In progress - FastAPI JSON response classes

FastAPI supports custom responses, among them there is support for multiple JSON response implementations. Default is  [JSONResponse](https://fastapi.tiangolo.com/advanced/custom-response/#jsonresponse) but [orjson](https://github.com/ijl/orjson) and [ujson](https://github.com/ultrajson/ultrajson) are available as well.
Both have their [benchmark](https://github.com/ultrajson/ultrajson#benchmarks) / [performance test](https://github.com/ijl/orjson#performance)claiminig they are the fastest, but worths checking for the given usecase.

# JSON response classes test

## Test environment
* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#Test environment) test set was used
* 1MB test json has been generated with strings, floats, ints, arrays, dicts, booleans and dates in it using standard Python json


## Baseline measurement
By default, FastAPI uses the base JSON implementation, let's see the results:

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |              7.4 |             7.41 |             7.67 |        7.4933 |
| Time per request [ms] |          13521.3 |         13487.2  |         13042.8  |    13350.4    |


## Orjson 
>Note: There are some [specialities](https://github.com/ijl/orjson#str) requre attantion

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |             7.87 |             7.98 |             8.11 |        7.9867 | 6.58 %                   |
| Time per request [ms] |         12706.9  |         12523.6  |         12334.4  |    12521.6    | -828.8 ms                 |
> 
## UltraJSON 
>Note: Just like orjson this has its own [speciality](https://github.com/ultrajson/ultrajson#using-an-external-or-system-copy-of-the-double-conversion-library)

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |             8.45 |             7.93 |             8.04 |          8.14 | 8.63 %                   |
| Time per request [ms] |         11839.4  |         12618.1  |         12433.8  |      12297.1  | -1053.34 ms               |
> 
## Verdict
You might want to run an extensive test before / after changing to the other response class to make sure the tiny differences won't cause issues for your client
Having 6-8% gain by simply chaning to other response class seems promissing isn't it? 