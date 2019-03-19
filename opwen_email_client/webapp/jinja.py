from bs4 import BeautifulSoup
from flask import url_for

from opwen_email_client.webapp import app


@app.template_filter('render_body')
def render_body(email: dict) -> str:
    body = email.get('body')
    if not body:
        return ''

    body = body.replace('\n', '<br>')

    soup = BeautifulSoup(body, 'html.parser')
    images = soup.find_all('img')
    if not images:
        return body

    attachments = {attachment['cid']: attachment['_uid']
                   for attachment in email.get('attachments', [])}
    for img in images:
        src = img.get('src')
        if not src:
            continue
        if src.startswith('cid:'):
            attachment_cid = src[4:]
            attachment_id = attachments.get(attachment_cid)
            if attachment_id:
                src = url_for('download_attachment',
                              attachment_id=attachment_id)
        del img['src']
        img['data-original'] = src
    body = str(soup)

    return body
