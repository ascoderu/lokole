from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import url_for
from flask_security import current_user
from flask_security import login_required
from flask_security import roles_required

from config import Config
from config import ui
from opwen_webapp import app
from opwen_webapp import filters
from opwen_webapp.controllers import download_remote_updates
from opwen_webapp.controllers import find_attachment
from opwen_webapp.controllers import inbox_emails_for
from opwen_webapp.controllers import new_email_for
from opwen_webapp.controllers import outbox_emails_for
from opwen_webapp.controllers import sent_emails_for
from opwen_webapp.controllers import upload_local_updates
from opwen_webapp.forms import NewEmailForm
from utils.uploads import UploadNotAllowed

app.jinja_env.filters['is_admin'] = filters.is_admin
app.jinja_env.filters['render_date'] = filters.render_date
app.jinja_env.filters['safe_multiline'] = filters.safe_multiline
app.jinja_env.filters['sort_by_date'] = filters.sort_by_date
app.jinja_env.filters['ui'] = filters.ui


@app.route('/')
def root():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/post_register')
@login_required
def post_register():
    user = current_user.name or current_user.email
    flash(ui('welcome_user', user=user), category='success')
    return redirect(url_for('home'))


@app.route('/post_login')
@login_required
def post_login():
    user = current_user.name or current_user.email
    flash(ui('welcome_back_user', user=user), category='success')
    return redirect(url_for('home'))


@app.route('/post_logout')
def post_logout():
    flash(ui('loggedout_user'), category='success')
    return redirect(url_for('home'))


@app.route('/email')
@login_required
def email():
    return redirect(url_for('email_inbox'))


@app.route('/email/new', methods=['GET', 'POST'])
@login_required
def email_new():
    form = NewEmailForm(request.form)
    if form.validate_on_submit():
        try:
            is_to_local_user = new_email_for(
                current_user, form.to.data, form.subject.data, form.body.data,
                request.files.getlist(form.attachments.name))
        except UploadNotAllowed:
            flash(ui('upload_not_allowed'), category='error')
        else:
            message = 'email_done' if is_to_local_user else 'email_delayed'
            next_endpoint = 'email_sent' if is_to_local_user else 'email_outbox'

            flash(ui(message), category='success')
            return redirect(url_for(next_endpoint))

    return render_template('email_new.html', form=form)


@app.route('/email/inbox', defaults={'page': 1})
@app.route('/email/inbox/<int:page>')
@login_required
def email_inbox(page):
    emails = inbox_emails_for(current_user)
    emails = emails.paginate(page, Config.EMAILS_PER_PAGE)
    return render_template('email.html', emails=emails, is_outgoing=False)


@app.route('/email/outbox', defaults={'page': 1})
@app.route('/email/outbox/<int:page>')
@login_required
def email_outbox(page):
    emails = outbox_emails_for(current_user)
    emails = emails.paginate(page, Config.EMAILS_PER_PAGE)
    return render_template('email.html', emails=emails, is_outgoing=True)


@app.route('/email/sent', defaults={'page': 1})
@app.route('/email/sent/<int:page>')
@login_required
def email_sent(page):
    emails = sent_emails_for(current_user)
    emails = emails.paginate(page, Config.EMAILS_PER_PAGE)
    return render_template('email.html', emails=emails, is_outgoing=True)


@app.route('/sync')
@roles_required(Config.ADMIN_ROLE)
def sync():
    emails_uploaded = upload_local_updates()
    emails_downloaded = download_remote_updates()

    flash(ui('upload_complete', num=emails_uploaded), category='success')
    flash(ui('download_complete', num=emails_downloaded), category='success')
    return redirect(url_for('home'))


@app.route('/%s/<filename>' % Config.UPLOAD_ENDPOINT)
@login_required
def attachments(filename):
    attachment = find_attachment(current_user, filename)
    if not attachment:
        abort(404)

    return send_file(attachment.path,
                     as_attachment=True, attachment_filename=attachment.name)
