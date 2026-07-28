from typing import Any

from PIL import Image, ImageDraw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement

from ..api import zzz_api
from ..utils.fonts import zzz_font_30, zzz_font_34, zzz_font_36, zzz_font_40, zzz_font_50
from ..utils.hint import error_reply
from ..utils.image import (
    GREY,
    YELLOW,
    add_footer,
    draw_bar,
    get_player_card_min,
    get_zzz_bg,
)
from ..utils.resource import TEXTURE2D_PATH

TEXT_PATH = TEXTURE2D_PATH / "zzzerouid_abyss"

COLLECT_MAP = {
    1: "鸣徽图鉴",
    2: "特殊区域记录",
    3: "哨站课题",
    4: "侵蚀研究",
    5: "旧都失物",
}


async def draw_hollow(msg: Bot.MessageSession, uid: str):
    data = await zzz_api.get_zzz_abyss_info(uid)
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    try:
        img = await _draw_hollow_image(msg, uid, data)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw hollow image")
        await _fallback_text(msg, uid, data)


async def _draw_hollow_image(
    msg: Bot.MessageSession,
    uid: str,
    data: dict,
) -> Image.Image:
    sender_name = msg.session_info.sender_name
    player_card = await get_player_card_min(uid, sender_name=sender_name)

    cur_level = data["abyss_level"]["cur_level"]
    max_level = data["abyss_level"]["max_level"]
    cur_talent = data["abyss_talent"]["cur_talent"]
    max_talent = data["abyss_talent"]["max_talent"]
    cur_duty = data["abyss_duty"]["cur_duty"]
    max_duty = data["abyss_duty"]["max_duty"]
    cur_point = data["abyss_point"]["cur_point"]
    max_point = data["abyss_point"]["max_point"]

    duty_bar = draw_bar("悬赏委托", cur_duty, max_duty)
    point_bar = draw_bar("调查点数", cur_point, max_point)

    bg = TEXT_PATH / "bg.jpg"
    data_banner = Image.open(TEXT_PATH / "data_banner.png")
    stage_banner = Image.open(TEXT_PATH / "stage_banner.png")
    level_bg = Image.open(TEXT_PATH / "level_bg.png")
    buff_bg = Image.open(TEXT_PATH / "buff_bg.png")
    level_draw = ImageDraw.Draw(level_bg)
    buff_draw = ImageDraw.Draw(buff_bg)

    level_draw.text((130, 130), f"/{max_level}", "white", zzz_font_34, "lm")
    level_draw.text((123, 126), f"{cur_level}", (255, 200, 1), zzz_font_50, "rm")

    buff_draw.text((130, 130), f"/{max_talent}", "white", zzz_font_34, "lm")
    buff_draw.text((123, 126), f"{cur_talent}", (255, 200, 1), zzz_font_50, "rm")

    img = get_zzz_bg(950, 1700, bg)

    for index, _d in enumerate(data["abyss_collect"]):
        bar = await _draw_data_bar(
            COLLECT_MAP.get(_d["type"], "未知数据"),
            _d["cur_collect"],
            _d["max_collect"],
        )
        img.paste(bar, (0, 824 + index * 87), bar)

    bar1 = await _draw_stage_bar("枯败花圃", data["abyss_nest"]["is_nest"])
    bar2 = await _draw_stage_bar("刀耕火焚", data["abyss_throne"]["is_throne"])

    for index, _s in enumerate([bar1, bar2]):
        img.paste(_s, (0, 1400 + index * 87), _s)

    img.paste(player_card, (0, 70), player_card)
    img.paste(data_banner, (0, 718), data_banner)
    img.paste(stage_banner, (0, 1278), stage_banner)
    img.paste(level_bg, (68, 289), level_bg)
    img.paste(buff_bg, (474, 289), buff_bg)
    img.paste(duty_bar, (0, 491), duty_bar)
    img.paste(point_bar, (0, 609), point_bar)

    img = add_footer(img)
    return img


async def _draw_data_bar(title: str, cur_value: Any, max_value: Any):
    bar = Image.open(TEXT_PATH / "data_bar.png")
    bar_draw = ImageDraw.Draw(bar)
    bar_draw.text((151, 49), f"{title}", GREY, zzz_font_36, "lm")
    bar_draw.text((765, 51), f"/{max_value}", GREY, zzz_font_30, "lm")
    bar_draw.text((757, 50), f"{cur_value}", YELLOW, zzz_font_40, "rm")
    return bar


async def _draw_stage_bar(title: str, value: bool):
    bar = Image.open(TEXT_PATH / "stage_bar.png")
    bar_draw = ImageDraw.Draw(bar)
    if value:
        _value = "已完成"
        _color = YELLOW
    else:
        _value = "尚未挑战"
        _color = GREY
    bar_draw.text((151, 49), f"{title}", GREY, zzz_font_36, "lm")
    bar_draw.text((817, 49), f"{_value}", _color, zzz_font_36, "rm")
    return bar


async def _fallback_text(msg: Bot.MessageSession, uid: str, data: dict):
    lines = [
        I18NContext("zzzerouid.message.hollow.title", uid=uid),
        "",
        I18NContext("zzzerouid.message.hollow.level"),
        I18NContext(
            "zzzerouid.message.hollow.level.current",
            cur=data.get("abyss_level", {}).get("cur_level", 0),
            max=data.get("abyss_level", {}).get("max_level", 0),
        ),
        "",
        I18NContext("zzzerouid.message.hollow.talent"),
        I18NContext(
            "zzzerouid.message.hollow.talent.current",
            cur=data.get("abyss_talent", {}).get("cur_talent", 0),
            max=data.get("abyss_talent", {}).get("max_talent", 0),
        ),
        "",
        I18NContext("zzzerouid.message.hollow.duty"),
        I18NContext(
            "zzzerouid.message.hollow.duty.current",
            cur=data.get("abyss_duty", {}).get("cur_duty", 0),
            max=data.get("abyss_duty", {}).get("max_duty", 0),
        ),
        "",
        I18NContext("zzzerouid.message.hollow.point"),
        I18NContext(
            "zzzerouid.message.hollow.point.current",
            cur=data.get("abyss_point", {}).get("cur_point", 0),
            max=data.get("abyss_point", {}).get("max_point", 0),
        ),
    ]

    collect = data.get("abyss_collect", [])
    if collect:
        lines.append("")
        lines.append(I18NContext("zzzerouid.message.hollow.collection"))
        for item in collect:
            item_type = item.get("type", 0)
            lines.append(
                I18NContext(
                    f"zzzerouid.message.hollow.collect.{item_type}",
                    cur=item.get("cur_collect", 0),
                    max=item.get("max_collect", 0),
                )
            )

    lines.extend(
        [
            "",
            I18NContext("zzzerouid.message.hollow.stages"),
            I18NContext(
                "zzzerouid.message.hollow.stage.withered",
                cleared="Yes" if data.get("abyss_nest", {}).get("is_nest", False) else "No",
            ),
            I18NContext(
                "zzzerouid.message.hollow.stage.flames",
                cleared="Yes" if data.get("abyss_throne", {}).get("is_throne", False) else "No",
            ),
        ]
    )

    await msg.finish(lines)
