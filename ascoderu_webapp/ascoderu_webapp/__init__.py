from flask import Flask
from flask_babel import Babel

app = Flask(__name__)
app.config.from_object('config')

babel = Babel(app)

from ascoderu_webapp import views
