from os import path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from atexit import register as run_on_app_stop
from flask import flash
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_babel import gettext as _
from flask_security.registerable import register_user
from humanize import naturalsize
from werkzeug.utils import redirect

from config import Config
from opwen_webapp import app
from opwen_webapp import babel
from opwen_webapp import db
from opwen_webapp import user_datastore
from opwen_webapp.controllers import sync_with_remote


@babel.localeselector
def _get_locale():
    return session['lang_code']


@app.url_defaults
def _add_language_code(endpoint, values):
    if 'lang_code' in values:
        return

    lang_code = session['lang_code']
    if lang_code not in Config.TRANSLATIONS:
        lang_code = request.accept_languages.best_match(Config.TRANSLATIONS)
        session['lang_code'] = lang_code

    if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
        values['lang_code'] = lang_code


# noinspection PyUnusedLocal
@app.url_value_preprocessor
def _pull_language_code(endpoint, values):
    lang_code = values.pop('lang_code', None)
    if lang_code:
        session['lang_code'] = lang_code


@app.context_processor
def _inject_available_translations():
    return dict(lang_codes=Config.TRANSLATIONS)


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


@app.before_first_request
def _setup_remote_sync_cronjob():
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        replace_existing=True,
        func=sync_with_remote,
        id='remote_sync_job',
        name='Upload and download emails from remote stroage',
        trigger=CronTrigger(hour=Config.REMOTE_SYNC_SCHEDULED_HOUR_UTC,
                            timezone='utc'))
    run_on_app_stop(lambda: scheduler.shutdown())


@app.after_request
def _store_visited_endpoint(response):
    if request.endpoint != 'static':
        session['previous_endpoint'] = request.endpoint
    return response


# noinspection PyUnusedLocal
@app.errorhandler(404)
def _on_404(code_or_exception):
    flash(_('The page %(url)s does not exist.', url=request.url), category='error')
    return redirect(url_for(session.get('previous_endpoint', 'home')))


# noinspection PyUnusedLocal
@app.errorhandler(413)
def _on_413(code_or_exception):
    max_size = naturalsize(Config.MAX_CONTENT_LENGTH)
    flash(_('The maximum attachment size is %(max_size)s.', max_size=max_size), category='error')
    return redirect(url_for(session.get('previous_endpoint', 'home')))


# noinspection PyUnusedLocal
@app.errorhandler(Exception)
@app.errorhandler(500)
def _on_error(code_or_exception):
    flash(_('Unexpected error. Please contact your admin.'), category='error')
    return redirect(url_for(session.get('previous_endpoint', 'home')))


@app.route('/favicon.ico')
def _favicon():
    return send_from_directory(path.join(app.root_path, 'satic'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')
