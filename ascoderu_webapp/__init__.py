from flask import Flask
from flask_babel import Babel
from flask_migrate import Migrate
from flask_security import SQLAlchemyUserDatastore
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy

from utils import jinja_filters

app = Flask(__name__)
app.config.from_object('config.Config')

babel = Babel(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.jinja_env.filters['nl2br'] = jinja_filters.nl2br
app.jinja_env.filters['render_date'] = jinja_filters.render_date
app.jinja_env.filters['sort_by'] = jinja_filters.sort_by

from ascoderu_webapp import views
from ascoderu_webapp import models
from ascoderu_webapp import forms

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore,
                    login_form=forms.LoginForm,
                    register_form=forms.RegisterForm)


@app.before_first_request
def create_user():
    if not models.User.query.filter_by(name='test').first():
        user_datastore.create_user(name='test', password='test')
        db.session.commit()
    if not models.User.query.filter_by(email='test@test.net').first():
        user_datastore.create_user(email='test@test.net', password='test')
        db.session.commit()

    if not models.Email.query.all():
        from datetime import datetime
        for i in range(1, 6):
            inbound_email = models.Email(
                date=datetime.now(), sender='sender@sender.net',
                to=['test@test.net', 'foo@bar.com'],
                subject='cool email %s' % i, body='the message\n' * i)
            outbound_email = models.Email(
                sender='test@test.net',
                to=['sender@sender.net', 'foo@bar.com'],
                subject='cool reply %s' % i, body='the reply\n' * i)
            sent_email = models.Email(
                date=datetime.now(), sender='test@test.net',
                to=['sender@sender.net', 'foo@bar.com'],
                subject='cool reply %s' % i, body='the reply\n' * i)
            db.session.add(inbound_email)
            db.session.add(outbound_email)
            db.session.add(sent_email)
        db.session.commit()
