import pytest

from compare_container_performance import CompareContainers

test_config = [{'name': 'app_gunicorn_w1_t0', 'port': 8010, 'baseline': True},
               {'name': 'app_gunicorn_w2_t0', 'port': 8011, 'baseline': False},
               {'name': 'app_uvicorn_w1', 'port': 8012, 'baseline': False},
               {'name': 'app_uvicorn_w2', 'port': 8014, 'baseline': False}]

@pytest.mark.gunicorn_vs_uvicorn
def test_gunicorn_vs_uvicorn_sync():
    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()


@pytest.mark.gunicorn_vs_uvicorn
def test_gunicorn_vs_uvicorn_async():
    async_test_config = []
    for container in test_config.copy():
        container['uri'] = '/async/items'
        async_test_config.append(container)
    print(async_test_config)
    p = CompareContainers(async_test_config)
    p.run_test()
    p.sum_container_results()


@pytest.mark.gunicorn_vs_uvicorn
def test_gunicorn_vs_uvicorn_sync_big_json_response():
    async_test_config = []
    for container in test_config.copy():
        container['uri'] = '/sync/big_json_response'
        container['request_count'] = 1000
        async_test_config.append(container)
    print(async_test_config)
    p = CompareContainers(async_test_config)
    p.run_test()
    p.sum_container_results()


@pytest.mark.gunicorn_vs_uvicorn
def test_gunicorn_vs_uvicorn_async_big_json_response():
    async_test_config = []
    for container in test_config.copy():
        container['uri'] = '/async/big_json_response'
        container['request_count'] = 1000
        async_test_config.append(container)
    print(async_test_config)
    p = CompareContainers(async_test_config)
    p.run_test()
    p.sum_container_results()
