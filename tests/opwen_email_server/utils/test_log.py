from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.utils import log


class LogMixinTests(TestCase):
    def test_adds_class_name_to_output(self):
        class Foo(log.LogMixin):
            def foo(self):
                self.log_info('message %d', 123)
        Foo().foo()

        self.assertDidLog('info', '%s:message %d', 'Foo', 123)

    def test_adds_extra_args_to_output(self):
        class Bar(log.LogMixin):
            def bar(self):
                self.log_info('message %d', 3)

            def extra_log_args(self):
                yield 'a %s', 1
                yield 'b %s', 2
        Bar().bar()

        self.assertDidLog('info', '%s:a %s:b %s:message %d', 'Bar', 1, 2, 3)

    def assertDidLog(self, log_level, *log_args):
        log_method_mock = getattr(self.logger_mock, log_level)
        log_method_mock.assert_called_once_with(*log_args)
        self.assertIsLogMessage(*log_args)

    def assertIsLogMessage(self, fmt, *args):
        try:
            fmt % args
        except TypeError:
            self.fail('unable to format string: %s %% %r' % (fmt, args))

    def setUp(self):
        self.log_patcher = patch.object(log, '_LOG')
        self.logger_mock = self.log_patcher.start()
        self.addCleanup(self.log_patcher.stop)
