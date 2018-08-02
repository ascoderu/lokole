#!/usr/bin/env python3

from connexion import App
from opwen_email_server.utils.imports import can_import


_servers = list(filter(can_import, ('tornado', 'gevent', 'flask')))
_hosts = ['127.0.0.1', '0.0.0.0']  # nosec

_server = _servers[0]
_host = _hosts[0]
_port = 8080
_ui = False


def build_app(apis, host=_host, port=_port, server=_server, ui=_ui):
    app = App(__name__, host=host, port=port, server=server, swagger_ui=ui)

    for api in apis:
        app.add_api(api)

    return app


def _cli():
    from argparse import ArgumentParser
    from argparse import FileType
    from os.path import dirname
    from os.path import join

    try:
        # noinspection PyUnresolvedReferences
        from dotenv import load_dotenv
        load_dotenv(join(dirname(__file__), '.env'))
    except ImportError:
        pass

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
