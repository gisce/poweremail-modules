# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from destral import testing
from destral.transaction import Transaction


class TestProviders(testing.OOTestCase):
    def test_provider_code_implementation(self):
        with Transaction().start(self.database) as txn:
            cursor, uid, pool = txn.cursor, txn.user, txn.pool
            provider_obj = pool.get("powersms.provider")
            providers = provider_obj.search(cursor, uid, [], context={"active_test": False})
            self.assertTrue(providers)
            for p_id in providers:
                self.assertTrue(
                    hasattr(provider_obj, provider_obj._get_provider_function(cursor, uid, p_id))
                )

    def test_provider_code_implementation_reverse(self):
        with Transaction().start(self.database) as txn:
            cursor, uid, pool = txn.cursor, txn.user, txn.pool
            provider_obj = pool.get("powersms.provider")
            provider_pattern_methods = [
                method
                for method in dir(provider_obj)
                if method.startswith("send_sms_")
                and method not in ("send_sms_default", "send_sms_detailed")
            ]
            self.assertTrue(provider_pattern_methods)
            for method in provider_pattern_methods:
                self.assertTrue(
                    provider_obj.search(
                        cursor,
                        uid,
                        [("function_pattern_code", "=", method.replace("send_sms_", ""))],
                    )
                )


class TestProviderDetailedContract(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestProviderDetailedContract, self).setUp()
        self.provider_obj = self.pool.get("powersms.provider")
        self.provider_id = self.provider_obj.search(
            self.cursor,
            self.uid,
            [("function_pattern_code", "=", "lleida")],
            context={"active_test": False},
        )[0]

    def test_normalizes_legacy_boolean(self):
        accepted = self.provider_obj.normalize_send_result(True)
        rejected = self.provider_obj.normalize_send_result(False)

        self.assertTrue(accepted["accepted"])
        self.assertFalse(rejected["accepted"])
        self.assertEqual(accepted["provider_code"], "")
        self.assertFalse(accepted["retryable"])

    def test_preserves_structured_provider_data(self):
        result = self.provider_obj.normalize_send_result(
            {
                "accepted": True,
                "provider_code": "202",
                "provider_message": "Accepted",
                "external_id": "sms-42",
                "retryable": False,
                "raw_response": "sanitized response",
                "provider_private_field": "not part of the contract",
            }
        )

        self.assertEqual(
            result,
            {
                "accepted": True,
                "provider_code": "202",
                "provider_message": "Accepted",
                "external_id": "sms-42",
                "retryable": False,
                "raw_response": "sanitized response",
            },
        )

    def test_falls_back_to_legacy_provider(self):
        with mock.patch.object(self.provider_obj, "send_sms", return_value=True) as legacy_send:
            result = self.provider_obj.send_sms_detailed(
                self.cursor,
                self.uid,
                self.provider_id,
                7,
                "GISCE",
                "+34600000000",
                body="test",
            )

        self.assertTrue(result["accepted"])
        legacy_send.assert_called_once_with(
            self.cursor,
            self.uid,
            self.provider_id,
            7,
            "GISCE",
            "+34600000000",
            body="test",
            files=None,
            context=None,
        )

    def test_uses_optional_provider_hook(self):
        detailed_result = {
            "accepted": True,
            "provider_code": "queued",
            "external_id": "sms-84",
        }

        with mock.patch.object(
            self.provider_obj,
            "send_sms_detailed_lleida",
            return_value=detailed_result,
            create=True,
        ) as detailed_send:
            result = self.provider_obj.send_sms_detailed(
                self.cursor,
                self.uid,
                self.provider_id,
                7,
                "GISCE",
                "+34600000000",
                body="test",
            )

        self.assertTrue(result["accepted"])
        self.assertEqual(result["provider_code"], "queued")
        self.assertEqual(result["external_id"], "sms-84")
        detailed_send.assert_called_once_with(
            self.cursor,
            self.uid,
            self.provider_id,
            7,
            "GISCE",
            "+34600000000",
            "test",
            None,
            context=None,
        )

    def test_account_exposes_detailed_provider_result(self):
        model_data_obj = self.pool.get("ir.model.data")
        account_id = model_data_obj.get_object_reference(
            self.cursor, self.uid, "powersms", "sms_account_001"
        )[1]
        account_obj = self.pool.get("powersms.core_accounts")
        account_obj.write(
            self.cursor,
            self.uid,
            [account_id],
            {"provider_id": self.provider_id},
        )
        detailed_result = {
            "accepted": True,
            "provider_code": "queued",
            "provider_message": "Accepted",
            "external_id": "sms-126",
            "retryable": False,
            "raw_response": "",
        }

        with mock.patch.object(
            self.provider_obj, "send_sms_detailed", return_value=detailed_result
        ) as detailed_send:
            result = account_obj.send_sms_detailed(
                self.cursor,
                self.uid,
                [account_id],
                "GISCE",
                "600000000",
                body="test",
            )

        self.assertEqual(result, detailed_result)
        detailed_send.assert_called_once_with(
            self.cursor,
            self.uid,
            self.provider_id,
            account_id,
            "GISCE",
            "600000000",
            body="test",
            files=[],
            context={},
        )
