import re
from datetime import datetime
from datetime import timezone

from jinja2 import Markup
from jinja2 import evalcontextfilter
from tzlocal import get_localzone

import config

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


# noinspection PyUnresolvedReferences
def render_date(utcdate, fmt='%x'):
    """
    :type utcdate: datetime
    :type fmt: str
    :rtype: str

    """
    if not utcdate:
        return ''

    local = utcdate.replace(tzinfo=timezone.utc).astimezone(get_localzone())
    return local.strftime(fmt)


def is_admin(user):
    """
    :type user: opwen_webapp.models.User
    :rtype: bool

    """
    return user and user.has_role('administrator')


def _key_for_attribute_sort(attribute, default):
    """
    :type attribute: str
    :type default: T
    :rtype: T -> T

    """
    def key(item):
        if not item:
            return default

        attribute_value = getattr(item, attribute, None)
        if not attribute_value:
            return default

        return attribute_value

    return key


def sort_by_date(iterable, reverse=False):
    """
    :type iterable: collections.Iterable[datetime]
    :type reverse: bool
    :rtype: list[datetime]

    """
    return sorted(iterable,
                  reverse=reverse,
                  key=_key_for_attribute_sort('date', datetime.utcnow()))


def ui(key):
    """
    :type key: str
    :rtype: str

    """
    return config.ui(key.split('.')[-1]) if key else ''


def lang2flag(lang_code):
    """
    :type lang_code: str
    :rtype: str

    """
    return {
        'en': 'ca',
    }.get(lang_code, lang_code)


def lang2name(lang_code):
    """
    :type lang_code: str
    :rtype: str

    """
    return {
        'en': 'English',
        'it': 'Italiano',
    }.get(lang_code, lang_code)


@evalcontextfilter
def safe_multiline(eval_ctx, value):
    html = '\n\n'.join('<p>%s</p>' % paragraph.replace('\n', '<br>\n')
                       for paragraph in _paragraph_re.split(value))
    return Markup(html) if eval_ctx.autoescape else html
