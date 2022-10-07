import os
import shutil
import json
import time

from typing import Dict
from ab_wrapper.generate_excel import ExcelGenerator


class Collector:

    OUTPUT_DIRECTORY: str = os.path.join(os.path.dirname(__file__), 'reports', str(int(time.time())))

    data: Dict = {}

    def __init__(self):
        if os.path.isdir(self.OUTPUT_DIRECTORY):
            shutil.rmtree(self.OUTPUT_DIRECTORY)
        os.makedirs(self.OUTPUT_DIRECTORY)

    def collect(self, key: str, data: Dict) -> None:
        self.data[key] = data

    def write_report(self):

        if not self.data:
            print('Nothing to write!')
            os.rmdir(self.OUTPUT_DIRECTORY)
            return

        print('Writing report to ' + self.OUTPUT_DIRECTORY)
        try:
            with open(os.path.join(self.OUTPUT_DIRECTORY, 'data.json'), 'w') as f:
                json.dump(self.data, f, indent=4)
        except IOError:
            print('Failed to save data.json!!!')

        ExcelGenerator().write_to_excel()

        print('Finished writing excel data')
        print('Finished writing report!')

