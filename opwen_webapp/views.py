from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import url_for
from flask_babel import gettext as _
from flask_security import current_user
from flask_security import login_required
from flask_security import roles_required

from config import Config
from opwen_webapp import app
from opwen_webapp.controllers import find_attachment
from opwen_webapp.controllers import inbox_emails_for
from opwen_webapp.controllers import new_email_for
from opwen_webapp.controllers import outbox_emails_for
from opwen_webapp.controllers import send_welcome_email
from opwen_webapp.controllers import sent_emails_for
from opwen_webapp.controllers import sync_with_remote
from opwen_webapp.helpers import filters
from opwen_webapp.helpers.forms import NewEmailForm
from utils.uploads import UploadNotAllowed

app.jinja_env.filters['is_admin'] = filters.is_admin
app.jinja_env.filters['render_date'] = filters.render_date
app.jinja_env.filters['safe_multiline'] = filters.safe_multiline
app.jinja_env.filters['sort_by_date'] = filters.sort_by_date
app.jinja_env.filters['ui'] = filters.ui
app.jinja_env.filters['lang2flag'] = filters.lang2flag
app.jinja_env.filters['lang2name'] = filters.lang2name


@app.route('/')
def root():
    return redirect(url_for('home'))


@app.route('/<lang_code>/home')
def home():
    return render_template('home.html')


@app.route('/<lang_code>/about')
def about():
    return render_template('about.html')


@app.route('/post_register')
@login_required
def post_register():
    send_welcome_email(current_user)
    user = current_user.name or current_user.email
    flash(_('Welcome, %(user)s!', user=user), category='success')
    return redirect(url_for('home'))


@app.route('/post_login')
@login_required
def post_login():
    user = current_user.name or current_user.email
    flash(_('Welcome back, %(user)s!', user=user), category='success')
    return redirect(url_for('home'))


@app.route('/post_logout')
def post_logout():
    flash(_('Logged out successfully!'), category='success')
    return redirect(url_for('home'))


@app.route('/<lang_code>/email')
@login_required
def email():
    return redirect(url_for('email_inbox'))


@app.route('/<lang_code>/email/new', methods=['GET', 'POST'])
@login_required
def email_new():
    form = NewEmailForm(request.form)

    to = request.args.get('to')
    subject = request.args.get('subject')
    if to:
        form.to.data = to
    if subject:
        form.subject.data = subject

    if form.validate_on_submit():
        try:
            is_to_local_user = new_email_for(
                current_user, form.to.data, form.subject.data, form.body.data,
                request.files.getlist(form.attachments.name))
        except UploadNotAllowed:
            flash(_('Only texts, images, documents and so forth are allowed as attachments.'), category='error')
        else:
            if is_to_local_user:
                message = _('Email sent!')
                next_endpoint = 'email_sent'
            else:
                message = _('Email will be sent soon!')
                next_endpoint = 'email_delayed'

            flash(message, category='success')
            return redirect(url_for(next_endpoint))

    return render_template('email_new.html', form=form)


@app.route('/<lang_code>/email/inbox', defaults={'page': 1})
@app.route('/<lang_code>/email/inbox/<int:page>')
@login_required
def email_inbox(page):
    emails = inbox_emails_for(current_user)
    emails = emails.paginate(page, Config.EMAILS_PER_PAGE)
    return render_template('email.html', emails=emails)


@app.route('/<lang_code>/email/outbox', defaults={'page': 1})
@app.route('/<lang_code>/email/outbox/<int:page>')
@login_required
def email_outbox(page):
    emails = outbox_emails_for(current_user)
    emails = emails.paginate(page, Config.EMAILS_PER_PAGE)
    return render_template('email.html', emails=emails)


@app.route('/<lang_code>/email/sent', defaults={'page': 1})
@app.route('/<lang_code>/email/sent/<int:page>')
@login_required
def email_sent(page):
    emails = sent_emails_for(current_user)
    emails = emails.paginate(page, Config.EMAILS_PER_PAGE)
    return render_template('email.html', emails=emails)


@app.route('/sync')
@roles_required(Config.ADMIN_ROLE)
def sync():
    sync_report = sync_with_remote(Config.INTERNET_INTERFACE_NAME)

    flash(_('Uploaded %(num)d emails.', num=sync_report.emails_uploaded), category='success')
    flash(_('Downloaded %(num)d emails.', num=sync_report.emails_downloaded), category='success')
    return redirect(url_for('home'))


@app.route('/%s/<filename>' % Config.UPLOAD_ENDPOINT)
@login_required
def attachments(filename):
    attachment = find_attachment(current_user, filename)
    if not attachment:
        abort(404)

    return send_file(attachment.path,
                     as_attachment=True, attachment_filename=attachment.name)
