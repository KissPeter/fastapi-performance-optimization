import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase

test_config_w1 = [
    {"name": "app_gunicorn_w1_t0", "port": 8010, "baseline": True},
    {"name": "app_uvicorn_w1", "port": 8015, "baseline": False},
]

test_config_w2 = [
    {"name": "app_gunicorn_w2_t0", "port": 8011, "baseline": True},
    {"name": "app_uvicorn_w2", "port": 8016, "baseline": False},
]


class TestGunicornUvicorn(TestBase):

    @pytest.mark.gunicorn_vs_uvicorn
    def test_gunicorn_vs_uvicorn_sync_w1(self):
        p = CompareContainers(test_config_w1)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.gunicorn_vs_uvicorn
    def test_gunicorn_vs_uvicorn_async_w1(self):
        async_test_config = []
        for container in test_config_w1.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.gunicorn_vs_uvicorn
    def test_gunicorn_vs_uvicorn_sync_w2(self):
        p = CompareContainers(test_config_w2)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.gunicorn_vs_uvicorn
    def test_gunicorn_vs_uvicorn_async_w2(self):
        async_test_config = []
        for container in test_config_w2.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
