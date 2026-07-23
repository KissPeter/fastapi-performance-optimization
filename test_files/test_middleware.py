import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase


def _mw_cfg(runner_name, base_port, uri="/sync/items/"):
    """Pair: baseline (no middleware) vs one FastAPI ProcessTime middleware."""
    return [
        {"name": f"{runner_name}_no_mw", "port": base_port, "baseline": True, "uri": uri},
        {"name": f"{runner_name}_one_mw", "port": base_port + 1, "baseline": False, "uri": uri},
    ]


def _starlette_mw_cfg(runner_name, base_port, uri="/sync/items/"):
    """Pair: baseline (no middleware) vs one Starlette ASGI middleware."""
    return [
        {"name": f"{runner_name}_no_mw", "port": base_port, "baseline": True, "uri": uri},
        {"name": f"{runner_name}_starlette_mw", "port": base_port + 1, "baseline": False, "uri": uri},
    ]


class TestMiddleware(TestBase):

    # --- Gunicorn w1t0 ---
    @pytest.mark.middlewares
    def test_middleware_gunicorn_w1t0(self):
        p = CompareContainers(_mw_cfg("gunicorn_w1t0", 8040))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_gunicorn_w1t0_async(self):
        p = CompareContainers(_mw_cfg("gunicorn_w1t0", 8040, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w2t0 ---
    @pytest.mark.middlewares
    def test_middleware_gunicorn_w2t0(self):
        p = CompareContainers(_mw_cfg("gunicorn_w2t0", 8042))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_gunicorn_w2t0_async(self):
        p = CompareContainers(_mw_cfg("gunicorn_w2t0", 8042, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w1t1 ---
    @pytest.mark.middlewares
    def test_middleware_gunicorn_w1t1(self):
        p = CompareContainers(_mw_cfg("gunicorn_w1t1", 8044))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_gunicorn_w1t1_async(self):
        p = CompareContainers(_mw_cfg("gunicorn_w1t1", 8044, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w2t1 ---
    @pytest.mark.middlewares
    def test_middleware_gunicorn_w2t1(self):
        p = CompareContainers(_mw_cfg("gunicorn_w2t1", 8046))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_gunicorn_w2t1_async(self):
        p = CompareContainers(_mw_cfg("gunicorn_w2t1", 8046, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w1t2 ---
    @pytest.mark.middlewares
    def test_middleware_gunicorn_w1t2(self):
        p = CompareContainers(_mw_cfg("gunicorn_w1t2", 8048))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_gunicorn_w1t2_async(self):
        p = CompareContainers(_mw_cfg("gunicorn_w1t2", 8048, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w2t2 ---
    @pytest.mark.middlewares
    def test_middleware_gunicorn_w2t2(self):
        p = CompareContainers(_mw_cfg("gunicorn_w2t2", 8050))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_gunicorn_w2t2_async(self):
        p = CompareContainers(_mw_cfg("gunicorn_w2t2", 8050, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Uvicorn single ---
    @pytest.mark.middlewares
    def test_middleware_uvicorn_single(self):
        p = CompareContainers(_mw_cfg("uvicorn_single", 8052))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_uvicorn_single_async(self):
        p = CompareContainers(_mw_cfg("uvicorn_single", 8052, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Uvicorn w2 ---
    @pytest.mark.middlewares
    def test_middleware_uvicorn_w2(self):
        p = CompareContainers(_mw_cfg("uvicorn_w2", 8054))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_uvicorn_w2_async(self):
        p = CompareContainers(_mw_cfg("uvicorn_w2", 8054, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- FastAPI CLI w1 ---
    @pytest.mark.middlewares
    def test_middleware_fastapi_cli_w1(self):
        p = CompareContainers(_mw_cfg("fastapi_cli_w1", 8056))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_fastapi_cli_w1_async(self):
        p = CompareContainers(_mw_cfg("fastapi_cli_w1", 8056, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- FastAPI CLI w2 ---
    @pytest.mark.middlewares
    def test_middleware_fastapi_cli_w2(self):
        p = CompareContainers(_mw_cfg("fastapi_cli_w2", 8058))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_middleware_fastapi_cli_w2_async(self):
        p = CompareContainers(_mw_cfg("fastapi_cli_w2", 8058, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    # --- Starlette ASGI middleware comparisons (baseline vs Starlette ASGI) ---
    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w1t0(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w1t0", 8040))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w1t0_async(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w1t0", 8040, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w2t0(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w2t0", 8042))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w2t0_async(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w2t0", 8042, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w1t1(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w1t1", 8044))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w1t1_async(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w1t1", 8044, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w2t1(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w2t1", 8046))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w2t1_async(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w2t1", 8046, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w1t2(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w1t2", 8048))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w1t2_async(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w1t2", 8048, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w2t2(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w2t2", 8050))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_gunicorn_w2t2_async(self):
        p = CompareContainers(_starlette_mw_cfg("gunicorn_w2t2", 8050, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_uvicorn_single(self):
        p = CompareContainers(_starlette_mw_cfg("uvicorn_single", 8052))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_uvicorn_single_async(self):
        p = CompareContainers(_starlette_mw_cfg("uvicorn_single", 8052, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_uvicorn_w2(self):
        p = CompareContainers(_starlette_mw_cfg("uvicorn_w2", 8054))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_uvicorn_w2_async(self):
        p = CompareContainers(_starlette_mw_cfg("uvicorn_w2", 8054, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_fastapi_cli_w1(self):
        p = CompareContainers(_starlette_mw_cfg("fastapi_cli_w1", 8056))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_fastapi_cli_w1_async(self):
        p = CompareContainers(_starlette_mw_cfg("fastapi_cli_w1", 8056, "/async/items/"))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_fastapi_cli_w2(self):
        p = CompareContainers(_starlette_mw_cfg("fastapi_cli_w2", 8058))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.middlewares
    def test_starlette_middleware_fastapi_cli_w2_async(self):
        p = CompareContainers(_starlette_mw_cfg("fastapi_cli_w2", 8058, "/async/items/"))
        p.run_test()
        p.sum_container_results()
