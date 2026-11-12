"""Telegram Bot API bilan minimal sinxron aloqa (urllib)."""

import json
from urllib import error, request


class TelegramAPIError(Exception):
    def __init__(self, method, description, status=None):
        self.method = method
        self.description = description
        self.status = status
        super().__init__(description)


def _chaqir(token, method, payload=None, timeout=15):
    if not token:
        raise TelegramAPIError(method, "Bot tokeni yo'q")
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    so_rov = request.Request(url, data=data, headers=headers)
    try:
        with request.urlopen(so_rov, timeout=timeout) as javob:
            natija = json.loads(javob.read().decode("utf-8"))
    except error.HTTPError as xato:
        try:
            tana = json.loads(xato.read().decode("utf-8"))
            tavsif = tana.get("description", str(xato))
        except Exception:
            tavsif = str(xato)
        raise TelegramAPIError(method, tavsif, xato.code)
    except (error.URLError, OSError, ValueError) as xato:
        raise TelegramAPIError(method, f"Telegram bilan aloqa xatosi: {xato}")

    if not natija.get("ok"):
        raise TelegramAPIError(
            method, natija.get("description", "Telegram xatosi"), natija.get("error_code")
        )
    return natija.get("result")


def get_me(token):
    return _chaqir(token, "getMe")


def set_webhook(token, url, secret, drop_pending_updates=False):
    return _chaqir(
        token,
        "setWebhook",
        {
            "url": url,
            "secret_token": secret,
            "allowed_updates": ["message", "callback_query"],
            "drop_pending_updates": bool(drop_pending_updates),
        },
    )


def delete_webhook(token):
    return _chaqir(token, "deleteWebhook", {"drop_pending_updates": False})


def get_webhook_info(token):
    return _chaqir(token, "getWebhookInfo")


def send_message(token, chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return _chaqir(token, "sendMessage", payload)


def answer_callback_query(token, callback_query_id, text=""):
    return _chaqir(
        token, "answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text}
    )


def edit_message_reply_markup(token, chat_id, message_id, reply_markup):
    return _chaqir(
        token,
        "editMessageReplyMarkup",
        {"chat_id": chat_id, "message_id": message_id, "reply_markup": reply_markup},
    )
