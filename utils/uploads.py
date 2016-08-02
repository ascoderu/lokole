from os import makedirs
from os import path
from os import rename

from werkzeug.datastructures import FileStorage

from utils.checksum import sha256
from utils.temporary import SafeNamedTemporaryFile

SCRIPTS = frozenset('.js .php .pl .py .rb .sh'.split())
EXECUTABLES = frozenset('.so .exe .dll'.split())


class LocalFileStorage(FileStorage):
    # noinspection PyMissingConstructor
    def __init__(self, localpath):
        """
        :type localpath: str

        """
        self.filename = localpath

    def save(self, dst, buffer_size=16384):
        # the FileStorage already exists on the file-system
        # no need to save it again
        return self.filename


class UploadNotAllowed(Exception):
    pass


class Uploads(object):
    def __init__(self, app=None, directory=None, disallowed=None, hasher=None):
        """
        :type app: flask.Flask
        :type directory: str
        :type disallowed: collections.Iterable[str]

        """
        self.root_directory = directory
        self.disallowed = frozenset(disallowed or SCRIPTS | EXECUTABLES)
        self.hasher = hasher or sha256

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        :type app: flask.Flask

        """
        if not self.root_directory:
            self.root_directory = app.config.get('UPLOAD_DIRECTORY')

    def _check_upload_allowed(self, filename):
        """
        :type filename: str
        :raises UploadNotAllowed

        """
        extension = path.splitext(filename)[1]
        if extension in self.disallowed:
            raise UploadNotAllowed

    @classmethod
    def _save_to_temporary_location(cls, upload):
        """
        :type upload: FileStorage
        :rtype: str

        """
        with SafeNamedTemporaryFile('w', delete=False) as tmpfile:
            upload.save(tmpfile.name)
        return tmpfile.name

    @classmethod
    def _move_to(cls, from_path, to_path):
        """
        :type from_path: str
        :type to_path: str

        """
        makedirs(path.dirname(to_path), mode=0o700, exist_ok=True)
        rename(from_path, to_path)

    def _move_to_upload_directory(self, uploaded_filename):
        """
        :type uploaded_filename: str
        :rtype: str

        """
        upload_location = path.join(self.root_directory,
                                    self.hasher(uploaded_filename))
        self._move_to(uploaded_filename, upload_location)
        return upload_location

    def save(self, upload):
        """
        :type upload: FileStorage | str
        :rtype: str
        :raises UploadNotAllowed

        """
        if isinstance(upload, str) and path.exists(upload):
            upload = LocalFileStorage(upload)

        self._check_upload_allowed(upload.filename)

        temporary_filename = self._save_to_temporary_location(upload)

        return self._move_to_upload_directory(temporary_filename)
