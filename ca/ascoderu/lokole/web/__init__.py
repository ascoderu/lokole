from flask import Flask
from flask_babel import Babel

from ca.ascoderu.lokole.web.config import FlaskConfig
from ca.ascoderu.lokole.web.ioc import Ioc

app = Flask(__name__)
app.config.from_object(FlaskConfig)
app.ioc = Ioc()

Babel(app)

from ca.ascoderu.lokole.web import login
from ca.ascoderu.lokole.web import views
