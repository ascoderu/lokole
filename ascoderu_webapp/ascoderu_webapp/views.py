from datetime import datetime

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import gettext
from flask_security import current_user
from flask_security import login_required

from ascoderu_webapp import app
from ascoderu_webapp import babel
from ascoderu_webapp import db
from ascoderu_webapp.models import Email
from ascoderu_webapp.models import User
from config import LANGUAGES

from .forms import NewEmailForm


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.route('/')
def root():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/welcome')
@login_required
def welcome():
    user = current_user.name or current_user.email
    flash(gettext('Welcome, %(user)s', user=user), category='success')
    return redirect('/')


@app.route('/email')
@login_required
def email():
    return redirect(url_for('email_inbox'))


@app.route('/email/new', methods=['GET', 'POST'])
@login_required
def email_new():
    form = NewEmailForm(request.form)
    if form.validate_on_submit():
        is_to_local_user = User.exists(form.to.data)
        email_date = datetime.now() if is_to_local_user else None
        flashed_message = ('Email sent!' if is_to_local_user
                           else 'Email will be sent soon!')
        next_endpoint = 'email_sent' if is_to_local_user else 'email_outbox'

        db.session.add(Email(
            date=email_date,
            to=[form.to.data],
            sender=current_user.email or current_user.name,
            subject=form.subject.data,
            body=form.body.data))
        db.session.commit()
        flash(gettext(flashed_message), category='success')
        return redirect(url_for(next_endpoint))

    return render_template('email_new.html', form=form)


@app.route('/email/inbox')
@login_required
def email_inbox():
    emails = [mail for mail in Email.query.all()
              if current_user.email in mail.to or current_user.name in mail.to]

    return render_template('email.html', emails=emails, is_outgoing=False)


@app.route('/email/outbox')
@login_required
def email_outbox():
    emails = Email.query.filter(Email.date.is_(None) &
                                (Email.sender.is_(current_user.email) |
                                 Email.sender.is_(current_user.name)))

    return render_template('email.html', emails=emails, is_outgoing=True)


@app.route('/email/sent')
@login_required
def email_sent():
    emails = Email.query.filter(Email.date.isnot(None) &
                                (Email.sender.is_(current_user.email) |
                                 Email.sender.is_(current_user.name)))

    return render_template('email.html', emails=emails, is_outgoing=True)
