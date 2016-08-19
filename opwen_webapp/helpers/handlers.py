from functools import lru_cache
from os import listdir
from os import path

from flask import flash
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_security.registerable import register_user
from humanize import naturalsize
from werkzeug.utils import redirect

from config import Config
from config import ui
from opwen_webapp import app
from opwen_webapp import babel
from opwen_webapp import db
from opwen_webapp import user_datastore


@lru_cache(maxsize=1)
def _translations():
    languages = set(listdir(Config.TRANSLATIONS_PATH))
    languages.add(Config.DEFAULT_TRANSLATION)
    return languages


@babel.localeselector
def _get_locale():
    return session['lang_code']


@app.url_defaults
def _add_language_code(endpoint, values):
    if 'lang_code' in values:
        return

    lang_code = session['lang_code']
    if lang_code not in _translations():
        lang_code = request.accept_languages.best_match(_translations())
        session['lang_code'] = lang_code

    if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
        values['lang_code'] = lang_code


# noinspection PyUnusedLocal
@app.url_value_preprocessor
def _pull_language_code(endpoint, values):
    lang_code = values.pop('lang_code', None)
    if lang_code:
        session['lang_code'] = lang_code


@app.before_first_request
def _create_db():
    db.create_all()


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


# noinspection PyUnusedLocal
@app.errorhandler(Exception)
@app.errorhandler(500)
def _on_error(code_or_exception):
    flash(ui('unexpected_error'), category='error')
    return redirect(session.get('previous_url') or url_for('home'))


@app.route('/favicon.ico')
def _favicon():
    return send_from_directory(path.join(app.root_path, 'satic'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')
