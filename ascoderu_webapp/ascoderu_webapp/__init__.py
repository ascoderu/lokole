from flask import Flask
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('config')

babel = Babel(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from ascoderu_webapp import views
from ascoderu_webapp import models
