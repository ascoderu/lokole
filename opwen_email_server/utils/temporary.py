from os import close
from tempfile import mkstemp


def create_tempfilename() -> str:
    file_descriptor, filename = mkstemp()
    close(file_descriptor)
    return filename
