# coding: utf-8
from __future__ import absolute_import, unicode_literals

import base64
import json
import socket

from osv import osv

try:
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse
    from urllib.request import Request, urlopen
except ImportError:  # pragma: no cover - Python 2
    from urllib2 import HTTPError, Request, URLError, urlopen
    from urlparse import urlparse


GSM_BASIC = (
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ"
    " !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿"
    "abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM_EXTENDED = "^{}\\[~]|€"
TEMPORARY_CODES = {1504}
DEFAULT_ENDPOINT = "https://api.lleida.net/sms/v2/"
DEFAULT_TIMEOUT = 15


class PowersmsProviderLleidaNet(osv.osv):
    _inherit = "powersms.provider"

    def _is_gsm_text(self, message):
        return all(character in GSM_BASIC or character in GSM_EXTENDED for character in message)

    def _validate_sender(self, sender):
        if not sender:
            raise ValueError("Lleida.net sender cannot be empty")
        if sender.isdigit():
            valid = len(sender) <= 15
        else:
            valid = len(sender) <= 11 and sender.isalnum()
        if not valid:
            raise ValueError("Invalid Lleida.net sender")

    def _get_json_body(self, number_to, message, from_name, user=None, context=None):
        self._validate_sender(from_name)
        sms = {"dst": {"num": number_to}, "src": from_name, "txt": message}
        if user is not None:
            sms["user"] = user
        if not self._is_gsm_text(message):
            encoded = base64.b64encode(message.encode("utf-16")).decode("ascii")
            sms.update(
                {
                    "charset": "utf-16",
                    "data_coding": "unicode",
                    "encoding": "base64",
                    "txt": encoded,
                }
            )
        context = context or {}
        if context.get("user_id"):
            sms["user_id"] = context["user_id"]
        if context.get("delivery_receipt"):
            sms["delivery_receipt"] = context["delivery_receipt"]
        return {"sms": sms}

    def _get_endpoint(self, api_server):
        server = (api_server or "").strip()
        if not server or server.rstrip("/") == "api.lleida.net":
            return DEFAULT_ENDPOINT
        if "://" not in server:
            server = "https://" + server
        parsed = urlparse(server)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Invalid Lleida.net API server")
        if parsed.path in ("", "/"):
            server = server.rstrip("/") + "/sms/v2/"
        return server

    def _result(self, accepted=False, code=None, message=None, retryable=False, raw=None):
        return {
            "accepted": accepted,
            "provider_code": code,
            "provider_message": message,
            "external_id": (raw or {}).get("id") or (raw or {}).get("message_id"),
            "retryable": retryable,
            "raw_response": raw,
        }

    def send_sms_detailed_lleida(
        self, cursor, uid, _id, account_id, from_name, numbers_to, body="", files=None, context=None
    ):
        account_obj = self.pool.get("powersms.core_accounts")
        values = account_obj.read(
            cursor, uid, account_id, ["api_uname", "api_pass", "api_server"]
        )
        endpoint = self._get_endpoint(values.get("api_server"))
        payload = self._get_json_body(
            numbers_to, body, from_name, user=values.get("api_uname"), context=context
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "Authorization": "x-api-key {}".format(values.get("api_pass") or ""),
        }
        request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            response = urlopen(request, timeout=DEFAULT_TIMEOUT)
            raw_body = response.read().decode("utf-8")
        except HTTPError as error:
            return self._result(code=error.code, message="Lleida.net HTTP error")
        except (URLError, socket.timeout) as error:
            return self._result(message=str(error), retryable=True)
        try:
            result = json.loads(raw_body)
        except (TypeError, ValueError):
            return self._result(message="Invalid JSON response from Lleida.net")
        code = result.get("code")
        status = result.get("status")
        message = result.get("message") or result.get("error") or status
        accepted = code == 200 and status == "Success"
        return self._result(
            accepted=accepted,
            code=code,
            message=message,
            retryable=code in TEMPORARY_CODES,
            raw={key: result.get(key) for key in ("code", "status", "message", "id", "message_id")},
        )

    def send_sms_lleida(
        self, cursor, uid, _id, account_id, from_name, numbers_to, body="", files=None, context=None
    ):
        result = self.send_sms_detailed_lleida(
            cursor, uid, _id, account_id, from_name, numbers_to, body, files, context=context
        )
        return result["accepted"]


PowersmsProviderLleidaNet()
