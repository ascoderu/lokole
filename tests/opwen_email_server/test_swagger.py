from pathlib import Path
from unittest import TestCase

import opwen_email_server

from flex.core import load as load_swagger
from flex.exceptions import ValidationError


class SwaggerTests(TestCase):
    def test_is_valid(self):
        swagger_directory = Path(opwen_email_server.__file__).parent / 'swagger'
        for swagger_file in swagger_directory.glob('*.yaml'):
            try:
                load_swagger(swagger_file)
            except ValidationError as ex:
                self.fail(f"{swagger_file.name} does not pass swagger validation: {ex}")
