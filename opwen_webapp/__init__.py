from flask import Flask
from flask_babel import Babel
from flask_migrate import Migrate
from flask_security import SQLAlchemyUserDatastore
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy

from config import Config
from opwen_webapp.helpers.logging import create_logging_handler
from utils.compressor import ZipCompressor
from utils.fileformatter import JsonLines
from utils.remotestorage import AzureBlob
from utils.uploads import Uploads

app = Flask(__name__)
app.config.from_object(Config)

babel = Babel(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

uploads = Uploads(app)

app.logger.addHandler(create_logging_handler())

from opwen_webapp import views
from opwen_webapp import models
from opwen_webapp.helpers import forms

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore,
                    login_form=forms.LoginForm,
                    register_form=forms.RegisterForm)

from opwen_webapp.helpers.serializers import Serializer

serializer = Serializer(JsonLines, ZipCompressor, app)
remote_storage = AzureBlob(app)

from opwen_webapp.helpers import handlers
