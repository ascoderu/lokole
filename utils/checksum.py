from hashlib import sha256 as _sha256

_DEFAULT_BUFFER_SIZE = 65536


def _hash_file_incrementally(filename, algorithm, buffer_size):
    """
    :type filename: str
    :type buffer_size: int
    :rtype: str

    """
    content_hash = algorithm
    with open(filename, 'rb') as fobj:
        while True:
            data = fobj.read(buffer_size)
            if not data:
                break
            content_hash.update(data)
    return content_hash.hexdigest()


def sha256(filename, buffer_size=_DEFAULT_BUFFER_SIZE):
    """
    :type filename: str
    :type buffer_size: int
    :rtype: str

    """
    return _hash_file_incrementally(filename, _sha256(), buffer_size)
