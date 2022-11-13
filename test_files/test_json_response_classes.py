import pytest
from compare_container_performance import CompareContainers


@pytest.mark.json_classes
def test_json_response_classes():
    test_config = [
        {
            "name": "app_default_json_response_class",
            "port": 8005,
            "baseline": True,
            "uri": "/sync/big_json_response/",
            "request_count": 500,
        },
        {
            "name": "app_ojson_response_class",
            "port": 8006,
            "baseline": False,
            "uri": "/sync/big_json_response/",
            "request_count": 500,
        },
        {
            "name": "app_ujson_response_class",
            "port": 8007,
            "baseline": False,
            "uri": "/sync/big_json_response/",
            "request_count": 500,
        },
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()
