import os
from datetime import datetime
from io import BytesIO

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_login import current_user
from opwen_domain.config import OpwenConfig
from opwen_infrastructure.logging import log_execution
from opwen_infrastructure.networking import use_network_interface
from opwen_infrastructure.pagination import Pagination

from opwen_email_client import app
from opwen_email_client.config import i8n
from opwen_email_client.forms import NewEmailForm
from opwen_email_client.login import admin_required
from opwen_email_client.login import login_required


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
        email_store.create(form.as_dict(attachment_encoder))
        flash(i8n.EMAIL_SENT, category='success')

    return render_template('email_new.html', form=form)


@app.route('/attachment/<attachment_id>', methods=['GET'])
@login_required
def download_attachment(attachment_id):
    attachment_encoder = app.ioc.attachment_encoder

    filename_content = session.get('attachment_{}'.format(attachment_id))

    if not filename_content:
        abort(404)

    filename = filename_content[0]
    content = BytesIO(attachment_encoder.decode(filename_content[1]))
    return send_file(content, attachment_filename=filename, as_attachment=True)


@app.route('/register_complete')
@login_required
def register_complete():
    email_store = app.ioc.email_store
    user = current_user

    email_store.create({
        'sent_at': datetime.utcnow(),
        'to': [user.email],
        'from': i8n.LOKOLE_TEAM,
        'subject': i8n.WELCOME,
        'body': render_template('_account_finalized.html', email=user.email),
    })

    flash(i8n.ACCOUNT_CREATED, category='success')
    return redirect(url_for('email_inbox'))


@app.route('/login_complete')
@login_required
def login_complete():
    flash(i8n.LOGGED_IN, category='success')
    return redirect(url_for('home'))


@app.route('/logout_complete')
def logout_complete():
    flash(i8n.LOGGED_OUT, category='success')
    return redirect(url_for('home'))


@app.route('/sync')
@admin_required
def sync():
    _emails_sync()

    flash(i8n.SYNC_COMPLETE, category='success')
    return redirect(url_for('home'))


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
def _on_exception(code_or_exception):
    app.logger.error(code_or_exception)
    flash(i8n.UNEXPECTED_ERROR, category='error')
    return redirect(url_for('home'))


@app.before_first_request
def _setup_email_sync_cron():
    cron_trigger_hour_utc = app.config['EMAIL_SYNC_HOUR_UTC']

    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=_emails_sync,
        id=_emails_sync.__name__,
        replace_existing=True,
        name='Sync Opwen emails at {} UTC'.format(cron_trigger_hour_utc),
        trigger=CronTrigger(hour=cron_trigger_hour_utc, timezone='utc'))


@log_execution(app.logger)
def _emails_sync():
    email_sync = app.ioc.email_sync
    email_store = app.ioc.email_store

    with use_network_interface(OpwenConfig.INTERNET_INTERFACE_NAME):
        email_sync.upload(email_store.pending())
        email_store.create(email_sync.download())


def _emails_view(emails, page, template='email.html'):
    """
    :type emails: collections.Iterable[dict]
    :type page: int
    :type template: str

    """
    if page < 1:
        abort(404)

    emails = Pagination(emails, page, app.config['EMAILS_PER_PAGE'])
    _store_attachments_in_session(emails)
    return render_template(template, emails=emails, page=page)


def _store_attachments_in_session(emails):
    """
    :type emails: collections.Iterable[dict]

    """
    for i, email in enumerate(emails):
        attachments = email.get('attachments', [])
        for j, attachment in enumerate(attachments):
            attachment_id = '{}{}'.format(i, j)
            session_data = attachment.get('filename'), attachment.get('content')
            session['attachment_{}'.format(attachment_id)] = session_data
            attachment['id'] = attachment_id
