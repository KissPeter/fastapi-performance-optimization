import copy
import os
import subprocess
import shlex
from collections import defaultdict

from tabulate import tabulate

from ab_wrapper.runner import Runner
from ab_wrapper.config import Config
from ab_wrapper.parser import Parser
from ab_wrapper.collector import Collector
from typing import Dict, List, Union
from dataclasses import dataclass


@dataclass
class TestFields:
    failed_requests: str = 'failed_requests'
    rps: str = 'rps'
    time_mean: str = 'time_mean'


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
                if error_code != 0:
                    print('An ap process failed with error code ' + str(error_code) + '!!!')
                    print(stderr)
                else:
                    self.ab_results = self.parser.parse_ab_result(stdout)

        except subprocess.TimeoutExpired:
            print("Timeout reached")


class TestContainer:
    DEFAULT_URI = "/items/"

    def __init__(self, port: int = 8000, uri: str = DEFAULT_URI):
        self.ab_parser = Parser()
        self.ab_collector = Collector()
        self.port = port
        self.uri = self._identify_uri(uri=uri)
        self.ab_raw_results = {}

    def _identify_uri(self, uri):
        if uri:
            uri = uri if uri.startswith('/') else f"/{uri}"
        else:
            uri = self.DEFAULT_URI
        return uri

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
        for key in [TestFields.time_mean, TestFields.rps, TestFields.failed_requests]:
            _return[key] = self.ab_raw_results.get(key)
        return _return


class CompareContainers:


    def __init__(self, test_config: List[dict]):
        self.test_config = test_config
        self.test_results = []

    def run_test(self):
        for container in self.test_config:
            port = container.get('port')
            name = container.get('name')
            uri = container.get('uri')
            baseline = container.get('name', False)
            container['results'] = self.test_container(port=port, uri=uri)
            self.test_results.append(container)

        print(self.test_results)

    def sum_test_results(self, results: list) -> dict:
        """
        IN:
        [{'failed_requests': 0, 'rps': 1280.72, 'time_mean': 78.081}]
        Out (in dict)
        | **Test attribute**    | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline [%] |
        |-----------------------|----------------|----------------|----------------|-------------|----------------------------|
        | Requests per second   | 686,21         | 689,44         | 674,9          | **683,52**  | -51,59                     |
        | Time per request [ms] | 145,728        | 145,044        | 148,17         | **146,31**  | 34,03                      |
        """
        pass

    @staticmethod
    def tabulate_data(headers: List[str], data: dict):
        """
        tabulate_data(
            headers=["Node name", "Last activity"],
            data={},
        )
        """
        table_data = []
        for k, v in data.items():
            row = [k]
            if isinstance(v, list):
                row.extend(v)
            else:
                row.append(v)
            table_data.append(row)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    @staticmethod
    def get_avg_of_list(elements: List[Union[int, float]]) -> float:
        if len(elements) > 0:
            return round(sum(elements) / len(elements), 4)
        else:
            return 0.0

    def sum_results(self, results: List[dict]) -> dict:
        rps = list()
        time_mean = list()
        failed_requests = 0
        result = defaultdict(list)
        for test in results:
            failed_requests += test.get(TestFields.failed_requests)
            rps.append(test.get(TestFields.rps))
            time_mean.append(test.get(TestFields.time_mean))
        # assert failed_requests > 0, f"{failed_requests} requests failed"
        result[TestFields.rps] = rps.copy()
        result[TestFields.rps].append(self.get_avg_of_list(rps))
        result[TestFields.time_mean] = time_mean.copy()
        result[TestFields.time_mean].append(self.get_avg_of_list(time_mean))
        return result

    @staticmethod
    def get_diff_percent_to_baseline(res: float, baseline: float, round_tens:int=2):
        return round(res / baseline * 100, round_tens)

    def sum_container_results(self):
        """
        [{'name': 'base', 'port': 8000, 'baseline': True,
        'results': [{'failed_requests': 0, 'rps': 1280.72, 'time_mean': 78.081}]},
        {'name': 'app_one_base_middleware', 'port': 8001, 'baseline': False, 'results': [{'failed_requests': 0, 'rps': 917.87, 'time_mean': 108.948}]}, {'name': 'app_two_base_middlewares', 'port': 8002, 'baseline': False, 'results': [{'failed_requests': 0, 'rps': 612.07, 'time_mean': 163.379}]}]
        :return:
        """
        tabulate_headers = ["**Test attribute**"]
        for i in range(TEST_RUN_PER_CONTAINER):
            tabulate_headers.append(f"**Test run {i + 1}**")
        tabulate_headers.append("**Average**")
        tabulate_headers_baseline = tabulate_headers.copy()
        tabulate_headers.append("Difference to baseline [%]")
        baseline_rps = 0
        baseline_time_mean = 0
        results = {}
        for container in self.test_results:
            # print(f"Container name: {container.get('name')}, container port: {container.get('port')}")
            if container.get('baseline'):
                baseline = self.sum_results(container.get('results'))
                baseline_rps = baseline.get(TestFields.rps)[-1]
                baseline_time_mean = baseline.get(TestFields.time_mean)[-1]
                print(f'Baseline:')
                self.tabulate_data(headers=tabulate_headers_baseline, data=baseline)
            else:
                results[container.get('port')] = self.sum_results(container.get('results'))
        for container_port, result in results.items():
            print(f"Containerport: {container_port}")
            cont_avg_rps = result[TestFields.rps][-1]
            result[TestFields.rps].append(self.get_diff_percent_to_baseline(cont_avg_rps, baseline_rps))
            cont_avg_time_mean = result[TestFields.time_mean][-1]
            result[TestFields.time_mean].append(
                self.get_diff_percent_to_baseline(cont_avg_time_mean, baseline_time_mean))
            self.tabulate_data(headers=tabulate_headers, data=result)

    def test_container(self, port, uri):
        _results = []
        for i in range(TEST_RUN_PER_CONTAINER):
            print(f"{i}. of {port} / {uri}")
            t = TestContainer(port=port, uri=uri)
            t.run()
            _results.append(t.get_results())
        return _results


if __name__ == '__main__':
    TEST_RUN_PER_CONTAINER = 3
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
    p.sum_container_results()
