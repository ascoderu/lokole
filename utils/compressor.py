from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from shutil import make_archive
from zipfile import BadZipfile
from zipfile import ZipFile

from utils.temporary import SafeNamedTemporaryFile


class DirectoryCompressor(metaclass=ABCMeta):
    def compress(self, directory):
        """
        :type directory: str
        :rtype: str

        """
        with SafeNamedTemporaryFile('w') as fobj:
            archive = make_archive(fobj.name, self._format, directory)
        return archive

    @abstractproperty
    def _format(self):
        """
        :rtype: str

        """
        raise NotImplementedError

    @abstractmethod
    def decompress(self, archive_path, filename, to_directory):
        """
        :type archive_path: str
        :type filename: str
        :type to_directory: str
        :rtype: str
        :raises ValueError

        """
        raise NotImplementedError


class ZipCompressor(DirectoryCompressor):
    _format = 'zip'

    def decompress(self, archive_path, filename, to_directory):
        try:
            with ZipFile(archive_path) as archive:
                extracted = archive.extract(filename, to_directory)
            return extracted
        except BadZipfile as exception:
            raise ValueError('corrupt archive') from exception
        except KeyError as exception:
            raise ValueError('file not in archive') from exception
