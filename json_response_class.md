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
* Test was repeated on synchronous and asynchronous endpoints

## Baseline measurement
By default FastAPI uses the base JSON implementation, let's see the results:

## Orjson measurement
>Note:

## Urjson measurement
>Note:

## Verdict
You might want to run an extensive test before / after changing to the other response class to make sure the tiny differences won't cause issues for your client
