import json
import sys

from typing import Dict, Any
from ab_wrapper.exit_codes import EXIT_CONFIG_DOES_NOT_EXIST, EXIT_FAILED_TO_PARSE_CONFIG


class Config:

    OPTIONS_FILE: str = 'options.json'

    DEFAULTS_KEY: str = '_defaults'

    config: Dict[str, Dict[str, Any]] = {}

    defaults: Dict[str, Any] = {
        'time': 10,
        'count': 100,
        'clients': 10,
        'keep-alive': True,
        'fixed-length': False,
    }

    def __init__(self) -> None:
        try:
            with open(self.OPTIONS_FILE) as f:
                data = json.load(f)

                if self.DEFAULTS_KEY in data:
                    self.defaults = {**self.defaults, **data[self.DEFAULTS_KEY]}

                for key, one_location in data.items():
                    if key == self.DEFAULTS_KEY:
                        continue
                    self.config[key] = {**self.defaults, **one_location}

                self.check_config()

        except ValueError:
            print('Failed to parse config file!')
            sys.exit(EXIT_FAILED_TO_PARSE_CONFIG)

        except FileNotFoundError:
            print('Did not find config.json. Does it exist?')
            sys.exit(EXIT_CONFIG_DOES_NOT_EXIST)

    def check_config(self) -> None:
        config_copy = self.config.copy()
        for config_key, one_config in config_copy.items():

            required_keys = ('time', 'count', 'clients', 'keep-alive', 'url')
            if not all(k in one_config for k in required_keys):
                print('The config ' + config_key + ' is missing a required key.')
                raise ValueError

            if not isinstance(one_config['time'], int):
                print('The config ' + config_key + ' has incorrect value for time')
                raise ValueError
            if not isinstance(one_config['count'], int):
                print('The config ' + config_key + ' has incorrect value for count')
                raise ValueError
            if not isinstance(one_config['keep-alive'], bool):
                print('The config ' + config_key + ' has incorrect value for keep-alive')
                raise ValueError
            if 'fixed-length' in one_config:
                if not isinstance(one_config['fixed-length'], bool):
                    print('The config ' + config_key + ' has incorrect value for fixed-length')
                    raise ValueError
            if not isinstance(one_config['url'], str):
                print('The config ' + config_key + ' has incorrect value for url')
                raise ValueError

            if isinstance(one_config['clients'], list):
                for one_client_option in one_config['clients']:
                    self.config[config_key + '-' + str(one_client_option)] = {**one_config, 'clients': one_client_option}
                self.config.pop(config_key)
            elif not isinstance(one_config['clients'], int):
                print('The config ' + config_key + ' has incorrect value for clients')
                raise ValueError

    def get(self) -> Dict[str, Dict[str, Any]]:
        return self.config
