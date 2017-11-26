from glob import glob
from os.path import join
from typing import List

from flask import Flask
from flask_script import Command


# noinspection PyAbstractClass,PyMethodOverriding
class DevServerCommand(Command):
    def __call__(self, app: Flask):
        _load_environment(app)

        templates_paths = _templates_paths_for(app, '*.html')
        reload_server_if_changed = templates_paths

        app.run(debug=True, extra_files=reload_server_if_changed)


def _load_environment(app: Flask) -> None:
    try:
        # noinspection PyUnresolvedReferences
        from dotenv import load_dotenv
        load_dotenv(join(app.root_path, '..', '..', '.env'))
    except ImportError:
        pass


def _templates_paths_for(app: Flask, templates_matcher: str) -> List[str]:
    templates_directory = join(app.root_path, app.template_folder)
    templates_glob = join(templates_directory, '**', templates_matcher)
    return glob(templates_glob, recursive=True)
