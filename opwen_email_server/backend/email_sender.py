from typing import Tuple

from opwen_email_server import config
from opwen_email_server.services.sendgrid import SendgridEmailSender

EMAIL = SendgridEmailSender(key=config.EMAIL_SENDER_KEY)


def send(email: dict) -> Tuple[str, int]:
    success = EMAIL.send_email(email)

    if not success:
        return 'error', 500

    return 'sent', 200


if __name__ == '__main__':
    from argparse import ArgumentParser
    from argparse import FileType
    from base64 import b64encode
    from json import loads
    from os.path import basename
    from uuid import uuid4

    parser = ArgumentParser()
    parser.add_argument('email')
    parser.add_argument('--attachment', type=FileType('rb'))
    args = parser.parse_args()

    email = loads(args.email)
    email.setdefault('_uid', str(uuid4()))

    if args.attachment:
        email.setdefault('attachments', []).append({
            'filename': basename(args.attachment.name),
            'content': b64encode(args.attachment.read()).decode('ascii')
        })
        args.attachment.close()

    send(email)
