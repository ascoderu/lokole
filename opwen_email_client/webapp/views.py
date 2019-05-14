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
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask_login import current_user

from opwen_email_client.util.pagination import Pagination
from opwen_email_client.webapp import app
from opwen_email_client.webapp import tasks
from opwen_email_client.webapp.actions import SendWelcomeEmail
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n
from opwen_email_client.webapp.forms.email import NewEmailForm
from opwen_email_client.webapp.forms.settings import SettingsForm
from opwen_email_client.webapp.ioc import Ioc
from opwen_email_client.webapp.login import User
from opwen_email_client.webapp.login import admin_required
from opwen_email_client.webapp.login import login_required
from opwen_email_client.webapp.session import Session
from opwen_email_client.webapp.session import track_history


@app.route('/favicon.ico')
def favicon() -> Response:
    return send_from_directory(
        directory=path.join(app.root_path, 'static'),
        filename='favicon.ico',
        mimetype='image/vnd.microsoft.icon')


@app.route('/')
@app.route('/home')
@track_history
def home() -> Response:
    return _view('home.html')


@app.route('/about')
@track_history
def about() -> Response:
    return _view('about.html')


@app.route('/news', defaults={'page': 1})
@app.route('/news/<int:page>')
@track_history
def news(page: int) -> Response:
    email_store = Ioc.email_store

    return _emails_view(email_store.inbox(AppConfig.NEWS_INBOX),
                        page, 'news.html')


@app.route('/email')
@app.route('/email/inbox', defaults={'page': 1})
@app.route('/email/inbox/<int:page>')
@login_required
@track_history
def email_inbox(page: int) -> Response:
    email_store = Ioc.email_store
    user = current_user

    return _emails_view(email_store.inbox(user.email), page)


@app.route('/email/outbox', defaults={'page': 1})
@app.route('/email/outbox/<int:page>')
@login_required
@track_history
def email_outbox(page: int) -> Response:
    email_store = Ioc.email_store
    user = current_user

    return _emails_view(email_store.outbox(user.email), page)


@app.route('/email/sent', defaults={'page': 1})
@app.route('/email/sent/<int:page>')
@login_required
@track_history
def email_sent(page: int) -> Response:
    email_store = Ioc.email_store
    user = current_user

    return _emails_view(email_store.sent(user.email), page)


@app.route('/email/search', defaults={'page': 1})
@app.route('/email/search/<int:page>')
@login_required
@track_history
def email_search(page: int) -> Response:
    email_store = Ioc.email_store
    user = current_user
    query = request.args.get('query')

    return _emails_view(email_store.search(user.email, query), page,
                        'email_search.html')


@app.route('/email/read/<email_uid>')
@login_required
def email_read(email_uid: str) -> Response:
    email_store = Ioc.email_store
    user = current_user

    email_store.mark_read(user.email, [email_uid])

    return Response('OK', status=200, mimetype='text/plain')


@app.route('/email/delete/<email_uid>')
@login_required
def email_delete(email_uid: str) -> Response:
    email_store = Ioc.email_store
    user = current_user

    email_store.delete(user.email, [email_uid])

    return redirect(Session.get_last_visited_url() or url_for('home'))


@app.route('/email/new', methods=['GET', 'POST'])
@login_required
@track_history
def email_new() -> Response:
    email_store = Ioc.email_store

    form = NewEmailForm.from_request(email_store)
    if form is None:
        return abort(404)

    if form.validate_on_submit():
        email_store.create([form.as_dict(email_store)])
        flash(i8n.EMAIL_SENT, category='success')
        return redirect(url_for('email_inbox'))

    return _view('email_new.html', form=form)


@app.route('/attachment/<uid>', methods=['GET'])
@login_required
def download_attachment(uid: str) -> Response:
    email_store = Ioc.email_store

    attachment = email_store.get_attachment(uid)
    if attachment is None:
        return abort(404)

    return send_file(BytesIO(attachment['content']),
                     attachment_filename=attachment['filename'],
                     as_attachment=True)


@app.route('/user/register/complete')
@login_required
def register_complete() -> Response:
    send_welcome_email = SendWelcomeEmail(
        time=datetime.utcnow(),
        to=current_user.email,
        email_store=Ioc.email_store)

    send_welcome_email()

    current_user.language = Session.get_current_language()
    current_user.save()

    flash(i8n.ACCOUNT_CREATED, category='success')
    return redirect(url_for('email_inbox'))


@app.route('/user/login/complete')
@login_required
def login_complete() -> Response:
    current_language = current_user.language
    if current_language:
        Session.store_current_language(current_language)

    flash(i8n.LOGGED_IN, category='success')
    return redirect(url_for('home'))


@app.route('/user/logout/complete')
def logout_complete() -> Response:
    flash(i8n.LOGGED_OUT, category='success')
    return redirect(url_for('home'))


