import pytest
from compare_container_performance import CompareContainers


@pytest.mark.middlewares
def test_middlewares():
    test_config = [
        {"name": "base", "port": 8000, "baseline": True},
        {"name": "app_one_base_middleware", "port": 8001, "baseline": False},
        {"name": "app_two_base_middlewares", "port": 8002, "baseline": False},
        {"name": "app_one_starlette_middleware", "port": 8003, "baseline": False},
        {"name": "app_two_starlette_middlewares", "port": 8004, "baseline": False},
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()
