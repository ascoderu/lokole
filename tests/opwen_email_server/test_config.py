from re import match
from unittest import TestCase

from opwen_email_server import config


class ConfigTests(TestCase):
    def test_azure_names_are_valid(self):
        skip_names = {'LOG_LEVEL'}
        skip_values = {None}
        acceptable_config_value = '^[a-z]{3,63}$'
        constants = _get_constants(config, skip_names, skip_values)

        for constant, value in constants:
            if not match(acceptable_config_value, value):
                self.fail('config {} is invalid: {}, should be {}'
                          .format(constant, value, acceptable_config_value))


def _get_constants(container, skip_names, skip_values):
    for variable_name in dir(container):
        if variable_name.upper() != variable_name:
            continue
        if variable_name in skip_names:
            continue
        value = getattr(container, variable_name)
        if value in skip_values:
            continue
        yield variable_name, value
