from base64 import b64encode
from datetime import datetime
from datetime import timezone
from email.utils import mktime_tz
from email.utils import parsedate_tz
from itertools import chain
from mimetypes import guess_type
from typing import Any
from typing import Iterable
from typing import List
from typing import Optional

from bs4 import BeautifulSoup
from pyzmail import PyzMessage
from pyzmail.parse import MailPart
import requests


def _parse_body(message: PyzMessage, default_charset: str='ascii') -> str:
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


def _parse_attachments(mailparts: Iterable[MailPart]) -> Iterable[dict]:
    attachment_parts = (part for part in mailparts if not part.is_body)
    for part in attachment_parts:
        filename = part.sanitized_filename
        payload = part.get_payload()
        if filename and payload:
            content = b64encode(payload).decode('ascii')
            yield {'filename': filename, 'content': content}


def _parse_addresses(message: PyzMessage, address_type: str) -> List[str]:
    return [email for _, email in message.get_addresses(address_type) if email]


def _parse_address(message: PyzMessage, address_type: str) -> Optional[str]:
    return next(iter(_parse_addresses(message, address_type)), None)


def _parse_sent_at(message: PyzMessage) -> Optional[str]:
    rfc_822 = message.get_decoded_header('date')
    if not rfc_822:
        return None
    date_tz = parsedate_tz(rfc_822)
    if not date_tz:
        return None
    timestamp = mktime_tz(date_tz)
    # noinspection PyUnresolvedReferences
    date_utc = datetime.fromtimestamp(timestamp, timezone.utc)
    return date_utc.strftime('%Y-%m-%d %H:%M')


def parse_mime_email(mime_email: str) -> dict:
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


def _get_recipients(email: dict) -> Iterable[str]:
    return chain(email.get('to') or [],
                 email.get('cc') or [],
                 email.get('bcc') or [])


def get_domains(email: dict) -> Iterable[str]:
    return frozenset(address.split('@')[-1]
                     for address in _get_recipients(email))


def _get_image_type(response: Any, url: str) -> Optional[str]:
    content_type = response.headers.get('Content-Type')
    if not content_type:
        return guess_type(url)[0]
    return content_type


def _get_as_base64(image_url: str) -> Optional[str]:
    response = requests.get(image_url)

    if not response.ok:
        return None

    image_type = _get_image_type(response, image_url)
    image_content = b64encode(response.content).decode('ascii')

    if not image_type or not image_content:
        return None

    base64 = 'data:{};base64,{}'.format(image_type, image_content)
    return base64


def inline_images(email: dict) -> dict:
    email_body = email.get('body', '')

    if not email_body:
        return email

    soup = BeautifulSoup(email_body, 'html.parser')

    for img in soup.find_all('img'):
        img_url = img.get('src')

        if not img_url:
            continue

        img_base64 = _get_as_base64(img_url)

        if img_base64:
            img['src'] = img_base64

    new_email = dict(email)
    new_email['body'] = str(soup)
    return new_email
