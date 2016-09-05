import socket
from unittest import TestCase

from utils.networking import ip_address_for_interface
from utils.networking import use_interface


# noinspection PyUnresolvedReferences
class InterfaceBasedTestMixin(object):
    @property
    def _try_interfaces(self):
        for i in range(5):
            yield 'eth{}'.format(i)
            yield 'wlan{}'.format(i)

    def inject_interfaces(self, interface_test_method):
        for interface in self._try_interfaces:
            try:
                interface_test_method(interface)
            except IOError:
                continue
            else:
                break
        else:
            self.skipTest('unable to find an interface to test')


class TestIpAddressForInterface(InterfaceBasedTestMixin, TestCase):
    def assertIsIpAddress(self, ip):
        """
        :type ip: str

        """
        self.assertRegexpMatches(ip, r'\d{1,3}\.\d{1,3}.\d{1,3}.\d{1,3}')

    def test_nonexisting_interface_raises_ioerror(self):
        with self.assertRaises(IOError):
            ip_address_for_interface('does-not-exist')

    def test_existing_interface_returns_some_ip(self):
        def test(interface):
            ip = ip_address_for_interface(interface)
            self.assertIsIpAddress(ip)

        self.inject_interfaces(test)


class TestUseInterface(InterfaceBasedTestMixin, TestCase):
    _real_socket = socket.socket

    def test_use_interface_switches_socket(self):
        def test(interface):
            with use_interface(interface):
                self.assertIsNot(socket.socket, self._real_socket)

        self.inject_interfaces(test)

    def test_use_interface_restores_real_socket(self):
        def test(interface):
            with use_interface(interface):
                pass
            self.assertIs(socket.socket, self._real_socket)

        self.inject_interfaces(test)
