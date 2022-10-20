import os
import subprocess
import sys
import threading

from typing import Dict, Any
from ab_wrapper.collector import Collector
from ab_wrapper.config import Config
from ab_wrapper.exit_codes import EXIT_CONFIG_DOES_NOT_EXIST
from ab_wrapper.parser import Parser


class Runner:
    CSV_DATA_FILE = 'data.csv'

    config: Dict[str, Dict[str, Any]] = None

    def __init__(self, config: Config, parser: Parser, collector: Collector):
        self.config = config.get()
        self.parser = parser
        self.collector = collector

    def compose_command(self, config_name: str) -> list:
        if config_name not in self.config:
            print('The config with name ' + config_name + ' does not exist.')
            sys.exit(EXIT_CONFIG_DOES_NOT_EXIST)

        cmd = ['ab']
        options = self.config[config_name]
        if options['keep-alive']:
            cmd.append('-k')
        cmd.append('-c ' + str(options['clients']))
        cmd.append('-n ' + str(options['count']))
        cmd.append('-t ' + str(options['time']))
        cmd.append('-e')
        cmd.append(self.CSV_DATA_FILE)

        if options['auth']:
            cmd.append('-A ' + options['auth'])
        if not options['fixed-length']:
            cmd.append('-l')

        cmd.append(options['url'])

        return cmd

    @staticmethod
    def execute_command_by_line(cmd: list) -> str:
        """"
            Executes a command and yields its output by lines
        """
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(process.stdout.readline, ""):
            yield stdout_line
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

    @staticmethod
    def execute_command_whole_output(cmd: list) -> (str, str, int):
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='ascii', shell=True, timeout=100, env=os.environ.copy())
        return process.stdout, process.stderr, int(process.returncode)

    def make_time_estimate(self) -> (int, int, int):
        seconds = 0
        for key, config in self.config.items():
            seconds += config['time']
        return self.get_human_time(seconds)

    @staticmethod
    def get_human_time(seconds) -> (int, int, int):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return h, m, s

    def run(self):
        try:
            for key, config in self.config.items():
                command = self.compose_command(key)
                # print('Running command ' + ' '.join(command))

                stdout, stderr, error_code = self.execute_command_whole_output(command)

                if error_code is not 0:
                    print('An ap process failed with error code ' + str(error_code) + '!!!')
                    print(stderr)
                else:
                    print(stderr)

                self.collector.collect(key, {
                    'ab_result': self.parser.parse_ab_result(stdout),
                    'percentages': self.parser.parse_timing_csv(self.CSV_DATA_FILE)
                })

        except subprocess.TimeoutExpired:
            print("Timeout reached")
        except KeyboardInterrupt:
            print("Cancelling run!")

        self.collector.write_report()


class ProgressWatcher(threading.Thread):
    TIMEOUT: float = 0.01

    def __init__(self, time: int):
        super().__init__()
        self.time = time * 100
        self.cv = threading.Condition()
        self.stopped = False
        self.cancelled = False
        self.setDaemon(True)

    def run(self) -> bool:
        self.cv.acquire()
        while True:
            try:
                print('\rAbout %.2f seconds remaining...' % (self.time / 100), end='\r')
                self.cv.wait(timeout=self.TIMEOUT)
                self.time -= 1
                if self.stopped:
                    try:
                        return False
                    finally:
                        self.cv.release()
            except KeyboardInterrupt:
                self.cancelled = True
                break
        return True

    def stop(self):
        self.cv.acquire()
        self.stopped = True
        self.cv.notify()
        self.cv.release()
        print('\n')

        return self.cancelled
