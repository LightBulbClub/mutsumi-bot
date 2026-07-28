from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext

from ..database.models import ZzzCookie


async def set_cookie(msg: Bot.MessageSession, uid: str, cookie: str):
    await ZzzCookie.update_or_create(
        defaults={"cookie": cookie},
        uid=uid,
    )
    await msg.finish(I18NContext("zzzerouid.message.cookie.set_success", uid=uid))


async def set_stoken(msg: Bot.MessageSession, uid: str, stoken: str):
    cookie = await ZzzCookie.get_or_none(uid=uid)
    if not cookie:
        await msg.finish(I18NContext("zzzerouid.message.cookie_missing"))
    cookie.stoken = stoken
    await cookie.save()
    await msg.finish(I18NContext("zzzerouid.message.stoken.set_success", uid=uid))
