import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase


def _json_cfg(runner_name, base_port, uri="/sync/big_json_response/"):
    """Three response classes: default JSONResponse (baseline), ORJSONResponse, UJSONResponse."""
    return [
        {"name": f"{runner_name}_json_default", "port": base_port, "baseline": True, "uri": uri, "request_count": 500},
        {"name": f"{runner_name}_json_orjson", "port": base_port + 1, "baseline": False, "uri": uri, "request_count": 500},
        {"name": f"{runner_name}_json_ujson", "port": base_port + 2, "baseline": False, "uri": uri, "request_count": 500},
    ]


class TestJSONClasses(TestBase):

    # --- Gunicorn w2t0 ---
    @pytest.mark.json_classes
    def test_json_response_classes_gunicorn_w2t0(self):
        p = CompareContainers(_json_cfg("gunicorn_w2t0", 8060))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.json_classes
    def test_json_response_classes_gunicorn_w2t0_async(self):
        p = CompareContainers(_json_cfg("gunicorn_w2t0", 8060, "/async/big_json_response/"))
        p.run_test()
        p.sum_container_results()

    # --- Uvicorn single ---
    @pytest.mark.json_classes
    def test_json_response_classes_uvicorn_single(self):
        p = CompareContainers(_json_cfg("uvicorn_single", 8063))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.json_classes
    def test_json_response_classes_uvicorn_single_async(self):
        p = CompareContainers(_json_cfg("uvicorn_single", 8063, "/async/big_json_response/"))
        p.run_test()
        p.sum_container_results()

    # --- FastAPI CLI w1 ---
    @pytest.mark.json_classes
    def test_json_response_classes_fastapi_cli_w1(self):
        p = CompareContainers(_json_cfg("fastapi_cli_w1", 8066))
        p.run_test()
        p.sum_container_results()

    @pytest.mark.json_classes
    def test_json_response_classes_fastapi_cli_w1_async(self):
        p = CompareContainers(_json_cfg("fastapi_cli_w1", 8066, "/async/big_json_response/"))
        p.run_test()
        p.sum_container_results()
