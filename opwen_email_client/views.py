import os
from datetime import datetime
from io import BytesIO

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask_login import current_user

from opwen_email_client import app
from opwen_email_client.actions import SendWelcomeEmail
from opwen_email_client.config import AppConfig
from opwen_email_client.config import i8n
from opwen_email_client.crons import emails_sync
from opwen_email_client.forms import NewEmailForm
from opwen_email_client.login import User
from opwen_email_client.login import admin_required
from opwen_email_client.login import login_required
from opwen_infrastructure.pagination import Pagination


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        directory=os.path.join(app.root_path, 'static'),
        filename='favicon.ico',
        mimetype='image/vnd.microsoft.icon')


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/email')
@app.route('/email/inbox', defaults={'page': 1})
@app.route('/email/inbox/<int:page>')
@login_required
def email_inbox(page):
    email_store = app.ioc.email_store
    user = current_user

    return _emails_view(email_store.inbox(user.email), page)


@app.route('/email/outbox', defaults={'page': 1})
@app.route('/email/outbox/<int:page>')
@login_required
def email_outbox(page):
    email_store = app.ioc.email_store
    user = current_user

    return _emails_view(email_store.outbox(user.email), page)


@app.route('/email/sent', defaults={'page': 1})
@app.route('/email/sent/<int:page>')
@login_required
def email_sent(page):
    email_store = app.ioc.email_store
    user = current_user

    return _emails_view(email_store.sent(user.email), page)


@app.route('/email/search', defaults={'page': 1})
@app.route('/email/search/<int:page>')
@login_required
def email_search(page):
    email_store = app.ioc.email_store
    user = current_user
    query = request.args.get('query')

    return _emails_view(email_store.search(user.email, query), page, 'email_search.html')


@app.route('/email/new', methods=['GET', 'POST'])
@login_required
def email_new():
    email_store = app.ioc.email_store
    attachment_encoder = app.ioc.attachment_encoder
    form = NewEmailForm.from_request()

    if form.validate_on_submit():
        email_store.create([form.as_dict(attachment_encoder)])
        flash(i8n.EMAIL_SENT, category='success')

    return render_template('email_new.html', form=form)


@app.route('/attachment/<attachment_id>', methods=['GET'])
@login_required
def download_attachment(attachment_id):
    attachments_session = app.ioc.attachments_session

    attachment = attachments_session.lookup(attachment_id)
    if attachment is None:
        abort(404)

    return send_file(BytesIO(attachment.content),
                     attachment_filename=attachment.name,
                     as_attachment=True)


@app.route('/register_complete')
@login_required
def register_complete():
    send_welcome_email = SendWelcomeEmail(
        time=datetime.utcnow(),
        to=current_user.email,
        email_store=app.ioc.email_store)

    send_welcome_email()

    current_user.last_login = datetime.now()
    current_user.save()

    flash(i8n.ACCOUNT_CREATED, category='success')
    return redirect(url_for('email_inbox'))


@app.route('/login_complete')
@login_required
def login_complete():
    current_user.last_login = datetime.now()
    current_user.save()

    flash(i8n.LOGGED_IN, category='success')
    return redirect(url_for('home'))


@app.route('/logout_complete')
def logout_complete():
    flash(i8n.LOGGED_OUT, category='success')
    return redirect(url_for('home'))


@app.route('/sync')
@admin_required
def sync():
    emails_sync()

    flash(i8n.SYNC_COMPLETE, category='success')
    return redirect(url_for('home'))


@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html', users=User.query.all())


@app.route('/admin/suspend/<userid>')
@admin_required
def suspend(userid):
    user = User.query.filter_by(id=userid).first()

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('admin'))

    user.active = False
    user.save()

    flash(i8n.USER_SUSPENDED, category='success')
    return redirect(url_for('admin'))


@app.route('/admin/unsuspend/<userid>')
@admin_required
def unsuspend(userid):
    user = User.query.filter_by(id=userid).first()

    if user is None:
        flash(i8n.USER_DOES_NOT_EXIST, category='error')
        return redirect(url_for('admin'))

    user.active = True
    user.save()

    flash(i8n.USER_UNSUSPENDED, category='success')
    return redirect(url_for('admin'))


@app.errorhandler(404)
def _on_404(code_or_exception):
    app.logger.error(code_or_exception)
    flash(i8n.PAGE_DOES_NOT_EXIST, category='error')
    return redirect(url_for('home'))


@app.errorhandler(Exception)
def _on_exception(code_or_exception):
    app.logger.error('%s: %s', code_or_exception.__class__.__name__, code_or_exception)
    flash(i8n.UNEXPECTED_ERROR, category='error')
    return redirect(url_for('home'))


@app.errorhandler(500)
def _on_500(code_or_exception):
    app.logger.error(code_or_exception)
    flash(i8n.UNEXPECTED_ERROR, category='error')
    return redirect(url_for('home'))


def _emails_view(emails, page, template='email.html'):
    """
    :type emails: collections.Iterable[dict]
    :type page: int
    :type template: str

    """
    attachments_session = app.ioc.attachments_session

    if page < 1:
        abort(404)

    emails = Pagination(emails, page, AppConfig.EMAILS_PER_PAGE)
    attachments_session.store(emails)
    return render_template(template, emails=emails, page=page)
