"""Send ERROR log records to a Telegram "reports" bot.

Standard library only, so the aiogram bot process (which has its own
``config`` module on sys.path) can load this file by path as well.

Configured by environment variables; without them the handler does nothing:
    ERROR_ALERT_BOT_TOKEN  token of the reports bot
    ERROR_ALERT_CHAT_IDS   comma separated Telegram chat ids
    ERROR_ALERT_SOURCE     label shown in each alert, e.g. "prod"
"""

import json
import logging
import os
import re
import socket
import threading
import time
import traceback
import urllib.request

TELEGRAM_LIMIT = 4000
# Same error (logger + exception type + place) is sent once per window.
DEDUP_SECONDS = 600
# Hard cap per process, so an error storm cannot flood the chat.
MAX_PER_HOUR = 30

_SECRET_PATTERNS = [
    (re.compile(r"\d{6,12}:[A-Za-z0-9_-]{30,}"), "<bot-token>"),
    (re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|authorization)(['\"]?\s*[:=]\s*)['\"]?[^\s'\",&]+"), r"\1\2<hidden>"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"), "Bearer <hidden>"),
    (re.compile(r"postgres(ql)?://[^\s]+"), "postgresql://<hidden>"),
]

# Noise that is not ours to fix: bad Host headers from scanners.
IGNORED_LOGGERS = ("django.security.DisallowedHost",)


def redact(text):
    for pattern, repl in _SECRET_PATTERNS:
        text = pattern.sub(repl, text)
    return text


class TelegramAlertHandler(logging.Handler):
    def __init__(self, level=logging.ERROR, process_name=""):
        super().__init__(level=level)
        self.token = os.environ.get("ERROR_ALERT_BOT_TOKEN", "").strip()
        self.chat_ids = [c.strip() for c in os.environ.get("ERROR_ALERT_CHAT_IDS", "").split(",") if c.strip()]
        self.source = os.environ.get("ERROR_ALERT_SOURCE", "").strip() or socket.gethostname()
        self.process_name = process_name
        self._seen = {}
        self._sent_times = []
        self._lock = threading.Lock()

    @property
    def enabled(self):
        return bool(self.token and self.chat_ids)

    def fingerprint(self, record):
        where = f"{record.pathname}:{record.lineno}"
        exc_type = ""
        if record.exc_info and record.exc_info[1] is not None:
            exc = record.exc_info[1]
            exc_type = type(exc).__name__
            tb = traceback.extract_tb(record.exc_info[2]) if record.exc_info[2] else []
            if tb:
                where = f"{tb[-1].filename}:{tb[-1].lineno}"
        return f"{record.name}|{exc_type}|{where}"

    def allow(self, key, now=None):
        now = time.monotonic() if now is None else now
        with self._lock:
            last = self._seen.get(key)
            if last is not None and now - last < DEDUP_SECONDS:
                return False
            self._sent_times = [t for t in self._sent_times if now - t < 3600]
            if len(self._sent_times) >= MAX_PER_HOUR:
                return False
            self._seen[key] = now
            self._sent_times.append(now)
            return True

    def build_text(self, record):
        head = f"🚨 {self.source}"
        if self.process_name:
            head += f" · {self.process_name}"
        lines = [head, f"{record.levelname} · {record.name}"]
        request = getattr(record, "request", None)
        if request is not None:
            method = getattr(request, "method", "")
            path = getattr(request, "path", "")
            user = getattr(request, "user", None)
            user_id = getattr(user, "pk", None) if user is not None and getattr(user, "is_authenticated", False) else None
            lines.append(f"{method} {path}" + (f" · user {user_id}" if user_id else ""))
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        lines.append(message[:800])
        if record.exc_info:
            tb = "".join(traceback.format_exception(*record.exc_info))
            lines.append("")
            lines.append(tb[-2500:])
        return redact("\n".join(lines))[:TELEGRAM_LIMIT]

    def emit(self, record):
        if not self.enabled or record.name.startswith(IGNORED_LOGGERS):
            return
        try:
            if not self.allow(self.fingerprint(record)):
                return
            text = self.build_text(record)
        except Exception:
            self.handleError(record)
            return
        threading.Thread(target=self._send_all, args=(text,), daemon=True).start()

    def _send_all(self, text):
        for chat_id in self.chat_ids:
            self.send(chat_id, text)

    def send(self, chat_id, text):
        body = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=5).close()
        except Exception:
            # Never log here: a failing alert must not raise another alert.
            pass


def attach(logger=None, process_name=""):
    """Add the handler to a logger (root by default) once; returns it or None when not configured."""
    logger = logger or logging.getLogger()
    for h in logger.handlers:
        if isinstance(h, TelegramAlertHandler):
            return h
    handler = TelegramAlertHandler(process_name=process_name)
    if not handler.enabled:
        return None
    logger.addHandler(handler)
    return handler
