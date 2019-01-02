#!/usr/bin/env python3

from applicationinsights.flask.ext import AppInsights
from applicationinsights.flask.ext import CONF_KEY
from connexion import App
from connexion.apps.flask_app import flask

from opwen_email_server.config import APPINSIGHTS_KEY
from opwen_email_server.utils.imports import can_import
from opwen_email_server.utils.log import LogMixin

_servers = list(filter(can_import, ('tornado', 'gevent', 'flask')))
_hosts = ['127.0.0.1', '0.0.0.0']  # nosec

_server = _servers[0]
_host = _hosts[0]
_port = 8080
_ui = False


def _get_flask(app: App) -> flask.Flask:
    return app.app


def build_app(apis, host=_host, port=_port, server=_server, ui=_ui):
    app = App(__name__, host=host, port=port, server=server,
              options={'swagger_ui': ui})

    flask_app = _get_flask(app)
    flask_app.config[CONF_KEY] = APPINSIGHTS_KEY
    appinsights = AppInsights(flask_app)

    # noinspection PyProtectedMember
    LogMixin.inject(flask_app.logger, appinsights._channel)

    for api in apis:
        app.add_api(api)

    return app


def _cli():
    from argparse import ArgumentParser
    from argparse import FileType

    parser = ArgumentParser()
    parser.add_argument('--host', choices=_hosts, default=_host)
    parser.add_argument('--port', type=int, default=_port)
    parser.add_argument('--server', choices=_servers, default=_server)
    parser.add_argument('--ui', action='store_true', default=_ui)
    parser.add_argument('apis', nargs='+', type=FileType('r'))
    args = parser.parse_args()

    apis = []
    for fobj in args.apis:
        apis.append(fobj.name)
        fobj.close()

    app = build_app(apis, args.host, args.port, args.server, args.ui)

    app.run()


if __name__ == '__main__':
    _cli()
