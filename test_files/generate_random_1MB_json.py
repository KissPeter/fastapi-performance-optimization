import json
import string
from random import randint, choice


def generate_random_int(size=1000):
    _data = []
    for _ in range(size):
        _data.append(str(randint(0, 9)))
    return "".join(_data)


def generate_random_string(size=1000):
    _data = []
    for _ in range(size):
        _data.append(choice(string.ascii_letters + string.punctuation))
    return "".join(_data)


def generate_random_array(size=1000):
    _data = []
    for _ in range(size):
        _data.append(choice(string.ascii_letters + string.punctuation))
    return _data


def generate_random_bool():
    return bool(randint(0, 1))


def generate_random_dict(size=10):
    _data = {}
    value_options = [generate_random_array, generate_random_string, generate_random_int,
                     generate_random_bool]
    value_generator = choice(value_options)
    for i in range(size):
        value = value_generator()
        _data[i] = value
        # print(f"{i}. {value}")
    return _data


class TestJSON:

    def __init__(self, max_size_MB=1):
        self.testdata = {}
        self.max_size_bytes = max_size_MB * 1024 * 1024
        self._generate()

    def _generate(self):
        size = 0
        iteration = 0
        while size <= self.max_size_bytes:
            self.testdata[iteration] = generate_random_dict()
            size = len(json.dumps(self.testdata))
            print(f"{iteration}. iteration, test data size: {size} bytes")
            iteration += 1
        print(f"Test data generation ready, size: {size}")

    def save_to_file(self):
        with open('./test_json_1MB.json', 'w') as f:
            f.write(json.dumps(self.testdata))


t = TestJSON()
t.save_to_file()
