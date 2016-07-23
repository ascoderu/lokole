from datetime import timezone
from tzlocal import get_localzone

import re

from jinja2 import Markup
from jinja2 import escape
from jinja2 import evalcontextfilter

import config

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


def render_date(utcdate, fmt='%x'):
    if not utcdate:
        return ''

    local = utcdate.replace(tzinfo=timezone.utc).astimezone(get_localzone())
    return local.strftime(fmt)


def sort_by(iterable, attribute, reverse=False):
    return sorted(iterable,
                  reverse=reverse,
                  key=lambda item: getattr(item, attribute) or 0)


def ui(key):
    return config.ui(key) if key else ''


@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(value)))
    return Markup(result) if eval_ctx.autoescape else result
