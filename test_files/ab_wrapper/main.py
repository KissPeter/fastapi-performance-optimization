import sys

from runner import Runner
from config import Config
from parser import Parser
from collector import Collector
from exit_codes import EXIT_ERROR, EXIT_SUCCESS

if __name__ == '__main__':
    config = Config()
    parser = Parser()
    collector = Collector()

    runner = Runner(config, parser, collector)

    # noinspection PyBroadException
    try:
        runner.run()

    except Exception:
        print('Caught an exception in main thread!')
        print('Trying to save anyways...')
        collector.write_report()
        sys.exit(EXIT_ERROR)

    sys.exit(EXIT_SUCCESS)
