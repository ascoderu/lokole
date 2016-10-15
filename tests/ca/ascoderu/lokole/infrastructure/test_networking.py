import socket
from unittest import TestCase


from ca.ascoderu.lokole.infrastructure.networking import ip_address_for_interface
from ca.ascoderu.lokole.infrastructure.networking import use_network_interface


# noinspection PyUnresolvedReferences
class InterfaceBasedTestMixin(object):
    @property
    def _try_interfaces(self):
        """
        :rtype: collections.Iterable[str]

        """
        for i in range(5):
            yield 'eth{}'.format(i)
            yield 'wlan{}'.format(i)

    def run_trying_all_interfaces(self, interface_test_method):
        """
        :type interface_test_method: str -> None

        """
        for interface in self._try_interfaces:
            try:
                interface_test_method(interface)
            except IOError:
                continue
            else:
                break
        else:
            self.skipTest('unable to find a network interface for which to execute the test')


class IpAddressForInterfaceTests(InterfaceBasedTestMixin, TestCase):
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

        self.run_trying_all_interfaces(test)


class UseNetworkInterfaceTests(InterfaceBasedTestMixin, TestCase):
    _real_socket = socket.socket

    def test_use_interface_switches_socket(self):
        def test(interface):
            with use_network_interface(interface):
                self.assertIsNot(socket.socket, self._real_socket)

        self.run_trying_all_interfaces(test)

    def test_use_interface_restores_real_socket(self):
        def test(interface):
            with use_network_interface(interface):
                pass
            self.assertIs(socket.socket, self._real_socket)

        self.run_trying_all_interfaces(test)
