# coding: utf-8
from __future__ import absolute_import, unicode_literals

import base64
import json

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
        response = mock.Mock(
            error=False,
            result={"code": 200, "status": "Success", "id": "abc"},
            transport_error=None,
        )
        client = mock.Mock()
        client.API.post.return_value = response
        with mock.patch.object(self.provider.pool, "get", return_value=self._account()), mock.patch(
            "powersms.powersms_provider_lleidanet.Client", return_value=client
        ) as mocked_client:
            result = self.provider.send_sms_detailed_lleida(
                self.cursor, self.uid, 1, 2, "GISCE", "+34666666666", "legacy text"
            )
        client_args = mocked_client.call_args[1]
        sent = client.API.post.call_args[1]["json"]
        self.assertEqual(client_args["api_url"], "https://api.lleida.net/sms/v2/")
        self.assertEqual(client_args["api_key"], "secret-key")
        self.assertEqual(client_args["timeout"], 15)
        self.assertTrue(client_args["preserve_error_response"])
        self.assertTrue(client_args["capture_transport_errors"])
        self.assertEqual(sent["sms"]["user"], "legacy-user")
        self.assertNotIn("password", sent["sms"])
        self.assertTrue(result["accepted"])
        self.assertEqual(result["external_id"], "abc")

    def test_functional_and_transport_errors_are_preserved(self):
        response = mock.Mock(
            error=True,
            result={"code": 1504, "status": "Error", "message": "Temporary"},
            transport_error=None,
        )
        client = mock.Mock()
        client.API.post.return_value = response
        with mock.patch.object(self.provider.pool, "get", return_value=self._account()), mock.patch(
            "powersms.powersms_provider_lleidanet.Client", return_value=client
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

        timeout_response = mock.Mock(
            error=True,
            result={},
            code=None,
            message="timed out",
            transport_error="timeout",
        )
        client.API.post.return_value = timeout_response
        with mock.patch.object(self.provider.pool, "get", return_value=self._account()), mock.patch(
            "powersms.powersms_provider_lleidanet.Client", return_value=client
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
