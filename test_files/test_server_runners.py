import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase


def _cfg(name, port, uri="/sync/items/"):
    return [{"name": name, "port": port, "baseline": True, "uri": uri}]


class TestServerRunners(TestBase):

    # --- Gunicorn 1w 0t ---
    @pytest.mark.server_runners
    def test_gunicorn_w1t0_sync(self):
        p = CompareContainers(_cfg("gunicorn_w1t0", 8010))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_w1t0_async(self):
        p = CompareContainers(_cfg("gunicorn_w1t0", 8010, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn 2w 0t ---
    @pytest.mark.server_runners
    def test_gunicorn_w2t0_sync(self):
        p = CompareContainers(_cfg("gunicorn_w2t0", 8011))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_w2t0_async(self):
        p = CompareContainers(_cfg("gunicorn_w2t0", 8011, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn 1w 1t ---
    @pytest.mark.server_runners
    def test_gunicorn_w1t1_sync(self):
        p = CompareContainers(_cfg("gunicorn_w1t1", 8025))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_w1t1_async(self):
        p = CompareContainers(_cfg("gunicorn_w1t1", 8025, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn 2w 1t ---
    @pytest.mark.server_runners
    def test_gunicorn_w2t1_sync(self):
        p = CompareContainers(_cfg("gunicorn_w2t1", 8026))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_w2t1_async(self):
        p = CompareContainers(_cfg("gunicorn_w2t1", 8026, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn 1w 2t ---
    @pytest.mark.server_runners
    def test_gunicorn_w1t2_sync(self):
        p = CompareContainers(_cfg("gunicorn_w1t2", 8027))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_w1t2_async(self):
        p = CompareContainers(_cfg("gunicorn_w1t2", 8027, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn 2w 2t ---
    @pytest.mark.server_runners
    def test_gunicorn_w2t2_sync(self):
        p = CompareContainers(_cfg("gunicorn_w2t2", 8028))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_gunicorn_w2t2_async(self):
        p = CompareContainers(_cfg("gunicorn_w2t2", 8028, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Uvicorn single-process ---
    @pytest.mark.server_runners
    def test_uvicorn_single_sync(self):
        p = CompareContainers(_cfg("uvicorn_single", 8015))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_uvicorn_single_async(self):
        p = CompareContainers(_cfg("uvicorn_single", 8015, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Uvicorn --workers 2 ---
    @pytest.mark.server_runners
    def test_uvicorn_workers_w2_sync(self):
        p = CompareContainers(_cfg("uvicorn_workers_w2", 8024))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_uvicorn_workers_w2_async(self):
        p = CompareContainers(_cfg("uvicorn_workers_w2", 8024, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- FastAPI CLI 1w ---
    @pytest.mark.server_runners
    def test_fastapi_cli_w1_sync(self):
        p = CompareContainers(_cfg("fastapi_cli_w1", 8021))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_fastapi_cli_w1_async(self):
        p = CompareContainers(_cfg("fastapi_cli_w1", 8021, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- FastAPI CLI 2w ---
    @pytest.mark.server_runners
    def test_fastapi_cli_w2_sync(self):
        p = CompareContainers(_cfg("fastapi_cli_w2", 8022))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_fastapi_cli_w2_async(self):
        p = CompareContainers(_cfg("fastapi_cli_w2", 8022, "/async/items/"))
        p.run_test()
        p.sum_container_results()
