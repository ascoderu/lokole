from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_security import current_user
from flask_security import login_required

from ascoderu_webapp import app
from ascoderu_webapp import babel
from ascoderu_webapp import models
from config import LANGUAGES


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


@app.route('/email')
@login_required
def email():
    return redirect(url_for('email_inbox'))


@app.route('/email/inbox')
@login_required
def email_inbox():
    emails = [mail for mail in models.Email.query.all()
              if current_user.email in mail.to]

    return render_template('email.html', emails=emails, is_outgoing=False)


@app.route('/email/outbox')
@login_required
def email_outbox():
    emails = [mail for mail in models.Email.query.all()
              if current_user.email == mail.sender and mail.date is None]

    return render_template('email.html', emails=emails, is_outgoing=True)


@app.route('/email/sent')
@login_required
def email_sent():
    emails = [mail for mail in models.Email.query.all()
              if current_user.email == mail.sender and mail.date is not None]

    return render_template('email.html', emails=emails, is_outgoing=True)
