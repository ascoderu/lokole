from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ascoderu_webapp import app
from ascoderu_webapp import babel
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
