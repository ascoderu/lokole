from base64 import b64decode
from base64 import b64encode
from copy import deepcopy
from datetime import datetime
from datetime import timezone
from email.utils import mktime_tz
from email.utils import parsedate_tz
from io import BytesIO
from itertools import chain
from mimetypes import guess_type
from opwen_email_server import config
from typing import Iterable
from typing import List
from typing import Optional

from bs4 import BeautifulSoup
from PIL import Image
from pyzmail import PyzMessage
from pyzmail.parse import MailPart
from requests import Response
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


def format_attachments(email: dict) -> dict:
    attachments = email.get('attachments', [])

    if not attachments:
        return email

    formatted_attachments = deepcopy(attachments)
    is_any_attachment_changed = False

    for i, attachment in enumerate(attachments):
        filename = attachment.get('filename', '')
        content = attachment.get('content', '')
        formatted_content = _format_attachment(filename, content)

        if content != formatted_content:
            formatted_attachments[i]['content'] = formatted_content
            is_any_attachment_changed = True

    if not is_any_attachment_changed:
        return email

    new_email = dict(email)
    new_email['attachments'] = formatted_attachments
    return new_email


def _format_attachment(filename: str, content: str) -> str:
    guessed_type = guess_type(filename)[0]

    if not guessed_type:
        return content

    if 'image' in guessed_type.lower():
        image = _change_image_size(content)
        return image
    return content


def _get_recipients(email: dict) -> Iterable[str]:
    return chain(email.get('to') or [],
                 email.get('cc') or [],
                 email.get('bcc') or [])


def get_domains(email: dict) -> Iterable[str]:
    return frozenset(address.split('@')[-1]
                     for address in _get_recipients(email))


def _get_image_type(response: Response, url: str) -> Optional[str]:
    content_type = response.headers.get('Content-Type')
    if not content_type:
        content_type = guess_type(url)[0]
    return content_type


def _change_image_size(image_content_b64: str) -> str:
    image_content_bytes = b64decode(image_content_b64)
    image_bytes = BytesIO(image_content_bytes)
    image_bytes.seek(0)
    image = Image.open(image_bytes)
    image_format = image.format
    max_width = config.MAX_WIDTH_IMAGES
    max_height = config.MAX_HEIGHT_IMAGES
    img_size = (max_width, max_height)
    image.thumbnail(img_size, Image.ANTIALIAS)
    new_image = BytesIO()
    image.save(new_image, image_format)
    new_image.seek(0)
    new_image_bytes = new_image.read()
    new_b64 = b64encode(new_image_bytes).decode('ascii')
    return new_b64


def _fetch_image_to_base64(image_url: str) -> Optional[str]:
    response = requests.get(image_url)
    if not response.ok:
        return None

    image_type = _get_image_type(response, image_url)
    if not image_type:
        return None

    if not response.content:
        return None

    image_content = b64encode(response.content).decode('ascii')
    image_content = _change_image_size(image_content)
    base64 = 'data:{};base64,{}'.format(image_type, image_content)
    return base64


def format_inline_images(email: dict) -> dict:
    email_body = email.get('body', '')
    if not email_body:
        return email

    soup = BeautifulSoup(email_body, 'html.parser')
    image_tags = soup.find_all('img')
    if not image_tags:
        return email

    for image_tag in image_tags:
        image_url = image_tag.get('src')
        if not image_url:
            continue

        encoded_image = _fetch_image_to_base64(image_url)
        if encoded_image:
            image_tag['src'] = encoded_image

    new_email = dict(email)
    new_email['body'] = str(soup)
    return new_email
