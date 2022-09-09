from ..ab_wrapper.runner import Runner
from ..ab_wrapper.config import Config
from ..ab_wrapper.parser import Parser
from ..ab_wrapper.collector import Collector
from typing import Dict


class ABConfig(Config):

    def __init__(self, config: Dict):
        # we don't want to load from file so don't call super
        self.config = self.defaults
        self.config.update(config)


class ABRunner(Runner):

    def compose_command(self, config_name: str) -> list:
        cmd = ['ab']
        options = self.config[config_name]
        cmd.append('-c ' + str(options['clients']))
        cmd.append('-n ' + str(options['count']))
        cmd.append('-T ' + str(options['content_type']))
        cmd.append('-p ' + str(options['request_body']))
        cmd.append('-e')

        if not options.get('fixed-length'):
            cmd.append('-l')

        cmd.append(options['url'])

        return cmd


class TestContainer:

    def __init__(self, port: int = 8000, uri: str = "/items/"):
        self.ab_parser = Parser()
        self.ab_collector = Collector()
        self.port = port
        self.uri = uri if uri.startswith('/') else f"/{uri}"

    def _get_config(self):
        return {
            "clients": 100,
            "count": 10000,
            "content_type": "application/json",
            "request_body": "requestbody",
            "url": f"http://127.0.0.1:{self.port}{self.uri}"
        }

    def pre_warm(self):
        config = self._get_config()
        config["count"] = config.get("clients", 100)
        _ab_runner = ABRunner(ABConfig(config=config), self.ab_parser, self.ab_collector)
        _ab_runner.run()

    def run(self):
        _ab_runner = ABRunner(ABConfig(config=self._get_config()), self.ab_parser, self.ab_collector)
        _ab_runner.run()

    def get_collection(self):
        return self.ab_collector.data


class CompareContainers:

    def __init__(self, test_config: Dict):
        self.test_config = test_config

    def run_test(self):
        for container in self.test_config:
            port = container.get('port')
            name = container.get('name')
            baseline = container.get('name', False)

    def test_container(self, ab_config):
        pass


test_config = [
    {
        "name": "base",
        "port": 8000,
        "baseline": True
    },
    {
        "name": "app_one_base_middleware",
        "port": 8001,
        "baseline": False
    },
    {
        "name": "app_two_base_middlewares",
        "port": 8002,
        "baseline": False
    }
]
p = CompareContainers(test_config)
p.run_test()