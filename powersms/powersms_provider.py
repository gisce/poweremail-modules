from __future__ import absolute_import, unicode_literals
from osv import osv, fields
from tools.translate import _


class PowersmsProvider(osv.osv):
    _name = "powersms.provider"

    detailed_result_keys = (
        "accepted",
        "provider_code",
        "provider_message",
        "external_id",
        "retryable",
        "raw_response",
    )

    def _get_provider_function(self, cursor, uid, _id, context=None):
        function_pattern = self.read(cursor, uid, _id, ["function_pattern_code"], context=context)[
            "function_pattern_code"
        ]
        return "send_sms_{function_pattern}".format(function_pattern=function_pattern)

    def send_sms_default(
        self, cursor, uid, _id, account_id, from_name, numbers_to, body="", files=None, context=None
    ):
        function_name = self._get_provider_function(cursor, uid, _id, context=context)
        raise osv.except_osv(
            _("Programing Error"), _("Method {} not defined".format(function_name))
        )

    def send_sms(
        self, cursor, uid, _id, account_id, from_name, numbers_to, body="", files=None, context=None
    ):
        if isinstance(_id, (tuple, list)):
            if len(_id) != 1:
                raise osv.except_osv(
                    _("Programing Error"), _("Multiple providers to send same sms")
                )
            _id = _id[0]

        function_name = self._get_provider_function(cursor, uid, _id, context=context)

        return getattr(self, function_name, self.send_sms_default)(
            cursor, uid, _id, account_id, from_name, numbers_to, body, files, context=context
        )

    def normalize_send_result(self, result):
        """Return the optional provider result using the common contract.

        Legacy providers may keep returning any truthy/falsey value. Detailed
        providers return a dict and may omit fields they cannot supply.
        """
        normalized = dict((key, False) for key in self.detailed_result_keys)
        normalized.update(
            {
                "provider_code": "",
                "provider_message": "",
                "external_id": "",
                "raw_response": "",
            }
        )
        if isinstance(result, dict):
            for key in self.detailed_result_keys:
                if key in result:
                    normalized[key] = result[key]
            normalized["accepted"] = bool(normalized["accepted"])
            normalized["retryable"] = bool(normalized["retryable"])
        else:
            normalized["accepted"] = bool(result)
        return normalized

    def send_sms_detailed(
        self, cursor, uid, _id, account_id, from_name, numbers_to, body="", files=None, context=None
    ):
        """Send an SMS and always return the optional detailed result.

        Providers can opt in by implementing ``send_sms_detailed_<code>``.
        Providers implementing only the legacy ``send_sms_<code>`` hook are
        called through ``send_sms`` and their result is normalized here.
        """
        if isinstance(_id, (tuple, list)):
            if len(_id) != 1:
                raise osv.except_osv(
                    _("Programing Error"), _("Multiple providers to send same sms")
                )
            _id = _id[0]

        function_pattern = self.read(
            cursor, uid, _id, ["function_pattern_code"], context=context
        )["function_pattern_code"]
        detailed_function = getattr(
            self, "send_sms_detailed_{}".format(function_pattern), None
        )
        if detailed_function is None:
            result = self.send_sms(
                cursor,
                uid,
                _id,
                account_id,
                from_name,
                numbers_to,
                body=body,
                files=files,
                context=context,
            )
        else:
            result = detailed_function(
                cursor,
                uid,
                _id,
                account_id,
                from_name,
                numbers_to,
                body,
                files,
                context=context,
            )
        return self.normalize_send_result(result)

    _columns = {
        "name": fields.char("Provider", size=64, required=True),
        "function_pattern_code": fields.char(
            "Function pattern definition",
            size=16,
            required=True,
            help=_("Function must be defined as def send_sms_{function_pattern_code}"),
        ),
    }
    _sql_constraints = [
        ("name_uniq", "unique (name)", "Provider must be unique"),
        ("code_uniq", "unique (function_pattern_code)", "Function pattern must be unique"),
    ]


PowersmsProvider()
