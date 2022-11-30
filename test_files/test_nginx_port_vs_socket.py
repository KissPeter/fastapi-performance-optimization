import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase

test_config = [
    {"name": "app_nginx_port", "port": 8008, "baseline": True},
    {"name": "app_nginx_socket", "port": 8009, "baseline": False},
]


class NginxPortvsSocket(TestBase):
    @pytest.mark.nginx_port_vs_socket
    def testnginx_port_vs_socket_sync(self):
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async(self):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_big_json_response(self):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_big_json_response(self):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
