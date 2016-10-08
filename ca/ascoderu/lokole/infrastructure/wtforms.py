from wtforms import StringField
from wtforms.widgets import Input


class EmailInput(Input):
    input_type = 'email'


class EmailField(StringField):
    widget = EmailInput()


class SuffixedStringField(StringField):
    def __init__(self, suffix='', *args, **kwargs):
        """
        :type suffix: str

        """
        super().__init__(*args, **kwargs)
        self._suffix = suffix

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
