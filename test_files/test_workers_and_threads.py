import pytest

from compare_container_performance import CompareContainers, get_field_from_container_name
from chart import Bar
from test_base import TestBase

test_config_t1 = [{"name": "app_w1_t1", "port": 8100, "baseline": True},
    {"name": "app_w2_t1", "port": 8105, "baseline": False}, {"name": "app_w3_t1", "port": 8110, "baseline": False},
    {"name": "app_w4_t1", "port": 8115, "baseline": False}, {"name": "app_w5_t1", "port": 8120, "baseline": False}, ]
test_config_t2 = [{"name": "app_w1_t2", "port": 8101, "baseline": True},
    {"name": "app_w2_t2", "port": 8106, "baseline": False}, {"name": "app_w3_t2", "port": 8111, "baseline": False},
    {"name": "app_w4_t2", "port": 8116, "baseline": False}, {"name": "app_w5_t2", "port": 8121, "baseline": False}, ]
test_config_t3 = [{"name": "app_w1_t3", "port": 8102, "baseline": True},
    {"name": "app_w2_t3", "port": 8107, "baseline": False}, {"name": "app_w3_t3", "port": 8112, "baseline": False},
    {"name": "app_w4_t3", "port": 8117, "baseline": False}, {"name": "app_w5_t3", "port": 8122, "baseline": False}, ]
test_config_t4 = [{"name": "app_w1_t4", "port": 8103, "baseline": True},
    {"name": "app_w2_t4", "port": 8108, "baseline": False}, {"name": "app_w3_t4", "port": 8113, "baseline": False},
    {"name": "app_w4_t4", "port": 8118, "baseline": False}, {"name": "app_w5_t4", "port": 8123, "baseline": False}, ]
test_config_t5 = [{"name": "app_w1_t5", "port": 8104, "baseline": True},
    {"name": "app_w2_t5", "port": 8109, "baseline": False}, {"name": "app_w3_t5", "port": 8114, "baseline": False},
    {"name": "app_w4_t5", "port": 8119, "baseline": False}, {"name": "app_w5_t5", "port": 8124, "baseline": False}, ]


def generate_chart(t, values, fields):
    no_of_threads = get_field_from_container_name(t[0]['name'], 2).replace('t', '')
    c = Bar(fields=fields,
            values=[values],
            titles=[f"{no_of_threads} Gunicorn thread"],
            graph_title=f"{no_of_threads} thread container RPS")
    c.save(filename=get_field_from_container_name(t[0]['name'], 2))

# fields = ['w1', 'w2', 'w3', 'w4', 'w5']
# values = [[727.5733, 1092.9267, 1077.9467, 1051.2367, 987.6333]]
# titles = ['1 Gunicorn thread']
# graph_title = '1 Threads container RPS'
# c = Bar(fields=fields, values=values, titles=titles, graph_title=graph_title)
# c.save('asd')


class TestWorkersThreads(TestBase):

    @pytest.mark.parametrize("test_config",
                             [test_config_t1, test_config_t2, test_config_t3, test_config_t4, test_config_t5])
    @pytest.mark.workers_and_threads
    def test_workers_and_threads_sync(self, test_config):
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()
        generate_chart(t=test_config, values=p.chart_values, fields=p.chart_titles)

    @pytest.mark.parametrize("test_config",
                             [test_config_t1, test_config_t2, test_config_t3, test_config_t4, test_config_t5])
    @pytest.mark.workers_and_threads
    def test_workers_and_threads_async(self, test_config):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/async/items"
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
        generate_chart(t=test_config, values=p.chart_values, fields=p.chart_titles)

    @pytest.mark.parametrize("test_config",
                             [test_config_t1, test_config_t2, test_config_t3, test_config_t4, test_config_t5])
    @pytest.mark.workers_and_threads
    def test_workers_and_threads_sync_big_json_response(self, test_config):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/sync/big_json_response"
            container["request_count"] = 500
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
        generate_chart(t=test_config, values=p.chart_values, fields=p.chart_titles)

    @pytest.mark.parametrize("test_config",
                             [test_config_t1, test_config_t2, test_config_t3, test_config_t4, test_config_t5])
    @pytest.mark.workers_and_threads
    def test_workers_and_threads_async_big_json_response(self, test_config):
        async_test_config = []
        for container in test_config.copy():
            container["uri"] = "/async/big_json_response"
            container["request_count"] = 500
            async_test_config.append(container)
        print(async_test_config)
        p = CompareContainers(async_test_config)
        p.run_test()
        p.sum_container_results()
        generate_chart(t=test_config, values=p.chart_values, fields=p.chart_titles)
