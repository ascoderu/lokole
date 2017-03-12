from base64 import b64encode
from datetime import datetime
from email.utils import mktime_tz
from email.utils import parsedate_tz
from itertools import chain

from pytz import utc
from pyzmail import PyzMessage


def _parse_body(message, default_charset='ascii'):
    """
    :type message: pyzmail.PyzMessage
    :type default_charset: str
    :rtype: str

    """
    body_parts = (message.html_part, message.text_part)
    for part in body_parts:
        if part is None:
            continue
        payload = part.get_payload()
        if payload is None:
            continue
        charset = part.charset or default_charset
        return payload.decode(charset, errors='replace')
    return ''


def _parse_attachments(mailparts):
    """
    :type mailparts: collections.Iterable[pyzmail.parse.MailPart]
    :rtype: collections.Iterable[dict]

    """
    attachment_parts = (part for part in mailparts if not part.is_body)
    for part in attachment_parts:
        filename = part.sanitized_filename
        payload = part.get_payload()
        if filename and payload:
            content = b64encode(payload).decode('ascii')
            yield {'filename': filename, 'content': content}


def _parse_addresses(message, address_type):
    """
    :type message: pyzmail.PyzMessage
    :type address_type: str
    :rtype: list[str]

    """
    return [email for _, email in message.get_addresses(address_type) if email]


def _parse_address(message, address_type):
    """
    :type message: pyzmail.PyzMessage
    :type address_type: str
    :rtype: str|None

    """
    return next(iter(_parse_addresses(message, address_type)), None)


def _parse_sent_at(message):
    """
    :type message: pyzmail.PyzMessage
    :rtype: str

    """
    rfc_822 = message.get_decoded_header('date')
    timestamp = mktime_tz(parsedate_tz(rfc_822))
    date_utc = datetime.fromtimestamp(timestamp, utc)
    return date_utc.strftime('%Y-%m-%d %H:%M')


def parse_mime_email(mime_email):
    """
    :type mime_email: str
    :rtype: dict

    """
    message = PyzMessage.factory(mime_email)

    return {
        'sent_at': _parse_sent_at(message),
        'to': _parse_addresses(message, 'to'),
        'cc': _parse_addresses(message, 'cc'),
        'bcc': _parse_addresses(message, 'bcc'),
        'from': _parse_address(message, 'from'),
        'subject': message.get_subject(),
        'body': _parse_body(message),
        'attachments': list(_parse_attachments(message.mailparts)),
    }


def _get_recipients(email):
    """
    :type email: dict
    :rtype: collections.Iterable[str]

    """
    return chain(email.get('to') or [],
                 email.get('cc') or [],
                 email.get('bcc') or [])


def get_domains(email):
    """
    :type email: dict
    :rtype: collections.Iterable[str]

    """
    return frozenset(address.split('@')[-1]
                     for address in _get_recipients(email))
