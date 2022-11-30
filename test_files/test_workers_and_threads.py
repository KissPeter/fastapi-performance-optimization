import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase

test_config = [
    {"name": "app_w1_t1", "port": 8100, "baseline": True},
    {"name": "app_w1_t2", "port": 8101, "baseline": False},
    {"name": "app_w1_t3", "port": 8102, "baseline": False},
    {"name": "app_w1_t4", "port": 8103, "baseline": False},
    {"name": "app_w1_t5", "port": 8104, "baseline": False},
    {"name": "app_w2_t1", "port": 8105, "baseline": False},
    {"name": "app_w2_t2", "port": 8106, "baseline": False},
    {"name": "app_w2_t3", "port": 8107, "baseline": False},
    {"name": "app_w2_t4", "port": 8108, "baseline": False},
    {"name": "app_w2_t5", "port": 8109, "baseline": False},
    {"name": "app_w3_t1", "port": 8110, "baseline": False},
    {"name": "app_w3_t2", "port": 8111, "baseline": False},
    {"name": "app_w3_t3", "port": 8112, "baseline": False},
    {"name": "app_w3_t4", "port": 8113, "baseline": False},
    {"name": "app_w3_t5", "port": 8114, "baseline": False},
    {"name": "app_w4_t1", "port": 8115, "baseline": False},
    {"name": "app_w4_t2", "port": 8116, "baseline": False},
    {"name": "app_w4_t3", "port": 8117, "baseline": False},
    {"name": "app_w4_t4", "port": 8118, "baseline": False},
    {"name": "app_w4_t5", "port": 8119, "baseline": False},
    {"name": "app_w5_t1", "port": 8120, "baseline": False},
    {"name": "app_w5_t2", "port": 8121, "baseline": False},
    {"name": "app_w5_t3", "port": 8122, "baseline": False},
    {"name": "app_w5_t4", "port": 8123, "baseline": False},
    {"name": "app_w5_t5", "port": 8124, "baseline": False},
]


class TestWorkersThreads(TestBase):

    @pytest.mark.workers_and_threads
    def test_workers_and_threads_sync(self):
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.workers_and_threads
    def test_workers_and_threads_async(self):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.workers_and_threads
    def test_workers_and_threads_sync_big_json_response(self):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 500
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.workers_and_threads
    def test_workers_and_threads_async_big_json_response(self):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 500
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
