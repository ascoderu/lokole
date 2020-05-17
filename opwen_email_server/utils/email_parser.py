from copy import deepcopy
from datetime import datetime
from datetime import timezone
from email.utils import mktime_tz
from email.utils import parsedate_tz
from io import BytesIO
from itertools import chain
from mimetypes import guess_type
from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from bs4 import BeautifulSoup
from PIL import Image
from pyzmail import PyzMessage
from pyzmail.parse import MailPart
from requests import Response
from requests import get as http_get

from opwen_email_server.config import MAX_HEIGHT_IMAGES
from opwen_email_server.config import MAX_WIDTH_IMAGES
from opwen_email_server.constants import mailbox
from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import to_base64


def _parse_body(message: PyzMessage, default_charset: str = 'ascii') -> str:
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
        attachment_id = part.content_id
        if filename and payload:
            attachment = {'filename': filename, 'content': payload}
            if attachment_id:
                attachment['cid'] = attachment_id
            yield attachment


def _parse_addresses(message: PyzMessage, address_type: str) -> List[str]:
    return sorted(email for _, email in message.get_addresses(address_type) if email)


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
        content = attachment.get('content', b'')
        formatted_content = _format_attachment(filename, content)

        if content != formatted_content:
            formatted_attachments[i]['content'] = formatted_content
            is_any_attachment_changed = True

    if not is_any_attachment_changed:
        return email

    new_email = dict(email)
    new_email['attachments'] = formatted_attachments
    return new_email


def _format_attachment(filename: str, content: bytes) -> bytes:
    attachment_type = guess_type(filename)[0]

    if not attachment_type:
        return content

    if 'image' in attachment_type.lower():
        content = _change_image_size(content)

    return content


def get_recipients(email: dict) -> Iterable[str]:
    return chain(email.get('to') or [], email.get('cc') or [], email.get('bcc') or [])


def get_domains(email: dict) -> Iterable[str]:
    return frozenset(get_domain(address) for address in get_recipients(email))


def get_domain(address: str) -> str:
    return address.split('@')[-1]


def ensure_has_sent_at(email: dict):
    if not email.get('sent_at'):
        email['sent_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M')


def _get_image_type(response: Response, url: str) -> Optional[str]:
    content_type = response.headers.get('Content-Type')
    if not content_type:
        content_type = guess_type(url.split('?')[0])[0]
    return content_type


def _is_already_small(size: Tuple[int, int]) -> bool:
    width, height = size
    return width <= MAX_WIDTH_IMAGES and height <= MAX_HEIGHT_IMAGES


def _change_image_size(image_content_bytes: bytes) -> bytes:
    image_bytes = BytesIO(image_content_bytes)
    image_bytes.seek(0)
    image = Image.open(image_bytes)

    if _is_already_small(image.size):
        return image_content_bytes

    new_size = (MAX_WIDTH_IMAGES, MAX_HEIGHT_IMAGES)
    image.thumbnail(new_size, Image.ANTIALIAS)
    new_image = BytesIO()
    image.save(new_image, image.format)
    new_image.seek(0)
    new_image_bytes = new_image.read()
    return new_image_bytes


def _fetch_image_to_base64(image_url: str) -> Optional[str]:
    response = http_get(image_url)
    if not response.ok:
        return None

    image_type = _get_image_type(response, image_url)
    if not image_type:
        return None

    if not response.content:
        return None

    small_image_bytes = _change_image_size(response.content)
    small_image_base64 = to_base64(small_image_bytes)
    return f'data:{image_type};base64,{small_image_base64}'


def _is_valid_url(url: Optional[str]) -> bool:
    if not url:
        return False
    has_http_prefix = url.startswith('http://')
    has_https_prefix = url.startswith('https://')
    return has_http_prefix or has_https_prefix


def format_inline_images(email: dict, on_error: Callable) -> dict:
    email_body = email.get('body', '')
    if not email_body:
        return email

    soup = BeautifulSoup(email_body, 'html.parser')
    image_tags = soup.find_all('img')
    if not image_tags:
        return email

    for image_tag in image_tags:
        image_url = image_tag.get('src')

        if not _is_valid_url(image_url):
            continue

        try:
            encoded_image = _fetch_image_to_base64(image_url)
        except Exception as ex:
            on_error('Unable to inline image %s: %s', image_url, ex)
        else:
            if encoded_image:
                image_tag['src'] = encoded_image

    new_email = dict(email)
    new_email['body'] = str(soup)
    return new_email


def descending_timestamp(email_sent_at: str) -> str:
    return str(mailbox.FUTURE_TIMESTAMP - int(datetime.fromisoformat(email_sent_at).timestamp()))


class MimeEmailParser(LogMixin):
    def __call__(self, mime_email: str) -> dict:
        email = parse_mime_email(mime_email)
        email = format_attachments(email)
        email = format_inline_images(email, self.log_warning)
        return email
