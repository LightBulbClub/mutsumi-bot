import re

from core.builtins.bot import Bot

from ..database.models import ZzzUidBind


async def get_uid(
    msg: Bot.MessageSession,
    text: str = "",
    only_uid: bool = False,
) -> str | None:
    info = msg.session_info
    uid_data = re.findall(r"\d{8,10}", text)
    if uid_data:
        return uid_data[0]
    if only_uid:
        return await ZzzUidBind.get_main_uid(info.sender_id, info.client_name)
    return await ZzzUidBind.get_main_uid(info.sender_id, info.client_name)
