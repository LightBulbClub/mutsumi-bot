import os

from core.builtins.bot import Bot
from core.builtins.message.internal import Image, Plain
from core.component import module
from core.constants.path import assets_path
from core.utils.random import Random

from .database.models import MarryDeck, TodayHusbandInfo, TodayWifeInfo

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
    sender_id = msg.session_info.sender_id
    kind = "husband" if is_husband else "wife"
    names = husband_names if is_husband else wife_names
    info_model = TodayHusbandInfo if is_husband else TodayWifeInfo

    # 非更换时，今天已经抽过就直接沿用；否则从牌堆里新抽一张。
    chosen = None if change else await info_model.get_today(sender_id)
    if chosen:
        await msg.send_message(
            [
                Plain(f"你今天的老{"公" if is_husband else "婆"}是"),
                Plain(chosen),
            ]
        )
    else:
        # 牌堆随机抽牌：每张牌概率相等，且牌堆抽空前不会重复。
        chosen = await MarryDeck.draw(sender_id=sender_id, is_husband=is_husband, names=names)
        await info_model.set_today(sender_id, chosen)
        await msg.send_message(
            [
                Plain(f"成功！你今天的老{"公" if is_husband else "婆"}是"),
                Plain(chosen),
            ]
        )

    chosen_files = os.listdir(assets / kind / chosen)
    await msg.finish(Image(assets / kind / chosen / Random.choice(chosen_files)))


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
