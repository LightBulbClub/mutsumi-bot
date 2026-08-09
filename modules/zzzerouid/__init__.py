from core.builtins.bot import Bot
from core.component import module

from .commands.ann import clear_ann
from .commands.char_detail import draw_card, refresh_card
from .commands.char_list import draw_roster
from .commands.challenge import draw_challenge
from .commands.cookie import set_cookie, set_stoken
from .commands.download import download_assets
from .commands.user import bind_uid, switch_uid, unbind_uid
from .commands.gachalog import draw_gacha, refresh_gacha
from .commands.help import send_guide, send_help
from .commands.hollow import draw_hollow
from .commands.mem import draw_mem
from .commands.month_info import draw_month_info
from .commands.roleinfo import draw_role_info
from .commands.stamina import draw_stamina
from .commands.void import draw_void
from .utils.hint import BIND_UID_HINT
from .utils.uid import get_uid

zzz = module(
    "zzz",
    alias="zenless",
    developers=["SoftGreyMon", "haoye_qwq"],
    support_languages=["zh_cn", "en_us"],
    desc="{I18N:zzzerouid.help.desc}",
    doc=True,
)

@zzz.command("bind uid <uid> {I18N:zzzerouid.help.bind.uid}")
async def _(msg: Bot.MessageSession, uid: str):
    await bind_uid(msg, uid)


@zzz.command("switch uid [uid] {I18N:zzzerouid.help.switch.uid}")
async def _(msg: Bot.MessageSession, uid: str = None):
    await switch_uid(msg, uid)


@zzz.command("unbind uid <uid> {I18N:zzzerouid.help.unbind.uid}")
async def _(msg: Bot.MessageSession, uid: str):
    await unbind_uid(msg, uid)


@zzz.command("set cookie <uid> <cookie> {I18N:zzzerouid.help.set.cookie}")
async def _(msg: Bot.MessageSession, uid: str, cookie: str):
    await set_cookie(msg, uid, cookie)


@zzz.command("set stoken <uid> <stoken> {I18N:zzzerouid.help.set.stoken}")
async def _(msg: Bot.MessageSession, uid: str, stoken: str):
    await set_stoken(msg, uid, stoken)


@zzz.command("info {I18N:zzzerouid.help.info}")
async def _(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(BIND_UID_HINT)
    await draw_role_info(msg, uid)


@zzz.command("stamina {I18N:zzzerouid.help.stamina}")
@zzz.command("note {I18N:zzzerouid.help.note}")
async def _(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(BIND_UID_HINT)
    await draw_stamina(msg, uid)


@zzz.command("challenge {I18N:zzzerouid.help.challenge}")
@zzz.command("abyss {I18N:zzzerouid.help.abyss}")
async def _(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(BIND_UID_HINT)
    await draw_challenge(msg, uid)


@zzz.command("hollow {I18N:zzzerouid.help.hollow}")
@zzz.command("zero {I18N:zzzerouid.help.zero}")
async def _(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(BIND_UID_HINT)
    await draw_hollow(msg, uid)


@zzz.command("mem {I18N:zzzerouid.help.mem}")
@zzz.command("dangerous {I18N:zzzerouid.help.dangerous}")
async def _(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(BIND_UID_HINT)
    await draw_mem(msg, uid)


@zzz.command("void {I18N:zzzerouid.help.void}")
@zzz.command("critical {I18N:zzzerouid.help.critical}")
async def _(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(BIND_UID_HINT)
    await draw_void(msg, uid)


@zzz.command("monthly [month] {I18N:zzzerouid.help.monthly}")
@zzz.command("ledger [month] {I18N:zzzerouid.help.ledger}")
async def _(msg: Bot.MessageSession, month: str = ""):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(BIND_UID_HINT)
    await draw_month_info(msg, uid, month)


@zzz.command("refresh gacha {I18N:zzzerouid.help.refresh_gacha}")
async def _(msg: Bot.MessageSession):
    await refresh_gacha(msg)


@zzz.command("gacha {I18N:zzzerouid.help.gacha}")
async def _(msg: Bot.MessageSession):
    await draw_gacha(msg)


@zzz.command("refresh card <character> {I18N:zzzerouid.help.refresh_card}")
async def _(msg: Bot.MessageSession, character: str):
    await refresh_card(msg, character)


@zzz.command("card <character> {I18N:zzzerouid.help.card}")
@zzz.command("character <character> {I18N:zzzerouid.help.character}")
async def _(msg: Bot.MessageSession, character: str):
    await draw_card(msg, character)


@zzz.command("roster {I18N:zzzerouid.help.roster}")
@zzz.command("characters {I18N:zzzerouid.help.characters}")
async def _(msg: Bot.MessageSession):
    await draw_roster(msg)


@zzz.command("guide <character> {I18N:zzzerouid.help.guide}")
async def _(msg: Bot.MessageSession, character: str):
    await send_guide(msg, character)


@zzz.command("ann {I18N:zzzerouid.help.ann}")
async def _(msg: Bot.MessageSession):
    await clear_ann(msg)


@zzz.command("download {I18N:zzzerouid.help.download}")
@zzz.command("update assets {I18N:zzzerouid.help.update_assets}")
async def _(msg: Bot.MessageSession):
    await download_assets(msg)


@zzz.command("help {I18N:zzzerouid.help.help}")
async def _(msg: Bot.MessageSession):
    await send_help(msg)
