import csv

from typing import Dict, Any


class Parser:
    LAST_CHECKED_AB_REVISION = 1826891

    @staticmethod
    def parse_ab_result(string: str) -> Dict:
        if not string:
            return {}

        def right_side_parser(x):
            return str(x.split(':')[1].strip())

        def number_followed_by_space(x):
            return x.split(' ')[0].strip()

        def parse_connection_times_line(x):
            split = right_side_parser(x).split(' ')
            split = [x for x in split if x]
            return {
                'min':  float(split[0]),
                'mean': float(split[1]),
                'std':  float(split[2]),
                'med':  float(split[3]),
                'max':  float(split[4]),
            }

        rules: Dict[str, Dict[str, Any]] = {
            'This is ApacheBench': {
                'key': 'revision',
                'callback': lambda x: x.split(' ')[-2],
            },
            'Document Path': {
                'key': 'path',
                'callback': lambda x: right_side_parser(x),
            },
            'Concurrency Level': {
                'key': 'clients',
                'callback': lambda x: int(right_side_parser(x)),
            },
            'Time taken for tests': {
                'key': 'time',
                'callback': lambda x: float(number_followed_by_space(right_side_parser(x))),
            },
            'Complete requests': {
                'key': 'completed_requests',
                'callback': lambda x: int(right_side_parser(x)),
            },
            'Failed requests': {
                'key': 'failed_requests',
                'callback': lambda x: int(right_side_parser(x)),
            },
            'Non-2xx responses': {
                'key': 'non-2xx-responses',
                'callback': lambda x: int(right_side_parser(x)),
            },
            'Total transferred': {
                'key': 'total_bytes',
                'callback': lambda x: int(number_followed_by_space(right_side_parser(x))),
            },
            'Requests per second': {
                'key': 'rps',
                'callback': lambda x: float(number_followed_by_space(right_side_parser(x))),
            },
            'across all concurrent requests': {
                'key': 'time_mean_all',
                'callback': lambda x: float(number_followed_by_space(right_side_parser(x))),
            },
            'Time per request': {
                'key': 'time_mean',
                'callback': lambda x: float(number_followed_by_space(right_side_parser(x))),
            },
            'Transfer rate': {
                'key': 'transfer_rate',
                'callback': lambda x: float(number_followed_by_space(right_side_parser(x))),
            }
        }

        lines = string.split('\n')
        data = {}
        while lines:
            line = lines.pop(0)
            for k, v in rules.items():
                if k in line:
                    if 'callback' not in v:
                        v['callback'] = lambda x: x
                    value = v['callback'](line)
                    data[v['key']] = value
                    break

            if 'Connection Times' in line:
                times = {}
                # Pop the line with min max etc.
                lines.pop(0)

                times['connect'] = parse_connection_times_line(lines.pop(0))
                times['processing'] = parse_connection_times_line(lines.pop(0))
                times['waiting'] = parse_connection_times_line(lines.pop(0))
                times['total'] = parse_connection_times_line(lines.pop(0))

                data['times'] = times

        return data

    @staticmethod
    def parse_timing_csv(file) -> Dict:
        if not file:
            return {}

        data = {}

        try:
            with open(file) as f:
                reader = csv.DictReader(f, fieldnames=('percentage', 'time'))
                for row in reader:
                    if 'Percentage' in row['percentage']:
                        continue
                    data[int(row['percentage'])] = float(row['time'])
        except IOError:
            print('Failed to open CSV file for reading.')

        return data
