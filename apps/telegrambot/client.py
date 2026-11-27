"""Telegram Bot API bilan minimal sinxron aloqa (urllib)."""

import json
import uuid
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


def get_chat(token, chat_id):
    return _chaqir(token, "getChat", {"chat_id": chat_id})


def get_chat_member(token, chat_id, user_id, timeout=10):
    return _chaqir(token, "getChatMember", {"chat_id": chat_id, "user_id": user_id}, timeout=timeout)


def export_chat_invite_link(token, chat_id):
    return _chaqir(token, "exportChatInviteLink", {"chat_id": chat_id})


def set_webhook(token, url, secret, drop_pending_updates=False):
    return _chaqir(
        token,
        "setWebhook",
        {
            "url": url,
            "secret_token": secret,
            "allowed_updates": ["message", "callback_query", "inline_query"],
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


def answer_inline_query(token, inline_query_id, results, cache_time=30, button=None, next_offset=""):
    payload = {
        "inline_query_id": inline_query_id,
        "results": results,
        "cache_time": cache_time,
        "is_personal": True,
    }
    if button:
        payload["button"] = button
    if next_offset:
        # Telegram calls us again with this offset when the user scrolls to the end of the list.
        payload["next_offset"] = next_offset
    return _chaqir(token, "answerInlineQuery", payload)


def edit_message_reply_markup(token, chat_id, message_id, reply_markup):
    return _chaqir(
        token,
        "editMessageReplyMarkup",
        {"chat_id": chat_id, "message_id": message_id, "reply_markup": reply_markup},
    )


def send_document(token, chat_id, filename, content, caption="", parse_mode="HTML", timeout=30):
    """Upload `content` (bytes) as a file; Bot API needs multipart for uploads."""
    if not token:
        raise TelegramAPIError("sendDocument", "Bot tokeni yo'q")
    boundary = uuid.uuid4().hex
    fields = {"chat_id": str(chat_id), "caption": caption, "parse_mode": parse_mode}
    body = bytearray()
    for name, value in fields.items():
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
        ).encode("utf-8")
    safe_name = filename.replace('"', "")
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{safe_name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    body += content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendDocument",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        try:
            description = json.loads(exc.read().decode("utf-8")).get("description", str(exc))
        except Exception:
            description = str(exc)
        raise TelegramAPIError("sendDocument", description, exc.code)
    except (error.URLError, OSError, ValueError) as exc:
        raise TelegramAPIError("sendDocument", f"Telegram bilan aloqa xatosi: {exc}")
    if not result.get("ok"):
        raise TelegramAPIError("sendDocument", result.get("description", "Telegram xatosi"), result.get("error_code"))
    return result.get("result")
