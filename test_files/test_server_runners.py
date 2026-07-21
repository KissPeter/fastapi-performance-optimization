import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase

test_config_w1 = [
    {"name": "app_gunicorn_w1_t0", "port": 8010, "baseline": True},
    {"name": "app_uvicorn_w1", "port": 8015, "baseline": False},
    {"name": "app_fastapi_cli_w1", "port": 8021, "baseline": False},
    {"name": "app_uvicorn_workers_w1", "port": 8023, "baseline": False},
]

test_config_w2 = [
    {"name": "app_gunicorn_w2_t0", "port": 8011, "baseline": True},
    {"name": "app_uvicorn_w2", "port": 8016, "baseline": False},
    {"name": "app_fastapi_cli_w2", "port": 8022, "baseline": False},
    {"name": "app_uvicorn_workers_w2", "port": 8024, "baseline": False},
]

test_config_multiprocess_w1 = [
    {"name": "app_uvicorn_multiprocess_w1", "port": 8019, "baseline": True},
]

test_config_multiprocess_w2 = [
    {"name": "app_uvicorn_multiprocess_w2", "port": 8020, "baseline": True},
]


class TestServerRunners(TestBase):

    @pytest.mark.server_runners
    def test_server_runners_sync_w1(self):
        p = CompareContainers(test_config_w1)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_server_runners_async_w1(self):
        async_test_config = []
        for container in test_config_w1.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_server_runners_sync_w2(self):
        p = CompareContainers(test_config_w2)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_server_runners_async_w2(self):
        async_test_config = []
        for container in test_config_w2.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_server_runners_sync_multiprocess_w1(self):
        p = CompareContainers(test_config_multiprocess_w1)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_server_runners_async_multiprocess_w1(self):
        async_test_config = []
        for container in test_config_multiprocess_w1.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_server_runners_sync_multiprocess_w2(self):
        p = CompareContainers(test_config_multiprocess_w2)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.server_runners
    def test_server_runners_async_multiprocess_w2(self):
        async_test_config = []
        for container in test_config_multiprocess_w2.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
