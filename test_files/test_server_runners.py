import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase

# Runner configs: all 7 runners in one group, Gunicorn w2t0 is always baseline
all_runners_w2 = [
    {"name": "app_gunicorn_w2_t0", "port": 8011, "baseline": True},
    {"name": "app_gunicorn_w2_t1", "port": 8026, "baseline": False},
    {"name": "app_uvicorn_w2", "port": 8016, "baseline": False},
    {"name": "app_uvicorn_workers_w2", "port": 8024, "baseline": False},
    {"name": "app_fastapi_cli_w2", "port": 8022, "baseline": False},
]

# Thread impact: Gunicorn w2t0 vs w1t0 vs w1t1 vs w2t1
gunicorn_threads = [
    {"name": "app_gunicorn_w2_t0", "port": 8011, "baseline": True},
    {"name": "app_gunicorn_w1_t0", "port": 8010, "baseline": False},
    {"name": "app_gunicorn_w1_t1", "port": 8025, "baseline": False},
    {"name": "app_gunicorn_w2_t1", "port": 8026, "baseline": False},
]

# Uvicorn multiprocess (standalone comparison)
uvicorn_multiprocess_w1 = [
    {"name": "app_uvicorn_multiprocess_w1", "port": 8019, "baseline": True},
]

uvicorn_multiprocess_w2 = [
    {"name": "app_uvicorn_multiprocess_w2", "port": 8020, "baseline": True},
]


class TestServerRunners(TestBase):

    @pytest.mark.server_runners
    def test_all_runners_sync(self):
        p = CompareContainers(all_runners_w2)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_all_runners_async(self):
        cfg = [{**c, "uri": "/async/items"} for c in all_runners_w2]
        p = CompareContainers(cfg)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_threads_sync(self):
        p = CompareContainers(gunicorn_threads)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_threads_async(self):
        cfg = [{**c, "uri": "/async/items"} for c in gunicorn_threads]
        p = CompareContainers(cfg)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_uvicorn_multiprocess_sync_w1(self):
        p = CompareContainers(uvicorn_multiprocess_w1)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_uvicorn_multiprocess_async_w1(self):
        cfg = [{**c, "uri": "/async/items"} for c in uvicorn_multiprocess_w1]
        p = CompareContainers(cfg)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_uvicorn_multiprocess_sync_w2(self):
        p = CompareContainers(uvicorn_multiprocess_w2)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_uvicorn_multiprocess_async_w2(self):
        cfg = [{**c, "uri": "/async/items"} for c in uvicorn_multiprocess_w2]
        p = CompareContainers(cfg)
        p.run_test()
        p.sum_container_results()
