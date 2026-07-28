from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext

from ..database.models import ZzzUidBind
from ..utils.message import send_diff_msg


async def bind_uid(msg: Bot.MessageSession, uid: str):
    info = msg.session_info
    result = await ZzzUidBind.insert_uid(info.sender_id, info.client_name, uid)
    await send_diff_msg(
        msg,
        result,
        {
            0: I18NContext("zzzerouid.message.bind.success", uid=uid),
            -1: I18NContext("zzzerouid.message.bind.invalid_uid", uid=uid),
            -2: I18NContext("zzzerouid.message.bind.already_bound", uid=uid),
            -3: I18NContext("zzzerouid.message.bind.invalid_format"),
        },
    )


async def switch_uid(msg: Bot.MessageSession, uid: str | None):
    info = msg.session_info
    if uid:
        result = await ZzzUidBind.switch_uid(info.sender_id, info.client_name, uid)
    else:
        binds = await ZzzUidBind.filter(sender_id=info.sender_id, bot_id=info.client_name).all()
        if len(binds) < 2:
            result = -2
        else:
            result = -3
    await send_diff_msg(
        msg,
        result,
        {
            0: I18NContext("zzzerouid.message.switch.success", uid=uid),
            -1: I18NContext("zzzerouid.message.switch.no_record"),
            -2: I18NContext("zzzerouid.message.switch.need_two_uids"),
            -3: I18NContext("zzzerouid.message.switch.need_two_uids"),
        },
    )


async def unbind_uid(msg: Bot.MessageSession, uid: str):
    info = msg.session_info
    result = await ZzzUidBind.delete_uid(info.sender_id, info.client_name, uid)
    await send_diff_msg(
        msg,
        result,
        {
            0: I18NContext("zzzerouid.message.unbind.success", uid=uid),
            -1: I18NContext("zzzerouid.message.unbind.not_found", uid=uid),
        },
    )
