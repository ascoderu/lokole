from datetime import datetime
from datetime import timezone
from tzlocal import get_localzone

import re

from jinja2 import Markup
from jinja2 import evalcontextfilter

from opwen_webapp import uploads
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
    return user and user.has_role(config.Config.ADMIN_ROLE)


def sort_by_date(iterable, reverse=False):
    """
    :type iterable: collections.Iterable[datetime]
    :type reverse: bool
    :rtype: list[datetime]

    """
    now = datetime.utcnow()
    return sorted(iterable,
                  reverse=reverse,
                  key=lambda item: item.date if item and item.date else now)


def attachment_url(filename):
    """
    :type filename: str
    :rtype: str

    """
    return uploads.url(filename) if filename else ''


def ui(key):
    """
    :type key: str
    :rtype: str

    """
    return config.ui(key.split('.')[-1]) if key else ''


@evalcontextfilter
def safe_multiline(eval_ctx, value):
    html = '\n\n'.join('<p>%s</p>' % paragraph.replace('\n', '<br>\n')
                       for paragraph in _paragraph_re.split(value))
    return Markup(html) if eval_ctx.autoescape else html
