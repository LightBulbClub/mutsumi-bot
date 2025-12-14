import os
import random
from datetime import datetime

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image, Plain
from core.component import module
from core.constants.path import assets_path

from .database.models import TodayHusbandInfo

hsb = module(
    "husband",
    {"jrlg": "husband", "hlg": "husband change"},
    "获取今日二次元老公",
    developers=["haoye_qwq"],
)

assets = assets_path / "modules" / "husband"

husband_names = os.listdir(assets)


async def husband(msg: Bot.MessageSession, change: bool):
    _id = msg.session_info.sender_id
    chose = random.sample(husband_names, 1)[0]
    db = await TodayHusbandInfo.get_or_none(sender_id=_id)
    husband_now = None
    if db and db.timestamp.date == datetime.date:
        if not change:
            husband_now = db.husband_name
    if husband_now:
        await msg.finish(
            [
                Plain("你今天的老婆是"),
                Plain(husband_now.split(".")[0]),
                Image(assets / husband_now),
            ]
        )
    _ = await TodayHusbandInfo.get_husband(sender_id=_id, name=chose)
    await msg.finish(
        [
            Plain("成功！你今天的老婆是"),
            Plain(chose.split(".")[0]),
            Image(assets / chose),
        ]
    )


@hsb.command("{获取今日二次元老公}")
async def _(msg: Bot.MessageSession):
    await husband(msg, False)


@hsb.command("change {换老公}")
async def _(msg: Bot.MessageSession):
    await husband(msg, True)
