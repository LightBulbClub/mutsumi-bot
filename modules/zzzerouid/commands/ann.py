from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext

from ..api import zzz_api
from ..utils.hint import error_reply
from ..utils.uid import get_uid


async def clear_ann(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(I18NContext("zzzerouid.message.bind_uid_hint"))
        return

    data = await zzz_api.get_zzz_ann(uid, _type="getAnnList")
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    ann_list = data.get("list", [])
    for ann in ann_list:
        ann_id = ann.get("ann_id")
        if ann_id:
            await zzz_api.get_zzz_ann(uid, _type="consumeRemind", ann_id=ann_id)

    await msg.finish(I18NContext("zzzerouid.message.ann.done"))
