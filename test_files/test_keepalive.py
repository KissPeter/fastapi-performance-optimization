import pytest

from compare_container_performance import CompareContainers

test_config = [
    {"name": "app_nginx_socket", "port": 8009, "baseline": True, "keep_alive": False},
    {"name": "app_nginx_socket_keepalive", "port": 8017, "baseline": False, "keep_alive": True},
]


@pytest.mark.nginx_socker_keepalive
def testnginx_socker_keepalive_sync():
    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()


@pytest.mark.nginx_socker_keepalive
def test_nginx_socker_keepalive_async():
    async_test_config = []
    for container in test_config.copy():
        container["uri"] = "/async/items"
        async_test_config.append(container)
    print(async_test_config)
    p = CompareContainers(async_test_config)
    p.run_test()
    p.sum_container_results()


@pytest.mark.nginx_socker_keepalive
def test_nginx_socker_keepalive_sync_big_json_response():
    async_test_config = []
    for container in test_config.copy():
        container["uri"] = "/sync/big_json_response"
        container["request_count"] = 1000
        async_test_config.append(container)
    print(async_test_config)
    p = CompareContainers(async_test_config)
    p.run_test()
    p.sum_container_results()


@pytest.mark.nginx_socker_keepalive
def test_nginx_socker_keepalive_async_big_json_response():
    async_test_config = []
    for container in test_config.copy():
        container["uri"] = "/async/big_json_response"
        container["request_count"] = 1000
        async_test_config.append(container)
    print(async_test_config)
    p = CompareContainers(async_test_config)
    p.run_test()
    p.sum_container_results()
