from datetime import datetime
from datetime import timedelta
from io import BytesIO
from os import path
from typing import Iterable
from typing import Optional

from babel import Locale
from flask import Response
from flask import abort
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask_cors import cross_origin
from flask_login import current_user
from flask_security.utils import hash_password
from passlib.pwd import genword

from opwen_email_client.webapp import app
from opwen_email_client.webapp import tasks
from opwen_email_client.webapp.actions import SendWelcomeEmail
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n
from opwen_email_client.webapp.forms.email import NewEmailForm
from opwen_email_client.webapp.forms.settings import SettingsForm
from opwen_email_client.webapp.security import login_required
from opwen_email_client.webapp.session import Session
from opwen_email_client.webapp.session import track_history


@app.route(AppConfig.APP_ROOT + '/favicon.ico')
def favicon() -> Response:
    return send_from_directory(
        directory=path.join(app.root_path, 'static'),
        filename='favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )


@app.route(AppConfig.APP_ROOT + '/')
@app.route(AppConfig.APP_ROOT + '/home')
@track_history
def home() -> Response:
    return _view('home.html')


@app.route(AppConfig.APP_ROOT + '/about')
@track_history
def about() -> Response:
    return _view('about.html')


@app.route(AppConfig.APP_ROOT + '/news', defaults={'page': 1})
@app.route(AppConfig.APP_ROOT + '/news/<int:page>')
@track_history
def news(page: int) -> Response:
    email_store = app.ioc.email_store

    return _emails_view(email_store.inbox(AppConfig.NEWS_INBOX, page), page, 'news.html')


@app.route(AppConfig.APP_ROOT + '/email')
@app.route(AppConfig.APP_ROOT + '/email/inbox', defaults={'page': 1})
@app.route(AppConfig.APP_ROOT + '/email/inbox/<int:page>')
@login_required
@track_history
def email_inbox(page: int) -> Response:
    email_store = app.ioc.email_store
    user = current_user

    return _emails_view(email_store.inbox(user.email, page), page, type='inbox')


@app.route(AppConfig.APP_ROOT + '/email/outbox', defaults={'page': 1})
@app.route(AppConfig.APP_ROOT + '/email/outbox/<int:page>')
@login_required
@track_history
def email_outbox(page: int) -> Response:
    email_store = app.ioc.email_store
    user = current_user

    return _emails_view(email_store.outbox(user.email, page), page, type='outbox')


@app.route(AppConfig.APP_ROOT + '/email/sent', defaults={'page': 1})
@app.route(AppConfig.APP_ROOT + '/email/sent/<int:page>')
@login_required
@track_history
def email_sent(page: int) -> Response:
    email_store = app.ioc.email_store
    user = current_user

    return _emails_view(email_store.sent(user.email, page), page, type='sent')


@app.route(AppConfig.APP_ROOT + '/email/search', defaults={'page': 1})
@app.route(AppConfig.APP_ROOT + '/email/search/<int:page>')
@login_required
@track_history
def email_search(page: int) -> Response:
    if not AppConfig.EMAIL_SEARCHABLE:
        return abort(404)

    email_store = app.ioc.email_store
    user = current_user
    query = request.args.get('query')

    return _emails_view(email_store.search(user.email, page, query), page, 'email_search.html', type='search')


@app.route(AppConfig.APP_ROOT + '/email/unread')
@login_required
def email_unread() -> Response:
    email_store = app.ioc.email_store
    user = current_user

    return jsonify(unread=email_store.has_unread(user.email))


@app.route(AppConfig.APP_ROOT + '/email/read/<email_uid>')
@login_required
def email_read(email_uid: str) -> Response:
    email_store = app.ioc.email_store
    user = current_user

    email_store.mark_read(user.email, [email_uid])

    return Response('OK', status=200, mimetype='text/plain')


@app.route(AppConfig.APP_ROOT + '/email/delete/<email_uid>')
@login_required
def email_delete(email_uid: str) -> Response:
    email_store = app.ioc.email_store
    user = current_user

    email_store.delete(user.email, [email_uid])

    return redirect(Session.get_last_visited_url() or url_for('home'))


@app.route(AppConfig.APP_ROOT + '/email/new', methods=['GET', 'POST'])
@login_required
@track_history
def email_new() -> Response:
    email_store = app.ioc.email_store

    form = NewEmailForm.from_request(email_store)
    if form is None:
        return abort(404)

    if form.validate_on_submit():
        email_store.create([form.as_dict(email_store)])
        flash(i8n.EMAIL_SENT, category='success')
        return redirect(url_for('email_inbox'))

    return _view('email_new.html', max_upload_size_mb=AppConfig.MAX_UPLOAD_SIZE_MB, form=form, type='write')


@app.route(AppConfig.APP_ROOT + '/attachment/<email_id>/<attachment_id>', methods=['GET'])
@login_required
def download_attachment(email_id: str, attachment_id: str) -> Response:
    email_store = app.ioc.email_store

    attachment = email_store.get_attachment(email_id, attachment_id)
    if attachment is None:
        return abort(404)

    return send_file(
        BytesIO(attachment['content']),
        attachment_filename=attachment['filename'],
        as_attachment=True,
    )


@app.route(AppConfig.APP_ROOT + '/user/register/complete')
@login_required
def register_complete() -> Response:
    user_store = app.ioc.user_store

    send_welcome_email = SendWelcomeEmail(
        time=datetime.utcnow(),
        to=current_user.email,
        email_store=app.ioc.email_store,
    )

    send_welcome_email()

    current_user.language = Session.get_current_language()
    user_store.w.put(current_user)
    user_store.w.commit()

    flash(i8n.ACCOUNT_CREATED, category='success')
    return redirect(url_for('email_inbox'))


@app.route(AppConfig.APP_ROOT + '/user/login/complete')
@login_required
def login_complete() -> Response:
    current_language = current_user.language
    if current_language:
        Session.store_current_language(current_language)

    flash(i8n.LOGGED_IN, category='success')
    return redirect(url_for('home'))


@app.route(AppConfig.APP_ROOT + '/user/logout/complete')
def logout_complete() -> Response:
    flash(i8n.LOGGED_OUT, category='success')
    return redirect(url_for('home'))


@app.route(AppConfig.APP_ROOT + '/admin/sync')
def sync() -> Response:
    if not current_user.is_admin:
        abort(403)

    tasks.sync.delay()

    flash(i8n.SYNC_RUNNING, category='success')
    return redirect(url_for('settings'))


@app.route(AppConfig.APP_ROOT + '/admin/update', defaults={'version': None})
@app.route(AppConfig.APP_ROOT + '/admin/update/<version>')
def update(version: Optional[str]) -> Response:
    if not current_user.is_admin:
        abort(403)

    tasks.update.delay(version=version)

    flash(i8n.UPDATE_RUNNING, category='success')
    return redirect(url_for('settings'))


@app.route(AppConfig.APP_ROOT + '/user/language/<locale>')
def language(locale: str) -> Response:
    user_store = app.ioc.user_store

    if current_user.is_authenticated:
        current_user.language = locale
        user_store.w.put(current_user)
        user_store.w.commit()

    Session.store_current_language(locale)
    return redirect(Session.get_last_visited_url() or url_for('home'))


@app.route(AppConfig.APP_ROOT + '/users')
@login_required
@track_history
def users() -> Response:
    user_store = app.ioc.user_store

    return _view('users.html', users=user_store.fetch_all(current_user))


@app.route(AppConfig.APP_ROOT + '/admin/settings', methods=['GET', 'POST'])
@track_history
def settings() -> Response:
    if not current_user.is_admin:
        abort(403)

    email_store = app.ioc.email_store

    form = SettingsForm()
    if form.validate_on_submit():
        form.update()
        flash(i8n.SETTINGS_UPDATED, category='success')
        return redirect(url_for('settings'))

    return _view('settings.html', form=SettingsForm.from_config(), num_pending=email_store.num_pending())


@app.route(AppConfig.APP_ROOT + '/admin/suspend/<userid>')
def suspend(userid: str) -> Response:
    if not current_user.is_admin:
        abort(403)

    user_store = app.ioc.user_store

    user = user_store.r.find_user(id=userid)

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    if user.is_admin:
        flash(i8n.ADMIN_CANNOT_BE_SUSPENDED, category='error')
        return redirect(url_for('users'))

    user.active = False
    user_store.w.put(user)
    user_store.w.commit()

    flash(i8n.USER_SUSPENDED, category='success')
    return redirect(url_for('users'))


@app.route(AppConfig.APP_ROOT + '/admin/unsuspend/<userid>')
def unsuspend(userid: str) -> Response:
    if not current_user.is_admin:
        abort(403)

    user_store = app.ioc.user_store

    user = user_store.r.find_user(id=userid)

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    user.active = True
    user_store.w.put(user)
    user_store.w.commit()

    flash(i8n.USER_UNSUSPENDED, category='success')
    return redirect(url_for('users'))


@app.route(AppConfig.APP_ROOT + '/admin/promote/<userid>')
def promote(userid: str) -> Response:
    if not current_user.is_admin:
        abort(403)

    user_store = app.ioc.user_store

    user = user_store.r.find_user(id=userid)

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    if user.is_admin:
        flash(i8n.ALREADY_PROMOTED, category='error')
        return redirect(url_for('users'))

    user.is_admin = True
    user_store.w.put(user)
    user_store.w.commit()

    flash(i8n.USER_PROMOTED, category='success')
    return redirect(url_for('users'))


@app.route(AppConfig.APP_ROOT + '/admin/password/reset/<userid>')
def reset_password(userid: str) -> Response:
    if not current_user.is_admin:
        abort(403)

    user_store = app.ioc.user_store

    user = user_store.r.find_user(id=userid)

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    if user.is_admin:
        flash(i8n.ADMIN_PASSWORD_CANNOT_BE_RESET, category='error')
        return redirect(url_for('users'))

    new_password = genword()
    user.password = hash_password(new_password)
    user_store.w.put(user)
    user_store.w.commit()

    flash(i8n.PASSWORD_CHANGED_BY_ADMIN + new_password, category='success')
    return redirect(url_for('users'))


@app.route(AppConfig.APP_ROOT + '/healthcheck/ping')
@cross_origin()
def ping() -> Response:
    return jsonify('OK')


# noinspection PyUnusedLocal
@app.errorhandler(404)
def _on_404(status_code: int) -> Response:
    app.logger.warning('404: %s', request.path)
    flash(i8n.PAGE_DOES_NOT_EXIST, category='error')
    return redirect(url_for('home'))


@app.errorhandler(Exception)
def _on_exception(exception: Exception) -> Response:
    try:
        raise exception
    except Exception:
        app.logger.exception('Unhandled exception!')
    flash(i8n.UNEXPECTED_ERROR, category='error')
    return redirect(url_for('home'))


@app.errorhandler(500)
def _on_500(status_code: int) -> Response:
    app.logger.error(status_code)
    flash(i8n.UNEXPECTED_ERROR, category='error')
    return redirect(url_for('home'))


@app.context_processor
def _inject_config() -> dict:
    return {
        'locales': AppConfig.LOCALES,
        'current_locale': Locale.parse(_localeselector()),
        'local_only': AppConfig.SIM_TYPE == 'LocalOnly',
        'app_root': AppConfig.APP_ROOT,
        'can_change_password': AppConfig.SECURITY_CHANGEABLE,
        'can_register_user': AppConfig.SECURITY_REGISTERABLE,
        'can_search_email': AppConfig.EMAIL_SEARCHABLE,
    }


@app.babel.localeselector
def _localeselector() -> str:
    current_language = Session.get_current_language()
    if not current_language and current_user.is_authenticated:
        current_language = current_user.language
    if not current_language:
        current_language = AppConfig.DEFAULT_LOCALE.language
    return current_language


def _emails_view(emails: Iterable[dict], page: int, template: str = 'email.html', **kwargs) -> Response:
    offset_minutes = getattr(current_user, 'timezone_offset_minutes', None) or 0
    timezone_offset = timedelta(minutes=offset_minutes)

    emails = list(emails)

    for email in emails:
        sent_at = email.get('sent_at')
        if sent_at:
            sent_at_utc = datetime.strptime(sent_at, '%Y-%m-%d %H:%M')
            sent_at_local = sent_at_utc - timezone_offset
            email['sent_at'] = sent_at_local.strftime('%Y-%m-%d %H:%M')

    return _view(template,
                 emails=emails,
                 page=page,
                 has_prevpage=page > 1,
                 has_nextpage=len(emails) == AppConfig.EMAILS_PER_PAGE,
                 **kwargs)


def _view(template: str, **kwargs) -> Response:
    return render_template(template, **kwargs)
