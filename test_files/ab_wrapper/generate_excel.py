import os
import xlsxwriter
import json
import itertools
import datetime
from ab_wrapper import collector

from ab_wrapper.config import Config


class ExcelGenerator:

    EXCEL_FILENAME = 'spreadsheet.xlsx'

    DATA = {}

    SEPARATOR_KEY = '__separator'
    TIMESTAMP_KEY = '__timestamp'
    LESS_IS_BETTER = 0
    MORE_IS_BETTER = 1

    def __init__(self):
        self.excel_book = xlsxwriter.Workbook(self.EXCEL_FILENAME)

    def get_data_for_timestamp_and_config_key(self, timestamp, config_key):

        if timestamp in self.DATA:
            if config_key in self.DATA[timestamp]:
                return self.DATA[timestamp][config_key]

        return None

    @staticmethod
    def write_header(data, sheet):
        i = 0
        for key, value in data.items():
            sheet.write(i, 0, key)
            sheet.write(i, 1, value)
            i += 1

        return i

    def write_timestamps(self, one_entry, sheet, offset=0):

        def get_key_from_entry_by_identifier(_key, _entry):
            split_key = _key.split('.')
            sub_entry = _entry
            while split_key:
                one_split = split_key.pop(0)
                if one_split in sub_entry:
                    sub_entry = sub_entry[one_split]
                else:
                    return None
            return sub_entry

        improvement_format = self.excel_book.add_format({
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006',
        })

        degradation_format = self.excel_book.add_format({
            'bg_color': '#C6EFCE',
            'font_color': '#006100',
        })

        mapping = {
            '': {
                'key': self.SEPARATOR_KEY,
                'comparison': None,
            },
            '-': {
                'key': self.TIMESTAMP_KEY,
                'comparison': None,
            },
            'Runtime': 'ab_result.time',
            'Completed requests': {
                'key': 'ab_result.completed_requests',
                'comparison': self.MORE_IS_BETTER,
            },
            'Failed requests': 'ab_result.failed_requests',
            'Requests per second': {
                'key': 'ab_result.rps',
                'comparison': self.MORE_IS_BETTER,
            },
            'Mean time': 'ab_result.time_mean',
            'Mean time across all requests': 'ab_result.time_mean_all',
            'Transfer Rate [Kb/sec]': {
                'key': 'ab_result.transfer_rate',
                'comparison': self.MORE_IS_BETTER,
            },
            'Timing': self.SEPARATOR_KEY,
        }

        for top in ['connect', 'processing', 'waiting', 'total']:
            for mid in ['min', 'mean', 'std', 'med', 'max']:
                mapping['    ' + top + '    ' + mid] = 'ab_result.times.' + top + '.' + mid

        mapping['Detailed percentiles'] = self.SEPARATOR_KEY
        for i in itertools.chain(range(0, 81, 5), range(81, 101)):
            mapping[str(i) + ' percentile'] = 'percentages.' + str(i)

        pairs, i = 0, 0
        for timestamp in sorted(one_entry.keys()):
            data = one_entry[timestamp]
            i = offset

            for description, key in mapping.items():
                if pairs == 0:
                    sheet.write(i, pairs * 2, description)

                comparison = self.LESS_IS_BETTER
                if isinstance(key, dict):
                    options = key
                    key = options['key']
                    comparison = options['comparison']

                if pairs != 0:
                    if key != self.SEPARATOR_KEY:
                        if comparison is not None:
                            sheet.write(i, pairs * 2,
                                        '=OFFSET(INDIRECT(ADDRESS(ROW(), COLUMN())),0,1) - OFFSET(INDIRECT('
                                        'ADDRESS(ROW(), COLUMN())),0,-1)')

                            criteria_mapping = {
                                self.LESS_IS_BETTER: ['<=', '>'],
                                self.MORE_IS_BETTER: ['>=', '<']
                            }

                            sheet.conditional_format(i, pairs * 2, i, pairs * 2, {
                                'type': 'cell',
                                'criteria': criteria_mapping[comparison][0],
                                'value': 0,
                                'format': degradation_format,
                            })

                            sheet.conditional_format(i, pairs * 2, i, pairs * 2, {
                                'type': 'cell',
                                'criteria': criteria_mapping[comparison][1],
                                'value': 0,
                                'format': improvement_format,
                            })

                if key == self.SEPARATOR_KEY:
                    i += 1
                    continue
                elif key == self.TIMESTAMP_KEY:
                    sheet.write(i, (pairs * 2) + 1,
                                datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                )
                else:
                    value = get_key_from_entry_by_identifier(key, data)
                    sheet.write(i, (pairs * 2) + 1, value)
                i += 1

            sheet.set_column(pairs * 2, pairs * 2, 10)
            sheet.set_column(pairs * 2 + 1, pairs * 2 + 1, 20)
            pairs += 1

        sheet.set_column(0, 0, 30)

        pass

    def write_all_data(self, book: xlsxwriter.Workbook):
        config = Config()
        sheets = {}
        final_data = {}
        for config_key, config in config.get().items():
            sheets[config_key] = book.add_worksheet(config_key[0:31])

            for timestamp in self.DATA.keys():
                data = self.get_data_for_timestamp_and_config_key(timestamp, config_key)
                if data is None:
                    print('No data found for %d %s!!!' % (timestamp, config_key))
                else:
                    if config_key not in final_data:
                        final_data[config_key] = {}
                        final_data[config_key]['_header'] = {
                            'path': data['ab_result']['path'],
                            'clients': data['ab_result']['clients'],
                        }
                    final_data[config_key][timestamp] = data

        for config_key, one_entry in final_data.items():
            sheet = sheets[config_key]
            offset = 0
            if '_header' in one_entry:
                offset = self.write_header(one_entry.pop('_header'), sheet)

            self.write_timestamps(one_entry, sheet, offset)

        pass

    def write_to_excel(self):
        directory = os.path.join(collector.Collector.OUTPUT_DIRECTORY, '../')
        directory = os.path.abspath(directory)

        with os.scandir(directory) as it:
            for entry in it:
                dir_name = entry.name
                if not dir_name.startswith('.') and dir_name.isdigit() and entry.is_dir():
                    data_file = os.path.join(directory, dir_name, 'data.json')
                    try:
                        with open(data_file, 'r') as f:
                            self.DATA[int(dir_name)] = json.load(f)
                    except FileNotFoundError:
                        continue

        self.write_all_data(self.excel_book)

        self.excel_book.close()
