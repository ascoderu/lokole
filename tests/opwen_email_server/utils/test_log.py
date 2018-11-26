from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.utils.log import LogMixin


class LogMixinTests(TestCase):
    def test_adds_class_name_to_output(self):
        class Foo(LogMixin):
            def foo(self):
                self.log_info('message %d', 123)
        Foo().foo()

        self.assertDidLog('info', '%s|message %d', 'Foo', 123)

    def test_important_messages_get_quickly_sent_by_appinsights(self):
        class Foo(LogMixin):
            def foo(self):
                self.log_info('message %d', 123)
        Foo().foo()
        self.assertAppInsightsIsSent()

    def test_not_important_messages_get_delayed_by_appinsights(self):
        class Foo(LogMixin):
            def foo(self):
                self.log_debug('message %d', 123)
        Foo().foo()
        self.assertAppInsightsIsSent(False)

    def assertDidLog(self, log_level, *log_args):
        self.assertIsLogMessage(*log_args)
        self.assertDidCallLogger(log_level, *log_args)
        self.assertDidCallApplicationInsights(log_level, *log_args)

    def assertAppInsightsIsSent(self, is_sent=True):
        mock = self.appinsights_mock.flush
        self.assertEqual(bool(mock.call_count), is_sent)

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
        log_patcher = patch.object(LogMixin, '_logger')
        appinsights_patcher = patch.object(LogMixin, '_telemetry_client')
        self.logger_mock = log_patcher.start()
        self.appinsights_mock = appinsights_patcher.start()
        self.addCleanup(log_patcher.stop)
        self.addCleanup(appinsights_patcher.stop)
