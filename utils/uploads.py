from os import makedirs
from os import path

from werkzeug.utils import secure_filename


SCRIPTS = frozenset('.js .php .pl .py .rb .sh'.split())
EXECUTABLES = frozenset('.so .exe .dll'.split())


class UploadNotAllowed(Exception):
    pass


class Uploads(object):
    def __init__(self, app, directory=None, disallowed=None):
        """
        :type app: flask.Flask
        :type directory: str
        :type disallowed: collections.Iterable[str]

        """
        self.app = app
        self.root_directory = directory or app.config.get('UPLOAD_DIRECTORY')
        self.disallowed = frozenset(disallowed or SCRIPTS | EXECUTABLES)

    def _path_for_save(self, filename):
        """
        :type filename: str
        :rtype: str

        """
        upload_name = secure_filename(filename)
        base, extension = path.splitext(upload_name)
        i = 1
        while path.isfile(path.join(self.root_directory, upload_name)):
            upload_name = '%s_%d%s' % (base, i, extension)
            i += 1

        return path.join(self.root_directory, upload_name)

    def save(self, upload):
        """
        :type upload: werkzeug.datastructures.FileStorage
        :rtype: str
        :raises UploadNotAllowed

        """
        extension = path.splitext(upload.filename)[1]
        if extension in self.disallowed:
            raise UploadNotAllowed

        upload_path = self._path_for_save(upload.filename)
        upload_directory, upload_filename = path.split(upload_path)

        makedirs(upload_directory, exist_ok=True)
        upload.save(upload_path)
        return upload_filename

    def path(self, filename):
        """
        :type filename: str
        :rtype: str

        """
        return path.join(self.root_directory, secure_filename(filename))

    def url(self, filename):
        """
        :type filename: str
        :rtype: str

        """
        endpoint = self.app.config.get('UPLOAD_ENDPOINT')
        resource = secure_filename(filename)
        return '/%s/%s' % (endpoint, resource)
