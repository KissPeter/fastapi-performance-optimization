import pytest
from compare_container_performance import CompareContainers

@pytest.mark.sync_async
def test_json_sync_vs_async():
    test_config = [
        {
            "name": "app_sync",
            "port": 8000,
            "baseline": True,
            "uri": "/sync/big_json_response/"
        },
        {
            "name": "app_async",
            "port": 8000,
            "baseline": False,
            "uri": "/async/big_json_response/"
        }
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()
