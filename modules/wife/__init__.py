import os
import random
from datetime import datetime

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image, Plain
from core.component import module
from core.constants.path import assets_path

from .database.models import TodayWifeInfo

wif = module(
    "wife",
    {"waifu": "wife", "jrlp": "wife", "hlp": "wife change"},
    "获取今日二次元老婆",
    developers=["haoye_qwq"],
)

assets = assets_path / "modules" / "wife"

wife_names = os.listdir(assets)


async def waifu(msg: Bot.MessageSession, change_: bool):
    change = change_
    _id = msg.session_info.sender_id
    chose = random.sample(wife_names, 1)[0]
    db = await TodayWifeInfo.get_or_none(sender_id=_id)
    wife_now = None
    if db:
        if db.timestamp.date != datetime.date:
            change = True
        else:
            wife_now = db.wife_name
    if change or not db:
        if await TodayWifeInfo.get_wife(sender_id=_id, name=chose):
            await msg.finish(
                [
                    Plain("成功！你今天的老婆是"),
                    Plain(chose.split(".")[0]),
                    Image(assets / chose),
                ]
            )
        await msg.finish(
            [
                Plain("失败！你今天换老婆次数太多了，你今天的老婆只能是"),
                Plain(wife_now.split(".")[0]),
                Image(assets / wife_now),
            ]
        )
    await msg.finish(
        [
            Plain("你今天的老婆是"),
            Plain(wife_now.split(".")[0]),
            Image(assets / wife_now),
        ]
    )


@wif.command("{获取今日二次元老婆}")
async def _(msg: Bot.MessageSession):
    await waifu(msg, False)


@wif.command("change {换老婆}")
async def _(msg: Bot.MessageSession):
    await waifu(msg, True)
