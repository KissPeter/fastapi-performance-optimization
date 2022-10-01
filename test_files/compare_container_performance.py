import os
import subprocess
import shlex

from ab_wrapper.runner import Runner
from ab_wrapper.config import Config
from ab_wrapper.parser import Parser
from ab_wrapper.collector import Collector
from typing import Dict


class ABConfig(Config):

    def __init__(self, config: Dict):
        # we don't want to load from file so don't call super
        self.config = {}
        data = config
        if self.DEFAULTS_KEY in data:
            self.defaults = {**self.defaults, **data[self.DEFAULTS_KEY]}

        for key, one_location in data.items():
            if key == self.DEFAULTS_KEY:
                continue
            self.config[key] = {**self.defaults, **one_location}
        self.config.update(config)
        self.check_config()


class ABRunner(Runner):

    def __init__(self, config: Config, parser: Parser, collector: Collector):
        super().__init__(config, parser, collector)
        open(self.CSV_DATA_FILE, 'w').close()
        self.ab_results = {}

    def compose_command(self, config_name: str) -> list:
        """
        ab -q -n 1000 -c 100 -T 'application/json' -prequestbody http://127.0.0.1:"$PORT""$URL" >/dev/null
        :param config_name:
        :return:
        """
        cmd = ['ab']
        options = self.config[config_name]
        cmd.append('-q ')
        cmd.append('-c ' + str(options['clients']))
        cmd.append('-n ' + str(options['count']))
        cmd.append('-T ' + str(options['content_type']))
        cmd.append('-p ' + str(options['request_body']))
        cmd.append(' ' + options['url'])

        return cmd

    @staticmethod
    def execute_command_whole_output(cmd: list) -> (str, str, int):
        process = subprocess.run(shlex.split(" ".join(cmd)), stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 encoding='ascii',
                                 shell=False,
                                 timeout=100,
                                 env=os.environ.copy(),
                                 check=False,
                                 universal_newlines=True,
                                 bufsize=0)
        return process.stdout, process.stderr, int(process.returncode)

    def run(self):
        try:
            for key, config in self.config.items():
                command = self.compose_command(key)
                print('Running command ' + ' '.join(command))
                stdout, stderr, error_code = self.execute_command_whole_output(command)
                if error_code is not 0:
                    print('An ap process failed with error code ' + str(error_code) + '!!!')
                    print(stderr)
                else:
                    self.ab_results = self.parser.parse_ab_result(stdout)

        except subprocess.TimeoutExpired:
            print("Timeout reached")


class TestContainer:

    def __init__(self, port: int = 8000, uri: str = "/items/"):
        self.ab_parser = Parser()
        self.ab_collector = Collector()
        self.port = port
        self.uri = uri if uri.startswith('/') else f"/{uri}"
        self.ab_raw_results = {}

    def _get_config(self):
        """
        Defaults: 'time', 'count', 'clients', 'keep-alive', 'url'
        :return:
        """
        return {
            "_defaults": {
                "time": 5,
                "clients": 100,
                "count": 10000,
                "content_type": "'application/json'",
                "request_body": os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requestbody')),
                "keep-alive": False,
                "url": f"http://127.0.0.1:{self.port}{self.uri}"}
        }

    def pre_warm(self):
        config = self._get_config()
        config["count"] = config.get("clients", 100)
        _ab_runner = ABRunner(ABConfig(config=config), Parser(), Collector())
        _ab_runner.run()

    def run(self):
        _ab_runner = ABRunner(ABConfig(config=self._get_config()), self.ab_parser, self.ab_collector)
        _ab_runner.run()
        self.ab_raw_results = _ab_runner.ab_results

    def get_results(self):
        _return = {}
        for key in ['failed_requests', 'rps', 'time_mean']:
            _return[key] = self.ab_raw_results.get(key)
        return _return


class CompareContainers:

    def __init__(self, test_config: Dict):
        self.test_config = test_config
        self.test_results = {}

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
# p = CompareContainers(test_config)
# p.run_test()
# print(ABRunner.execute_command_whole_output(cmd=['ab', '-q ', '-c 100', '-n 10000', "-T 'application/json'", '-p /home/kissp/PycharmProjects/fastapi-middlewares/test_files/requestbody', ' http://127.0.0.1:8000/items/']))
# exit()
p = TestContainer()
p.run()
print("DATA?")
print(p.get_results())
