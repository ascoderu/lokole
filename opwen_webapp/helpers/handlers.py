from atexit import register as run_on_app_stop
from os import path
from traceback import format_exc

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import flash
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_babel import gettext as _
from humanize import naturalsize
from werkzeug.utils import redirect

from opwen_webapp import app
from opwen_webapp import babel
from opwen_webapp import db
from opwen_webapp.actions import sync_with_remote
from opwen_webapp.helpers.logging import exception_to_logline


@babel.localeselector
def _get_locale():
    return session.get('lang_code', app.config['DEFAULT_TRANSLATION'])


@app.url_defaults
def _add_language_code(endpoint, values):
    if 'lang_code' in values:
        return

    default_translation = app.config['DEFAULT_TRANSLATION']
    translations = app.config['TRANSLATIONS']

    lang_code = session.get('lang_code', default_translation)
    if lang_code not in translations:
        lang_code = request.accept_languages.best_match(translations)
        session['lang_code'] = lang_code

    if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
        values['lang_code'] = lang_code


# noinspection PyUnusedLocal
@app.url_value_preprocessor
def _pull_language_code(endpoint, values):
    lang_code = values.pop('lang_code', None) if values else None
    if lang_code:
        session['lang_code'] = lang_code


@app.context_processor
def _inject_available_translations():
    return dict(lang_codes=app.config['TRANSLATIONS'])


@app.before_first_request
def _create_db():
    db.create_all()


@app.before_first_request
def _setup_remote_sync_cronjob():
    def run_cron():
        app.logger.info('running scheduled sync')
        sync_with_remote(app.config['INTERNET_INTERFACE_NAME'])

    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        replace_existing=True,
        func=run_cron,
        id='remote_sync_job',
        name='Upload and download emails from remote stroage',
        trigger=CronTrigger(hour=app.config['REMOTE_SYNC_SCHEDULED_HOUR_UTC'],
                            timezone='utc'))

    def stop_cron():
        app.logger.info('removing scheduled sync')
        scheduler.shutdown()

    run_on_app_stop(stop_cron)


@app.after_request
def _store_visited_endpoint(response):
    if request.endpoint != 'static':
        session['previous_endpoint'] = request.endpoint
    return response


# noinspection PyUnusedLocal
@app.errorhandler(404)
def _on_404(code_or_exception):
    app.logger.info('file not found: %s', request.url)
    flash(_('The page %(url)s does not exist.', url=request.url), category='error')
    return redirect(url_for(session.get('previous_endpoint', 'home')))


# noinspection PyUnusedLocal
@app.errorhandler(413)
def _on_413(code_or_exception):
    max_size = naturalsize(app.config['MAX_CONTENT_LENGTH'])
    flash(_('The maximum attachment size is %(max_size)s.', max_size=max_size), category='error')
    return redirect(url_for(session.get('previous_endpoint', 'home')))


@app.errorhandler(500)
def _on_500(code_or_exception):
    app.logger.error('internal server error: %s', code_or_exception)
    flash(_('Unexpected error. Please contact your admin.'), category='error')
    return redirect(url_for(session.get('previous_endpoint', 'home')))


# noinspection PyUnusedLocal
@app.errorhandler(Exception)
def _on_exception(code_or_exception):
    app.logger.error(exception_to_logline(format_exc()))
    flash(_('Unexpected error. Please contact your admin.'), category='error')
    return redirect(url_for(session.get('previous_endpoint', 'home')))


@app.route('/favicon.ico')
def _favicon():
    return send_from_directory(path.join(app.root_path, 'satic'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')
