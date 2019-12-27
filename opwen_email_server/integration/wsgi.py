#!/usr/bin/env python3

from applicationinsights.flask.ext import AppInsights
from connexion import App
from flask import Flask
from flask_cors import CORS

from opwen_email_server import config

_hosts = ['127.0.0.1', '0.0.0.0']  # nosec

_host = _hosts[0]
_port = 8080
_ui = False


def build_app(apis, host=_host, port=_port, ui=_ui):
    app = App(__name__, host=host, port=port, server='flask', options={'swagger_ui': ui})

    for api in apis:
        app.add_api(api)

    _configure_flask(app.app)

    return app


def _configure_flask(app: Flask):
    app.config['APPINSIGHTS_INSTRUMENTATIONKEY'] = config.APPINSIGHTS_KEY
    app.config['APPINSIGHTS_ENDPOINT_URI'] = config.APPINSIGHTS_HOST
    app.config['APPINSIGHTS_DISABLE_TRACE_LOGGING'] = True
    app.config['APPINSIGHTS_DISABLE_REQUEST_LOGGING'] = True
    AppInsights(app)

    CORS(app)


def _cli():
    from argparse import ArgumentParser
    from argparse import FileType

    parser = ArgumentParser()
    parser.add_argument('--host', choices=_hosts, default=_host)
    parser.add_argument('--port', type=int, default=_port)
    parser.add_argument('--ui', action='store_true', default=_ui)
    parser.add_argument('apis', nargs='+', type=FileType('r'))
    args = parser.parse_args()

    apis = []
    for fobj in args.apis:
        apis.append(fobj.name)
        fobj.close()

    app = build_app(apis, args.host, args.port, args.ui)

    app.run()


if __name__ == '__main__':
    _cli()
