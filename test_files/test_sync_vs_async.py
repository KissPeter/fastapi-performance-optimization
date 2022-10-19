import pytest
from compare_container_performance import CompareContainers

@pytest.mark.sync_async
def test_json_sync_vs_async_small_response():
    test_config = [
        {
            "name": "app_sync_small_response",
            "port": 8000,
            "baseline": True,
            "uri": "/sync/items/"
        },
        {
            "name": "app_async_small_response",
            "port": 8000,
            "baseline": False,
            "uri": "/async/items/"
        }
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()

@pytest.mark.sync_async
def test_json_sync_vs_async_big_response():
    test_config = [
        {
            "name": "app_sync_big_response",
            "port": 8000,
            "baseline": True,
            "uri": "/sync/big_json_response/",
            "request_count": 500
        },
        {
            "name": "app_async_big_response",
            "port": 8000,
            "baseline": False,
            "uri": "/async/big_json_response/",
            "request_count": 500
        }
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()