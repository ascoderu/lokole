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
        self.assertIsLogMessage(*log_args)
        self.assertDidCallLogger(log_level, *log_args)
        self.assertDidCallApplicationInsights(log_level, *log_args)

    def assertDidCallApplicationInsights(self, log_level, fmt, *args):
        mock = self.appinsights_mock.track_trace
        mock.assert_called_once_with(fmt % args, {'level': log_level})

    def assertDidCallLogger(self, log_level, *log_args):
        mock = getattr(self.logger_mock, log_level)
        mock.assert_called_once_with(*log_args)

    def assertIsLogMessage(self, fmt, *args):
        try:
            fmt % args
        except TypeError:
            self.fail('unable to format string: %s %% %r' % (fmt, args))

    def setUp(self):
        self.log_patcher = patch.object(log, '_LOG')
        self.appinsights_patcher = patch.object(log, '_APPINSIGHTS')
        self.logger_mock = self.log_patcher.start()
        self.appinsights_mock = self.appinsights_patcher.start()
        self.addCleanup(self.log_patcher.stop)
        self.addCleanup(self.appinsights_patcher.stop)
