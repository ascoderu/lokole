from abc import ABCMeta
from abc import abstractproperty
from collections import namedtuple
from unittest import TestCase

from wtforms import ValidationError

from ascoderu_webapp.forms import EmailOrLocalUser
from ascoderu_webapp.forms import UserDoesNotAlreadyExist
from utils.testing import AppTestMixin


class BaseFormFieldValidatorTest(AppTestMixin, TestCase, metaclass=ABCMeta):
    @abstractproperty
    def validator_under_test(self):
        raise NotImplementedError

    def _create_field(self, data):
        return namedtuple('Field', 'data')(data)

    def _run_validator(self, data):
        validator = self.validator_under_test('some error message')
        field = self._create_field(data)
        validator(field=field, form=None)

    def assertValidatesAgainst(self, data):
        self._run_validator(data)

    def assertDoesNotValidateAgainst(self, data):
        with self.assertRaises(ValidationError):
            self._run_validator(data)


class TestUserDoesNotAlreadyExist(BaseFormFieldValidatorTest):
    validator_under_test = UserDoesNotAlreadyExist

    def test_passes_for_new_user(self):
        self.assertValidatesAgainst('someone')

    def test_fails_for_existing_user(self):
        user = self.new_user(name='someone')
        self.assertDoesNotValidateAgainst(user.name)


class TestEmailOrLocalUser(BaseFormFieldValidatorTest):
    validator_under_test = EmailOrLocalUser

    def test_passes_for_email(self):
        self.assertValidatesAgainst('someone@test.net')

    def test_passes_for_local_user(self):
        user = self.new_user(name='someone')
        self.assertValidatesAgainst(user.name)

    def test_fails_for_non_email_input_that_is_not_local_user(self):
        self.new_user(name='someone')
        self.assertDoesNotValidateAgainst('someone-else')
