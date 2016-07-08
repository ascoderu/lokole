from flask import render_template

from ascoderu_webapp import app


@app.route('/')
def index():
    return render_template('index.html')
