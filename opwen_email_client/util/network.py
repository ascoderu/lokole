from socket import create_connection
from socket import gethostbyname


def check_connection(hostname: str, port: int) -> bool:
    try:
        host = gethostbyname(hostname)
        with create_connection((host, port)):
            return True
    except OSError:
        pass
    return False
