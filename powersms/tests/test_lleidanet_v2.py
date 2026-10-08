# coding: utf-8
from __future__ import absolute_import, unicode_literals

import base64
import json
import socket

import mock
from destral import testing


class TestLleidaNetV2(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestLleidaNetV2, self).setUp()
        self.provider = self.openerp.pool.get("powersms.provider")

    def test_gsm_extended_characters_are_not_encoded(self):
        payload = self.provider._get_json_body(
            "+34666666666", "Preu 10€ ^{}", "GISCE", user="legacy-user"
        )
        self.assertEqual(payload["sms"]["txt"], "Preu 10€ ^{}")
        self.assertNotIn("encoding", payload["sms"])

    def test_non_gsm_text_is_utf16_base64_json_text(self):
        sms = self.provider._get_json_body("+12025550123", "Hola 🙂", "GISCE")["sms"]
        self.assertEqual(sms["encoding"], "base64")
        self.assertEqual(sms["charset"], "utf-16")
        self.assertEqual(sms["data_coding"], "unicode")
        self.assertIsInstance(sms["txt"], type(""))
        self.assertEqual(base64.b64decode(sms["txt"]).decode("utf-16"), "Hola 🙂")
        json.dumps(sms)

    def test_sender_limits_are_checked_before_transport(self):
        self.provider._get_json_body("+34666666666", "ok", "123456789012345")
        with self.assertRaises(ValueError):
            self.provider._get_json_body("+34666666666", "bad", "1234567890123456")
        with self.assertRaises(ValueError):
            self.provider._get_json_body("+34666666666", "bad", "TOO-LONG-NAME")

    def _account(self):
        account_obj = mock.Mock()
        account_obj.read.return_value = {
            "api_uname": "legacy-user",
            "api_pass": "secret-key",
            "api_server": "api.lleida.net",
        }
        return account_obj

    def test_legacy_configuration_uses_v2_without_password_in_payload(self):
        response = mock.Mock()
        response.read.return_value = b'{"code": 200, "status": "Success", "id": "abc"}'
        with mock.patch.object(self.provider.pool, "get", return_value=self._account()), mock.patch(
            "powersms.powersms_provider_lleidanet.urlopen", return_value=response
        ) as mocked_open:
            result = self.provider.send_sms_detailed_lleida(
                self.cursor, self.uid, 1, 2, "GISCE", "+34666666666", "legacy text"
            )
        request = mocked_open.call_args[0][0]
        sent = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.get_full_url(), "https://api.lleida.net/sms/v2/")
        self.assertEqual(request.get_header("Authorization"), "x-api-key secret-key")
        self.assertEqual(mocked_open.call_args[1]["timeout"], 15)
        self.assertEqual(sent["sms"]["user"], "legacy-user")
        self.assertNotIn("password", sent["sms"])
        self.assertTrue(result["accepted"])
        self.assertEqual(result["external_id"], "abc")

    def test_functional_and_transport_errors_are_preserved(self):
        response = mock.Mock()
        response.read.return_value = b'{"code": 1504, "status": "Error", "message": "Temporary"}'
        with mock.patch.object(self.provider.pool, "get", return_value=self._account()), mock.patch(
            "powersms.powersms_provider_lleidanet.urlopen", return_value=response
        ):
            result = self.provider.send_sms_detailed_lleida(
                self.cursor, self.uid, 1, 2, "GISCE", "+34666666666", "text"
            )
        self.assertEqual(
            (
                result["provider_code"],
                result["provider_message"],
                result["retryable"],
            ),
            (1504, "Temporary", True),
        )

        with mock.patch.object(self.provider.pool, "get", return_value=self._account()), mock.patch(
            "powersms.powersms_provider_lleidanet.urlopen", side_effect=socket.timeout("timed out")
        ):
            result = self.provider.send_sms_detailed_lleida(
                self.cursor, self.uid, 1, 2, "GISCE", "+34666666666", "text"
            )
        self.assertFalse(result["accepted"])
        self.assertTrue(result["retryable"])

    def test_legacy_boolean_matches_detailed_result(self):
        detailed = {
            "accepted": True,
            "provider_code": 200,
            "provider_message": "Success",
            "external_id": "abc",
            "retryable": False,
            "raw_response": None,
        }
        with mock.patch.object(
            self.provider, "send_sms_detailed_lleida", return_value=detailed
        ):
            result = self.provider.send_sms_lleida(
                self.cursor, self.uid, 1, 2, "GISCE", "+34666666666", "legacy text"
            )
        self.assertIs(result, detailed["accepted"])
