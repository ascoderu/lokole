from abc import ABCMeta
from abc import abstractmethod
import json


class FileFormatter(metaclass=ABCMeta):
    _encoding = 'utf8'

    def __init__(self, name=None, mode=None, fobj=None):
        """
        :type name: str
        :type mode: str
        :type fobj: io.BytesIO

        """
        self.name = name
        self.mode = mode
        self.fobj = fobj or open(name, mode + 'b')

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.fobj.close()

    def _check_is_closed(self):
        if self.fobj.closed:
            raise ValueError('I/O on closed file')

    def _check_can_write(self):
        if self.mode != 'w':
            raise ValueError('invalid mode for write: %s' % self.mode)
        self._check_is_closed()

    def _check_can_read(self):
        if self.mode != 'r':
            raise ValueError('invalid mode for read: %s' % self.mode)
        self._check_is_closed()

    def write(self, obj):
        """
        :type obj: object

        """
        self._check_can_write()
        self._write(obj)

    def __iter__(self):
        """
        :rtype: collections.Iterable[object]

        """
        self._check_can_read()
        return self._read()

    @abstractmethod
    def _read(self):
        """
        :rtype: collections.Iterable[object]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _write(self, obj):
        """
        :type obj: object

        """
        raise NotImplementedError  # pragma: no cover


class JsonLines(FileFormatter):
    _separators = (',', ':')

    def _write(self, obj):
        serialized = json.dumps(obj, separators=self._separators)
        line = serialized.encode(self._encoding)
        self.fobj.write(line)
        self.fobj.write(b'\n')

    def _read(self):
        for line in self.fobj:
            serialized = line.decode(self._encoding)
            yield json.loads(serialized)
