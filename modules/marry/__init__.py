import os
import random
from datetime import datetime

from core.builtins.bot import Bot
from core.builtins.message.internal import Image, Plain
from core.component import module
from core.constants.path import assets_path

from .database.models import TodayWifeInfo, TodayHusbandInfo

wif = module(
    "wife",
    {"waifu": "wife", "jrlp": "wife", "hlp": "wife change"},
    "获取今日二次元老婆",
    developers=["haoye_qwq"],
)

hsb = module(
    "husband",
    {"jrlg": "husband", "hlg": "husband change"},
    "获取今日二次元老公",
    developers=["haoye_qwq"],
)

assets = assets_path / "modules"

wife_names = os.listdir(assets / "wife")
husband_names = os.listdir(assets / "husband")


async def marry(msg: Bot.MessageSession, change: bool, is_husband: bool = False):
    _id = msg.session_info.sender_id
    names = husband_names if is_husband else wife_names
    chose = random.sample(names, 1)[0]
    db = (await TodayHusbandInfo.get_or_none(sender_id=_id)) \
     if is_husband else (await TodayWifeInfo.get_or_none(sender_id=_id))
    now = None
    if db and db.timestamp.date == datetime.date:
        if not change:
            now = db.wife_name if is_husband else db.husband_name
    if now:
        await msg.finish(
            [
                Plain(f"你今天的老{"公" if is_husband else "婆"}是"),
                Plain(now.split(".")[0]),
                Image(assets / wife_now),
            ]
        )
    _ = (await TodayWifeInfo.get_wife(sender_id=_id, name=chose)) \
     if not is_husband else (await TodayHusbandInfo.get_husband(sender_id=_id, name=chose))
    await msg.finish(
        [
            Plain(f"成功！你今天的老{"公" if is_husband else "婆"}是"),
            Plain(chose.split(".")[0]),
            Image(assets / chose),
        ]
    )


@hsb.command("{获取今日二次元老公}")
async def _(msg: Bot.MessageSession):
    await marry(msg, False, True)


@wif.command("{获取今日二次元老婆}")
async def _(msg: Bot.MessageSession):
    await marry(msg, False, False)


@hsb.command("change {换老公}")
async def _(msg: Bot.MessageSession):
    await marry(msg, True, True)

@wif.command("change {换老婆}")
async def _(msg: Bot.MessageSession):
    await marry(msg, True, False)
