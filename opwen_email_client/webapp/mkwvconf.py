from flask import Blueprint
from flask import Response
from flask import jsonify
from flask import request
from mkwvconf import Mkwvconf
from mkwvconf.mkwvconf import DEFAULT_MODEM_DEVICE
from mkwvconf.mkwvconf import DEFAULT_PROFILE_NAME

from opwen_email_client.webapp.cache import cache

blueprint = Blueprint('mkwvconf', __name__)


def create_mkwvconf() -> Mkwvconf:
    return Mkwvconf({
        option: request.args.get(option, default)
        for option, default in (
          ('modemDevice', DEFAULT_MODEM_DEVICE),
          ('profileName', DEFAULT_PROFILE_NAME),
        )
    })


@blueprint.route('/<country>/<provider>/<apn>')
@cache.memoize(timeout=600)
def get_config(country: str, provider: str, apn: str) -> Response:
    mkwvconf = create_mkwvconf()
    parameters = mkwvconf.getConfigParameters(country, provider, apn)
    config = mkwvconf.formatConfig(parameters)
    return jsonify({'config': config})


@blueprint.route('/<country>/<provider>')
@cache.memoize(timeout=600)
def list_apns(country: str, provider: str) -> Response:
    mkwvconf = create_mkwvconf()
    apns = mkwvconf.getApns(country, provider)
    return jsonify({'apns': apns})


@blueprint.route('/<country>')
@cache.memoize(timeout=600)
def list_providers(country: str) -> Response:
    mkwvconf = create_mkwvconf()
    providers = mkwvconf.getProviders(country)
    return jsonify({'providers': providers})


@blueprint.route('/')
@cache.memoize(timeout=600)
def list_countries() -> Response:
    mkwvconf = create_mkwvconf()
    countries = mkwvconf.getCountryCodes()
    return jsonify({'countries': countries})
