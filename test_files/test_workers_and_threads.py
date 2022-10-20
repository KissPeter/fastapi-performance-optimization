import pytest

from compare_container_performance import CompareContainers

test_config = [
    {
        "name": "app_w1_t1",
        "port": 8008,
        "baseline": True,
    },
    {
        "name": "app_w2_t1",
        "port": 8009,
        "baseline": False,
    },
    {
        "name": "app_w3_t1",
        "port": 8010,
        "baseline": False,
    },
    {
        "name": "app_w1_t2",
        "port": 8011,
        "baseline": False,
    },
    {
        "name": "app_w1_t3",
        "port": 8012,
        "baseline": False,
    },
    {
        "name": "app_w2_t2",
        "port": 8013,
        "baseline": False,
    },
    {
        "name": "app_w2_t3",
        "port": 8014,
        "baseline": False,
    },
    {
        "name": "app_w3_t2",
        "port": 8015,
        "baseline": False,
    },
    {
        "name": "app_w3_t3",
        "port": 8016,
        "baseline": False,
    },
    {
        "name": "app_w4_t1",
        "port": 8017,
        "baseline": False,
    },
    {
        "name": "app_w4_t2",
        "port": 8018,
        "baseline": False
    },
    {
        "name": "app_w4_t3",
        "port": 8019,
        "baseline": False,
    },
    {
        "name": "app_w4_t4",
        "port": 8020,
        "baseline": False,
    }
]


@pytest.mark.workers_and_threads
def test_workers_and_threads_sync():

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()

@pytest.mark.workers_and_threads
def test_workers_and_threads_async():
    async_test_config = []
    for container in test_config.copy():
        container['uri'] = '/async/items'
        async_test_config.append(container)
    p = CompareContainers(async_test_config)
    p.run_test()
    p.sum_container_results()