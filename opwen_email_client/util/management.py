from glob import glob
from os.path import join

from flask import Flask
from flask_script import Command


# noinspection PyAbstractClass,PyMethodOverriding
class DevServerCommand(Command):
    def __call__(self, app: Flask):
        extra_files = _templates_paths_for(app)
        app.run(debug=True, extra_files=extra_files)


def _templates_paths_for(app: Flask, templates_matcher: str='*.html'):
    templates_directory = join(app.root_path, app.template_folder)
    templates_glob = join(templates_directory, '**', templates_matcher)
    return glob(templates_glob, recursive=True)
