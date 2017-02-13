try:
    from html import unescape
except ImportError:
    from html.parser import HTMLParser
    unescape = HTMLParser().unescape  # type: ignore

import re

from wtforms import StringField
from wtforms import TextAreaField
from wtforms.widgets import Input


class EmailInput(Input):
    input_type = 'email'


class EmailField(StringField):
    widget = EmailInput()


class HtmlTextAreaField(TextAreaField):
    _script_tags_re = re.compile(r'<script[\s\S]+?/script>', re.IGNORECASE)

    # pylint:disable=attribute-defined-outside-init
    # noinspection PyAttributeOutsideInit
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = self._to_safe_html(self.data)

    def _value(self):
        value = super()._value()
        return self._to_safe_html(value)

    @classmethod
    def _remove_script_tags(cls, data):
        """
        :type data: str
        :rtype: str

        """
        match = cls._script_tags_re.search(data)
        while match:
            start = match.start()
            end = match.end()
            data = data[:start] + data[end:]
            match = cls._script_tags_re.search(data)

        return data

    @classmethod
    def _to_safe_html(cls, data):
        """
        :type data: str | None
        :rtype: str

        """
        if not data:
            return ''

        data = unescape(data)
        data = cls._remove_script_tags(data)
        return data


class SuffixedStringField(StringField):
    def __init__(self, suffix='', *args, **kwargs):
        """
        :type suffix: str

        """
        super().__init__(*args, **kwargs)
        self._suffix = suffix

    # pylint:disable=attribute-defined-outside-init
    # noinspection PyAttributeOutsideInit
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = self._ensure_suffix(self.data)

    def _value(self):
        value = super()._value()
        return self._ensure_suffix(value)

    def _ensure_suffix(self, value):
        """
        :type value: str
        :rtype: str

        """
        if value and not value.endswith(self._suffix):
            return value + self._suffix
        else:
            return value
