import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase

test_config = [
    {"name": "app_nginx_port", "port": 8008, "baseline": True},
    {"name": "app_nginx_socket", "port": 8009, "baseline": False},
]

test_config_gunicorn_w1t0 = [
    {"name": "nginx_gunicorn_w1t0_port", "port": 8140, "baseline": True},
    {"name": "nginx_gunicorn_w1t0_socket", "port": 8141, "baseline": False},
]

test_config_gunicorn_w2t0 = [
    {"name": "nginx_gunicorn_w2t0_port", "port": 8142, "baseline": True},
    {"name": "nginx_gunicorn_w2t0_socket", "port": 8143, "baseline": False},
]

test_config_gunicorn_w1t1 = [
    {"name": "nginx_gunicorn_w1t1_port", "port": 8144, "baseline": True},
    {"name": "nginx_gunicorn_w1t1_socket", "port": 8145, "baseline": False},
]

test_config_gunicorn_w2t1 = [
    {"name": "nginx_gunicorn_w2t1_port", "port": 8146, "baseline": True},
    {"name": "nginx_gunicorn_w2t1_socket", "port": 8147, "baseline": False},
]

test_config_gunicorn_w1t2 = [
    {"name": "nginx_gunicorn_w1t2_port", "port": 8148, "baseline": True},
    {"name": "nginx_gunicorn_w1t2_socket", "port": 8149, "baseline": False},
]

test_config_gunicorn_w2t2 = [
    {"name": "nginx_gunicorn_w2t2_port", "port": 8150, "baseline": True},
    {"name": "nginx_gunicorn_w2t2_socket", "port": 8151, "baseline": False},
]


class TestNginxPortvsSocket(TestBase):

    # --- Gunicorn w3t1 (default) ---
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

    # --- Gunicorn w1t0 ---
    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_gunicorn_w1t0(self):
        p = CompareContainers(test_config_gunicorn_w1t0)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_gunicorn_w1t0(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t0.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_big_json_response_gunicorn_w1t0(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t0.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_big_json_response_gunicorn_w1t0(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t0.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w2t0 ---
    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_gunicorn_w2t0(self):
        p = CompareContainers(test_config_gunicorn_w2t0)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_gunicorn_w2t0(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t0.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_big_json_response_gunicorn_w2t0(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t0.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_big_json_response_gunicorn_w2t0(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t0.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w1t1 ---
    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_gunicorn_w1t1(self):
        p = CompareContainers(test_config_gunicorn_w1t1)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_gunicorn_w1t1(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t1.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_big_json_response_gunicorn_w1t1(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t1.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_big_json_response_gunicorn_w1t1(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t1.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w2t1 ---
    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_gunicorn_w2t1(self):
        p = CompareContainers(test_config_gunicorn_w2t1)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_gunicorn_w2t1(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t1.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_big_json_response_gunicorn_w2t1(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t1.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_big_json_response_gunicorn_w2t1(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t1.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w1t2 ---
    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_gunicorn_w1t2(self):
        p = CompareContainers(test_config_gunicorn_w1t2)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_gunicorn_w1t2(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t2.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_big_json_response_gunicorn_w1t2(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t2.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_big_json_response_gunicorn_w1t2(self):
        async_test_config = []
        for container in test_config_gunicorn_w1t2.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    # --- Gunicorn w2t2 ---
    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_gunicorn_w2t2(self):
        p = CompareContainers(test_config_gunicorn_w2t2)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_gunicorn_w2t2(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t2.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_sync_big_json_response_gunicorn_w2t2(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t2.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.nginx_port_vs_socket
    def test_nginx_port_vs_socket_async_big_json_response_gunicorn_w2t2(self):
        async_test_config = []
        for container in test_config_gunicorn_w2t2.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 1000
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
