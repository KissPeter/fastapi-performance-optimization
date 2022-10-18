from compare_container_performance import CompareContainers


def test_json_response_classes_sync_endpoint():
    test_config = [
        {
            "name": "app_default_json_response_class",
            "port": 8005,
            "baseline": True,
            "uri": "/sync/big_json_response/"
        },
        {
            "name": "app_ojson_response_class",
            "port": 8006,
            "baseline": False,
            "uri": "/sync/big_json_response/"
        },
        {
            "name": "app_ujson_response_class",
            "port": 8007,
            "baseline": False,
            "uri": "/sync/big_json_response/"
        }
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()


def test_json_response_classes_async_endpoint():
    test_config = [
        {
            "name": "app_default_json_response_class",
            "port": 8005,
            "baseline": True,
            "uri": "/async/big_json_response/"
        },
        {
            "name": "app_ojson_response_class",
            "port": 8006,
            "baseline": False,
            "uri": "/async/big_json_response/"
        },
        {
            "name": "app_ujson_response_class",
            "port": 8007,
            "baseline": False,
            "uri": "/async/big_json_response/"
        }
    ]

    p = CompareContainers(test_config)
    p.run_test()
    p.sum_container_results()
