from os import path

from flask import Flask
from flask import flash
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_babel import Babel
from flask_migrate import Migrate
from flask_security import SQLAlchemyUserDatastore
from flask_security import Security
from flask_security.registerable import register_user
from flask_sqlalchemy import SQLAlchemy
from humanize import naturalsize
from werkzeug.utils import redirect

from config import Config
from config import LANGUAGES
from config import ui
from utils.factory import DynamicFactory
from utils.uploads import Uploads

app = Flask(__name__)
app.config.from_object(Config)

babel = Babel(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

uploads = Uploads(app)

from utils import jinja_filters

app.jinja_env.filters['safe_multiline'] = jinja_filters.safe_multiline
app.jinja_env.filters['render_date'] = jinja_filters.render_date
app.jinja_env.filters['sort_by_date'] = jinja_filters.sort_by_date
app.jinja_env.filters['ui'] = jinja_filters.ui
app.jinja_env.filters['is_admin'] = jinja_filters.is_admin
app.jinja_env.filters['attachment_url'] = jinja_filters.attachment_url

from opwen_webapp import views
from opwen_webapp import models
from opwen_webapp import forms

app.remote_serializer = DynamicFactory(Config.REMOTE_SERIALIZATION_CLASS)()
app.remote_packer = DynamicFactory(Config.REMOTE_PACKER_CLASS)()
app.remote_storage = DynamicFactory(Config.REMOTE_STORAGE_CLASS)(
    account_name=Config.REMOTE_STORAGE_ACCOUNT_NAME,
    account_key=Config.REMOTE_STORAGE_ACCOUNT_KEY,
    container=Config.REMOTE_STORAGE_CONTAINER,
    upload_path=Config.REMOTE_UPLOAD_PATH,
    download_path=Config.REMOTE_DOWNLOAD_PATH,
    upload_format=Config.REMOTE_UPLOAD_FORMAT)

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore,
                    login_form=forms.LoginForm,
                    register_form=forms.RegisterForm)


@babel.localeselector
def _get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.before_first_request
def _create_admin():
    admin = user_datastore.find_user(name=Config.ADMIN_NAME)
    if not admin:
        is_admin = user_datastore.find_or_create_role(Config.ADMIN_ROLE)
        register_user(name=Config.ADMIN_NAME, password=Config.ADMIN_PASSWORD,
                      roles=[is_admin])
        db.session.commit()


@app.after_request
def _store_visited_url(response):
    session['previous_url'] = request.url
    return response


# noinspection PyUnusedLocal
@app.errorhandler(404)
def _on_404(code_or_exception):
    flash(ui('page_not_found', url=request.url), category='error')
    return redirect(session.get('previous_url') or url_for('home'))


# noinspection PyUnusedLocal
@app.errorhandler(413)
def _on_413(code_or_exception):
    max_size = naturalsize(Config.MAX_CONTENT_LENGTH)
    flash(ui('attachment_too_large', max_size=max_size), category='error')
    return redirect(session.get('previous_url') or url_for('home'))


@app.route('/favicon.ico')
def _favicon():
    return send_from_directory(path.join(app.root_path, 'satic'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')
