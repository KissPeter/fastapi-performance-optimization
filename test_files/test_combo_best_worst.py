import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase

best_config = [
    {"name": "best_async_orjson", "port": 8130, "baseline": False},
]
worst_config = [
    {"name": "worst_sync_json", "port": 8131, "baseline": True},
]


class TestComboBestWorst(TestBase):

    @pytest.mark.combo
    def test_combo_sync_big_json_best_vs_worst(self):
        test_config = []
        for container in worst_config.copy():
            container["uri"] = "/sync/big_json_response/"
            container["request_count"] = 500
            test_config.append(container)
        for container in best_config.copy():
            container["uri"] = "/sync/big_json_response/"
            container["request_count"] = 500
            test_config.append(container)
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.combo
    def test_combo_async_big_json_best_vs_worst(self):
        test_config = []
        for container in worst_config.copy():
            container["uri"] = "/async/big_json_response/"
            container["request_count"] = 500
            test_config.append(container)
        for container in best_config.copy():
            container["uri"] = "/async/big_json_response/"
            container["request_count"] = 500
            test_config.append(container)
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.combo
    def test_combo_sync_small_best_vs_worst(self):
        test_config = []
        for container in worst_config.copy():
            container["uri"] = "/sync/items/"
            test_config.append(container)
        for container in best_config.copy():
            container["uri"] = "/sync/items/"
            test_config.append(container)
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.combo
    def test_combo_async_small_best_vs_worst(self):
        test_config = []
        for container in worst_config.copy():
            container["uri"] = "/async/items/"
            test_config.append(container)
        for container in best_config.copy():
            container["uri"] = "/async/items/"
            test_config.append(container)
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()
