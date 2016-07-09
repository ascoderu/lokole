from flask import Flask
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security
from flask_security import SQLAlchemyUserDatastore

app = Flask(__name__)
app.config.from_object('config')

babel = Babel(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
