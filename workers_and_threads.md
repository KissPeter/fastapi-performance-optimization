---
title: Workers and threads
layout: template
filename: workers_and_threads.md
---

# Gunicorn Workers and Threads

Not strictly FastAPI performance tuning, but performance improvement on runner environment naturally helps for the system. [Gunicorn](https://gunicorn.org/) is one straightforward option to run FastAPI in [production](https://www.uvicorn.org/deployment/#gunicorn) environment
For high performance low latency, cheap, robust and reliable services it is important to get the maximum out of a single computing unit. In this example we will focus on a container with only 2 CPU cores allocated.
This is typically used and GitHub Action container has two CPU cores allocated where [these](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) measurements were executed  

## Gunicorn

[Gunicorn](https://gunicorn.org/) is a mature, fully featured server and process manager.
Gunicorn can manage the processes and threads for us and run [UvicornWorker](https://www.uvicorn.org/deployment/#gunicorn) which can carry FastAPI application

## Uvicorn

Uvicorn can run FastAPI application even with multiple workers, convenient during development thanks to the [reload](https://www.uvicorn.org/deployment/#running-from-the-command-line) capability but even their documentation [suggests](https://www.uvicorn.org/deployment/#gunicorn) to run with Gunicorn in production

## Workers

Workers are pre-forked processes spawn by Gunicorn. Number of workers had to be pre-defined, there is no process pool like e.g: [php-fpm](https://www.digitalocean.com/community/tutorials/php-fpm-nginx#2-configure-php-fpm-pool)
Gunicorn documentation [suggests](https://docs.gunicorn.org/en/latest/design.html?highlight=workers#how-many-workers) using `(2 x $num_cores) + 1` as the number of workers, but also reminds: `Always remember, there is such a thing as too many workers. After a point your worker processes will start thrashing system resources decreasing the throughput of the entire system.` 
We will see it in our measurements

## Threads
Gunicorn can also fork processes for each worker. We know the story around [GIL](https://tenthousandmeters.com/blog/python-behind-the-scenes-13-the-gil-and-its-effects-on-python-multithreading/), but don't judge, measure
This is how it looks like in action:

<img src="https://miro.medium.com/max/1400/1*IWcHIxgsf71p19rbJrfZmA.jpeg" alt="Gunicorn workers and threads">

> > Source: https://medium.com/@nhudinhtuan/gunicorn-worker-types-practice-advice-for-better-performance-7a299bb8f929

## Measurements

1-5 Workers and 1-5 threads were measured, this together is 25 measurements in the [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) way. There would be place for further measurements E.g measuring with 0 threads or raising the counts to even higher and so on. Also note that some values are not fitting due to intermittent performance issue during measurement.
Request is the same in allcases the difference is the size of the response (few bytes vs 1MB)

### Synchronous API endpoint with small request / response

<img src="https://kisspeter.github.io/fastapi-performance-optimization/images/sync_small_response.svg" alt="Measurement results">

#### Observation
2 worker configuration outperforms all others, thread number seems no significant impact

### Asynchronous API endpoint with small request / response

<img src="https://kisspeter.github.io/fastapi-performance-optimization/images/async_small_response.svg" alt="Measurement results">

#### Observation 

Result is not as clear as for synchronous endpoint, 3 workers and 1 thread seems the winner

### Synchronous API endpoint with 1MB response

<img src="https://kisspeter.github.io/fastapi-performance-optimization/images/sync_big_response.svg" alt="Measurement results">

#### Observation

Similar to small responses 2 workers performing the best

### Asynchronous API endpoint with 1MB response

<img src="https://kisspeter.github.io/fastapi-performance-optimization/images/async_big_response.svg" alt="Measurement results">

#### Observation

* For some strange reason 2 and 5 threads working the best at each worker count, but best results are at 2 and 3 workers
* **FastAPI latency was lowest** at 3 workers and 2 threads

## Verdict

No clear winner, but suggestion of Gunicorn documentation was right, `there is such a thing as too many workers`.
It is highly recommended making a measurement like this and select the best combination for the given usecase. Feel free to reuse the [test code](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/test_files/test_workers_and_threads.py)

# Gunicorn vs Uvicorn

You may ask why use Gunicorn instead of Uvicorn for application where latency is not that critical and high load is not expected?
Let's see:

## 1 Worker setup

### Gunicorn
1 worker, 0 thread

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1182.34  |         1202.61  |         1181.1   |     1188.68   |
| Time per request [ms] |           84.578 |           83.153 |           84.667 |       84.1327 |

### Uvicorn

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1116.09  |          1139.08 |         1151.8   |     1135.66   | -4.46 %                  |
| Time per request [ms] |           89.598 |            87.79 |           86.821 |       88.0697 | -3.94 ms                 |

## 2 Worker setup

### Gunicorn
2 workers, 0 threads

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         1658.62  |         1518.47  |         1697.9   |      1625     |
| Time per request [ms] |           60.291 |           65.856 |           58.896 |        61.681 |


### Uvicorn


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         1518.02  |         1554.76  |         1564.23  |     1545.67   | -4.88 %                  |
| Time per request [ms] |           65.875 |           64.318 |           63.929 |       64.7073 | -3.03 ms                 |

## Observation

Not a big difference, but Gunicorn performs a bit better however requires extra package installed, a bit more configuration, etc.