@app.route('/admin/sync')
@admin_required
def sync() -> Response:
    tasks.sync.delay()

    flash(i8n.SYNC_RUNNING, category='success')
    return redirect(url_for('settings'))


@app.route('/admin/update', defaults={'version': None})
@app.route('/admin/update/<version>')
@admin_required
def update(version: Optional[str]) -> Response:
    tasks.update.delay(version)

    flash(i8n.UPDATE_RUNNING, category='success')
    return redirect(url_for('settings'))


@app.route('/user/language/<locale>')
def language(locale: str) -> Response:
    if current_user.is_authenticated:
        current_user.language = locale
        current_user.save()
    Session.store_current_language(locale)
    return redirect(Session.get_last_visited_url() or url_for('home'))


@app.route('/users')
@login_required
@track_history
def users() -> Response:
    return _view('users.html',
                 users=User.query.all())


@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
@track_history
def settings() -> Response:
    email_store = Ioc.email_store

    form = SettingsForm()
    if form.validate_on_submit():
        form.update()
        flash(i8n.SETTINGS_UPDATED, category='success')
        return redirect(url_for('settings'))

    return _view('settings.html',
                 form=SettingsForm.from_config(),
                 num_pending=email_store.num_pending())


@app.route('/admin/suspend/<userid>')
@admin_required
def suspend(userid: str) -> Response:
    user = User.query.filter_by(id=userid).first()

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    if user.is_admin:
        flash(i8n.ADMIN_CANNOT_BE_SUSPENDED, category='error')
        return redirect(url_for('users'))

    user.active = False
    user.save()

    flash(i8n.USER_SUSPENDED, category='success')
    return redirect(url_for('users'))


@app.route('/admin/unsuspend/<userid>')
@admin_required
def unsuspend(userid: str) -> Response:
    user = User.query.filter_by(id=userid).first()

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    user.active = True
    user.save()

    flash(i8n.USER_UNSUSPENDED, category='success')
    return redirect(url_for('users'))


@app.route('/admin/promote/<userid>')
@admin_required
def promote(userid: str) -> Response:
    user = User.query.filter_by(id=userid).first()

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    if user.is_admin:
        flash(i8n.ALREADY_PROMOTED, category='error')
        return redirect(url_for('users'))

    user.make_admin()
    user.save()

    flash(i8n.USER_PROMOTED, category='success')
    return redirect(url_for('users'))


@app.route('/admin/password/reset/<userid>')
@admin_required
def reset_password(userid: str) -> Response:
    user = User.query.filter_by(id=userid).first()

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('users'))

    if user.is_admin:
        flash(i8n.ADMIN_PASSWORD_CANNOT_BE_RESET, category='error')
        return redirect(url_for('users'))

    new_password = user.reset_password()
    user.save()

    flash(i8n.PASSWORD_CHANGED_BY_ADMIN + new_password, category='success')
    return redirect(url_for('users'))


# noinspection PyUnusedLocal
@app.errorhandler(404)
def _on_404(status_code: int) -> Response:
    app.logger.warning('404: %s', request.path)
    flash(i8n.PAGE_DOES_NOT_EXIST, category='error')
    return redirect(url_for('home'))


@app.errorhandler(Exception)
def _on_exception(exception: Exception) -> Response:
    app.logger.error('%s: %s', exception.__class__.__name__, exception)
    flash(i8n.UNEXPECTED_ERROR, category='error')
    return redirect(url_for('home'))


@app.errorhandler(500)
def _on_500(status_code: int) -> Response:
    app.logger.error(status_code)
    flash(i8n.UNEXPECTED_ERROR, category='error')
    return redirect(url_for('home'))


@app.context_processor
def _inject_locales() -> dict:
    return {
        'locales': AppConfig.LOCALES,
        'current_locale': Locale.parse(_localeselector()),
    }


@app.babel.localeselector
def _localeselector() -> str:
    current_language = Session.get_current_language()
    if not current_language and current_user.is_authenticated:
        current_language = current_user.language
    if not current_language:
        current_language = AppConfig.DEFAULT_LOCALE.language
    return current_language


def _emails_view(emails: Iterable[dict], page: int,
                 template: str = 'email.html') -> Response:
    offset_minutes = getattr(current_user, 'timezone_offset_minutes', 0)
    timezone_offset = timedelta(minutes=offset_minutes)

    if page < 1:
        return abort(404)

    emails = Pagination(emails, page, AppConfig.EMAILS_PER_PAGE)

    for email in emails:
        sent_at = email.get('sent_at')
        if sent_at:
            sent_at_utc = datetime.strptime(sent_at, '%Y-%m-%d %H:%M')
            sent_at_local = sent_at_utc - timezone_offset
            email['sent_at'] = sent_at_local.strftime('%Y-%m-%d %H:%M')

    return _view(template, emails=emails, page=page)


def _view(template: str, **kwargs) -> Response:
    return render_template(template, **kwargs)
