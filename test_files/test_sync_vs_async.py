import pytest
from compare_container_performance import CompareContainers

from test_base import TestBase


def _sync_async_cfg(name, port):
    return [
        {"name": f"{name}_sync", "port": port, "baseline": True, "uri": "/sync/items/"},
        {"name": f"{name}_async", "port": port, "baseline": False, "uri": "/async/items/"},
    ]


class TestSyncAsync(TestBase):

    @pytest.mark.sync_async
    def test_gunicorn_w1t0(self):
        p = CompareContainers(_sync_async_cfg("gunicorn_w1t0", 8010))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_gunicorn_w2t0(self):
        p = CompareContainers(_sync_async_cfg("gunicorn_w2t0", 8011))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_gunicorn_w1t1(self):
        p = CompareContainers(_sync_async_cfg("gunicorn_w1t1", 8025))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_gunicorn_w2t1(self):
        p = CompareContainers(_sync_async_cfg("gunicorn_w2t1", 8026))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_gunicorn_w1t2(self):
        p = CompareContainers(_sync_async_cfg("gunicorn_w1t2", 8027))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_gunicorn_w2t2(self):
        p = CompareContainers(_sync_async_cfg("gunicorn_w2t2", 8028))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_uvicorn_single(self):
        p = CompareContainers(_sync_async_cfg("uvicorn_single", 8015))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_uvicorn_workers_w2(self):
        p = CompareContainers(_sync_async_cfg("uvicorn_workers_w2", 8024))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_fastapi_cli_w1(self):
        p = CompareContainers(_sync_async_cfg("fastapi_cli_w1", 8021))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.sync_async
    def test_fastapi_cli_w2(self):
        p = CompareContainers(_sync_async_cfg("fastapi_cli_w2", 8022))
        p.run_test()
        p.sum_container_results()
