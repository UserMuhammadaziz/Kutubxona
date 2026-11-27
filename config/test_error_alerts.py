import logging
import os
import sys
from unittest import mock

from django.test import SimpleTestCase

from config import error_alerts
from config.error_alerts import TelegramAlertHandler, redact

ENV = {"ERROR_ALERT_BOT_TOKEN": "123:abc", "ERROR_ALERT_CHAT_IDS": "11, 22", "ERROR_ALERT_SOURCE": "prod"}


def record(msg="boom", exc=None, name="django.request"):
    exc_info = None
    if exc is not None:
        try:
            raise exc
        except Exception:
            exc_info = sys.exc_info()
    return logging.LogRecord(name, logging.ERROR, __file__, 10, msg, None, exc_info)


class ErrorAlertTest(SimpleTestCase):
    def test_disabled_without_env(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(TelegramAlertHandler, "send") as send:
            TelegramAlertHandler().emit(record())
        send.assert_not_called()
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(error_alerts.attach(logging.getLogger("alerts-test")))

    def test_sends_to_every_chat_with_traceback(self):
        with mock.patch.dict(os.environ, ENV), mock.patch.object(TelegramAlertHandler, "send") as send:
            handler = TelegramAlertHandler(process_name="web")
            handler._send_all(handler.build_text(record("Internal Server Error", ValueError("bad"))))
        self.assertEqual([c.args[0] for c in send.call_args_list], ["11", "22"])
        text = send.call_args.args[1]
        self.assertIn("prod · web", text)
        self.assertIn("ValueError: bad", text)

    def test_same_error_sent_once_per_window(self):
        with mock.patch.dict(os.environ, ENV):
            handler = TelegramAlertHandler()
        key = handler.fingerprint(record(exc=KeyError("x")))
        self.assertTrue(handler.allow(key, now=0))
        self.assertFalse(handler.allow(key, now=60))
        self.assertTrue(handler.allow(key, now=error_alerts.DEDUP_SECONDS + 1))

    def test_hourly_cap(self):
        with mock.patch.dict(os.environ, ENV):
            handler = TelegramAlertHandler()
        allowed = [handler.allow(f"k{i}", now=i) for i in range(error_alerts.MAX_PER_HOUR + 5)]
        self.assertEqual(sum(allowed), error_alerts.MAX_PER_HOUR)

    def test_secrets_redacted(self):
        text = redact("token 1234567890:AAH" + "x" * 33 + " password=hunter2 postgresql://u:p@h/db Bearer abc.def")
        for secret in ("AAHxxx", "hunter2", "u:p@h", "abc.def"):
            self.assertNotIn(secret, text)

    def test_disallowed_host_ignored(self):
        with mock.patch.dict(os.environ, ENV), mock.patch("threading.Thread") as thread:
            TelegramAlertHandler().emit(record(name="django.security.DisallowedHost"))
        thread.assert_not_called()
