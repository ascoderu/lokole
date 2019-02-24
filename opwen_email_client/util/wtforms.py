try:
    from html import unescape
except ImportError:
    from html.parser import HTMLParser
    unescape = HTMLParser().unescape  # type: ignore

from re import IGNORECASE
from re import compile as re_compile
from typing import Optional

from crontab import CronItem
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import HostnameValidation
from wtforms.validators import Regexp
from wtforms.validators import ValidationError


class CronSchedule:
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field, message=None):
        schedule = (field.data or '').strip()
        if not schedule:
            return

        try:
            CronItem().setall(schedule)
        except (KeyError, ValueError):
            message = message or self.message or field.gettext('Invalid cron')
            raise ValidationError(message)


class Emails(Regexp):
    def __init__(self, email_address_delimiter, message=None):
        self.validate_hostname = HostnameValidation(require_tld=True)
        self.email_address_delimiter = email_address_delimiter
        super().__init__(r'^.+@([^.@][^@]+)$', IGNORECASE, message)

    # noinspection PyMethodOverriding
    def __call__(self, form, field):
        message = self.message
        if message is None:
            message = field.gettext('Invalid email address.')

        messages = message.split(self.email_address_delimiter)
        for message in messages:
            match = super().__call__(form, field, message.strip())
            if not self.validate_hostname(match.group(1)):
                raise ValidationError(message)


class HtmlTextAreaField(TextAreaField):
    _script_tags_re = re_compile(r'<script[\s\S]+?/script>', IGNORECASE)

    # noinspection PyAttributeOutsideInit
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = self._to_safe_html(self.data)

    def _value(self):
        value = super()._value()
        return self._to_safe_html(value)

    @classmethod
    def _remove_script_tags(cls, data: str) -> str:
        match = cls._script_tags_re.search(data)
        while match:
            start = match.start()
            end = match.end()
            data = data[:start] + data[end:]
            match = cls._script_tags_re.search(data)

        return data

    @classmethod
    def _to_safe_html(cls, data: Optional[str]) -> str:
        if not data:
            return ''

        data = unescape(data)
        data = cls._remove_script_tags(data)
        return data


class SuffixedStringField(StringField):
    def __init__(self, suffix: str = '', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._suffix = suffix

    # noinspection PyAttributeOutsideInit
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = self._ensure_suffix(self.data)

    def _value(self):
        value = super()._value()
        return self._ensure_suffix(value)

    def _ensure_suffix(self, value: str) -> str:
        if value and not value.endswith(self._suffix):
            return value + self._suffix
        else:
            return value
