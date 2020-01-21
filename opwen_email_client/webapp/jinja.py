from datetime import timedelta
from os.path import splitext

from bs4 import BeautifulSoup
from flask import url_for

from opwen_email_client.webapp import app


@app.template_filter('asset_url')
def asset_url(asset_path: str) -> str:
    if app.config['TESTING']:
        return url_for('static', filename=asset_path)

    asset_path, extension = splitext(asset_path)
    return url_for('static', filename='{}.min{}'.format(asset_path, extension))


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

    attachments = {attachment['cid']: attachment['_uid'] for attachment in email.get('attachments', [])}
    for img in images:
        src = img.get('src')
        if not src:
            continue
        if src.startswith('cid:'):
            attachment_cid = src[4:]
            attachment_id = attachments.get(attachment_cid)
            if attachment_id:
                src = url_for('download_attachment', email_id=email['_uid'], attachment_id=attachment_id)
        del img['src']
        img['data-original'] = src
    body = str(soup)

    return body


@app.context_processor
def _inject_format_last_login():
    def format_last_login(user, current_user) -> str:
        if not user.last_login_at:
            return ''

        date = user.last_login_at - timedelta(minutes=current_user.timezone_offset_minutes)
        return date.strftime('%Y-%m-%d %H:%M')

    return {'format_last_login': format_last_login}
