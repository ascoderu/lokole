import fcntl
import socket
import struct
from contextlib import contextmanager


@contextmanager
def use_interface(ifname):
    """
    :type ifname: str

    """
    ip = _ip_address_for_interface(ifname.encode('ascii'))
    original_socket = socket.socket

    def rebound_socket(*args, **kwargs):
        sock = original_socket(*args, **kwargs)
        sock.bind((ip, 0))
        return sock

    socket.socket = rebound_socket
    yield
    socket.socket = original_socket


def _ip_address_for_interface(ifname):
    """
    :type ifname: bytes
    :rtype: str

    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        sock.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
