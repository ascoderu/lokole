from base64 import b64encode

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


def parse_mime_email(mime_email):
    """
    :type mime_email: str
    :rtype: dict

    """
    message = PyzMessage.factory(mime_email)

    return {
        'sent_at': message.get_decoded_header('date'),
        'to': [email for _, email in message.get_addresses('to') if email],
        'cc': [email for _, email in message.get_addresses('cc') if email],
        'bcc': [email for _, email in message.get_addresses('bcc') if email],
        'from': message.get_address('from')[-1],
        'subject': message.get_subject(),
        'body': _parse_body(message),
        'attachments': list(_parse_attachments(message.mailparts)),
    }
