from core.builtins.message.elements import I18NContextElement
from core.builtins.message.internal import I18NContext

BIND_UID_HINT = I18NContext("zzzerouid.message.bind_uid_hint")

ERROR_CODE = {
    -51: "zzzerouid.message.error.cookie_missing",
    -100: "zzzerouid.message.error.cookie_expired",
    -503: "zzzerouid.message.error.cookie_invalid",
    10001: "zzzerouid.message.error.cookie_expired",
    10101: "zzzerouid.message.error.query_limit",
    10102: "zzzerouid.message.error.privacy",
    1034: "zzzerouid.message.error.captcha",
    -10001: "zzzerouid.message.error.request_error",
    -201: "zzzerouid.message.error.account_banned",
    1008: "zzzerouid.message.error.no_cookie_bound",
    10104: "zzzerouid.message.error.cookie_mismatch",
    -999: "zzzerouid.message.error.verification_failed",
    -501002: "zzzerouid.message.error.user_data_private",
    10110: "zzzerouid.message.error.no_character",
}


def error_reply(retcode: int) -> I18NContextElement:
    key = ERROR_CODE.get(retcode, "zzzerouid.message.error.unknown")
    return I18NContext(key, code=retcode)
