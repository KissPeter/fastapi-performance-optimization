---
title: Response class
layout: template
filename: json_response_class.md
--- 

# FastAPI JSON response classes

FastAPI supports custom [response classes](https://fastapi.tiangolo.com/advanced/custom-response/#jsonresponse), among them there is support for multiple JSON response implementations. Default is  [JSONResponse](https://fastapi.tiangolo.com/advanced/custom-response/#jsonresponse) but [orjson](https://github.com/ijl/orjson) and [ujson](https://github.com/ultrajson/ultrajson) are available as well.
Both have their [benchmark](https://github.com/ultrajson/ultrajson#benchmarks) / [performance test](https://github.com/ijl/orjson#performance)claiminig they are the fastest, but worths checking for the given usecase.

> Note: FastAPI supports different response classes, but request parsing is done by Starlette where you [don't have control](https://github.com/encode/starlette/blob/master/starlette/requests.py#L242) over which JSON implementation to be used

# JSON response classes test

> CI run [29770319196](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29770319196) — Python 3.14, Ubuntu latest.

## Test environment
* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) test set was used
* 1MB test json has been generated with strings, floats, ints, arrays, dicts, booleans and dates in it using standard Python json


## Baseline measurement
By default, FastAPI uses the base JSON implementation, let's see the results:

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |             19.51 |             19.64 |             19.62 |        19.59 |
| Time per request [ms] |          5125.68 |          5091.15 |          5096.26 |    5104.36   |


## Orjson 
>Note: There are some [specialities](https://github.com/ijl/orjson#str) requre attention

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |             21.29 |             20.2 |             21.62 |      21.0367 | +7.38 %                  |
| Time per request [ms] |          4696.16 |          4951.17 |          4624.58 |     4757.3   | 347.06 ms                |
 
## UltraJSON 
>Note: Just like orjson this has its own [speciality](https://github.com/ultrajson/ultrajson#using-an-external-or-system-copy-of-the-double-conversion-library)

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |             19.52 |             19.57 |             19.43 |      19.5067 | -0.43 %                  |
| Time per request [ms] |          5122.47 |          5108.58 |          5145.63 |     5125.56  | -21.2 ms                 |
 
# Cross-runner JSON response class comparison

> CI run [29858316413](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29858316413) — Python 3.14, Ubuntu latest.

The same JSON response class comparison was repeated across 3 key server runners (Gunicorn 2 workers 0 threads, Uvicorn single-process, FastAPI CLI 1 worker) to see whether the choice of response class interacts with the runner type.

### Sync endpoint (`/sync/big_json_response/` — 1MB payload)

| Runner | JSONResponse (baseline) | ORJSONResponse | UJSONResponse |
|--------|------------------------|----------------|---------------|
| Gunicorn (2 workers, 0 threads) | 17.65 RPS | 18.44 RPS (+4.46%) | 17.26 RPS (-2.19%) |
| Uvicorn single | 9.15 RPS | 10.36 RPS (+13.26%) | 9.40 RPS (+2.81%) |
| FastAPI CLI (1 worker) | 9.45 RPS | 10.66 RPS (+12.81%) | 9.84 RPS (+4.13%) |

### Async endpoint (`/async/big_json_response/` — 1MB payload)

| Runner | JSONResponse (baseline) | ORJSONResponse | UJSONResponse |
|--------|------------------------|----------------|---------------|
| Gunicorn (2 workers, 0 threads) | 17.06 RPS | 18.15 RPS (+6.39%) | 17.30 RPS (+1.41%) |
| Uvicorn single | 9.16 RPS | 10.38 RPS (+13.35%) | 9.29 RPS (+1.42%) |
| FastAPI CLI (1 worker) | 9.48 RPS | 10.58 RPS (+11.64%) | 9.74 RPS (+2.74%) |

### Observations
* **ORJSONResponse consistently outperforms** the default JSONResponse across all runners (+4% to +13%)
* **UJSONResponse shows marginal improvement** (+1% to +4%), less impactful than ORJSON
* The **relative gain of ORJSON is larger on Uvicorn and FastAPI CLI** (~13%) compared to Gunicorn (~5%), suggesting ORJSON's serialization advantage is more visible when the server framework has less overhead
* Gunicorn with 2 workers achieves higher absolute throughput (~17-18 RPS) than Uvicorn/FastAPI CLI single-process (~9-10 RPS) for large JSON serialization, as it can parallelize across workers

# Verdict

> **Individual impact: +4-13% throughput** by switching from JSONResponse to ORJSONResponse.

* You might want to run an extensive test before / after changing to the other response class to make sure the tiny differences won't cause issues for your client
* Having some gain by simply changing to other response class seems promissing isn't it?
* **ORJSONResponse is the recommended choice** — it provides consistent +5-13% improvement across all runners with minimal code change
* The response class benefit is **runner-independent** — ORJSON wins everywhere, but the margin varies


Please note that you can have different JSON response class for each API endpoint as shown in the FastAPI [docs](https://fastapi.tiangolo.com/advanced/custom-response/#ujsonresponse):
    
```python
from fastapi import FastAPI
from fastapi.responses import UJSONResponse

app = FastAPI()


@app.get("/items/", response_class=UJSONResponse)
async def read_items():
    return [{"item_id": "Foo"}]
```