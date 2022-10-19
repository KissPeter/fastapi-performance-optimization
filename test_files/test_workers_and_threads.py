import pytest
from compare_container_performance import CompareContainers

@pytest.mark.workers_and_threads
def test_workers_and_threads():
    test_config = [
        {
            "name": "app_w1_t1",
            "port": 8008,
            "baseline": True,
            "request_count": 500
        },
        {
            "name": "app_w2_t1",
            "port": 8009,
            "baseline": False,
            "request_count": 500
        },
        {
            "name": "app_w3_t1",
            "port": 8010,
            "baseline": False,
            "request_count": 500
        },
        {
            "name": "app_w1_t2",
            "port": 8011,
            "baseline": False,
            "request_count": 500
        },
        {
            "name": "app_w1_t3",
            "port": 8012,
            "baseline": False,
            "request_count": 500
        },
        {
            "name": "app_w2_t2",
            "port": 8013,
            "baseline": False,
            "request_count": 500
        },
        {
            "name": "app_w2_t3",
            "port": 8014,
            "baseline": False,
            "request_count": 500
        },
        {
            "name": "app_w3_t2",
            "port": 8015,
            "baseline": False,
            "request_count": 500
        },
        {
            "name": "app_w3_t3",
            "port": 8016,
            "baseline": False,
            "request_count": 500
        }
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()
