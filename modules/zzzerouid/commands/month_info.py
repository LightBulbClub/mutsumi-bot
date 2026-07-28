from PIL import Image, ImageDraw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement

from ..api import zzz_api
from ..utils.fonts import zzz_font_24, zzz_font_28, zzz_font_30, zzz_font_42, zzz_font_58
from ..utils.hint import error_reply
from ..utils.image import (
    BLACK_G,
    GREY,
    add_footer,
    get_player_card_min,
    get_zzz_bg,
)
from ..utils.resource import TEXTURE2D_PATH

TEXT_PATH = TEXTURE2D_PATH / "zzzerouid_month_info"

ACTION_MAP = {
    "daily_activity_rewards": "日常活跃奖励",
    "mail_rewards": "邮件奖励",
    "growth_rewards": "成长奖励",
    "event_rewards": "活动奖励",
    "hollow_rewards": "零号空洞奖励",
    "shiyu_rewards": "式舆防卫战奖励",
    "other_rewards": "其他奖励",
}

COLOR_MAP = {
    "daily_activity_rewards": (74, 191, 53),
    "mail_rewards": (189, 67, 225),
    "growth_rewards": (190, 225, 67),
    "event_rewards": (67, 108, 225),
    "hollow_rewards": (109, 29, 149),
    "shiyu_rewards": (225, 67, 67),
    "other_rewards": (197, 143, 62),
}


async def draw_month_info(msg: Bot.MessageSession, uid: str, month: str = ""):
    data = await zzz_api.get_zzz_month_info(uid, month)
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    try:
        img = await _draw_month_image(msg, uid, data)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw month info image")
        await _fallback_text(msg, uid, data)


async def _draw_month_image(
    msg: Bot.MessageSession,
    uid: str,
    data: dict,
) -> Image.Image:
    sender_name = msg.session_info.sender_name
    player_card = await get_player_card_min(uid, sender_name=sender_name)

    data_month = data["data_month"]
    data_month_str = data_month[:4] + "-" + data_month[4:]
    month_data = data["month_data"]

    img = get_zzz_bg(950, 1800)
    fg = Image.open(TEXT_PATH / "fg.png")
    img.paste(player_card, (0, 75), player_card)
    img.paste(fg, (0, 0), fg)
    img_draw = ImageDraw.Draw(img)

    img_draw.text(
        (205, 366),
        "绳网月报",
        "white",
        zzz_font_58,
        "lm",
    )
    img_draw.text(
        (205, 413),
        data_month_str,
        GREY,
        zzz_font_30,
        "lm",
    )

    for i in month_data["list"]:
        _count = i["count"]
        if i["data_type"] == "PolychromesData":
            pos = (246, 811)
        elif i["data_type"] == "MatserTapeData":
            pos = (476, 811)
        elif i["data_type"] == "BooponsData":
            pos = (707, 811)
        else:
            pos = (0, 0)

        img_draw.text(
            pos,
            str(_count),
            BLACK_G,
            zzz_font_42,
            "mm",
        )

    for index, j in enumerate(month_data["income_components"]):
        line = Image.new("RGBA", (950, 82))
        action = ACTION_MAP.get(j["action"], "未知奖励")
        line_draw = ImageDraw.Draw(line)
        line_draw.text(
            (143, 32),
            action,
            GREY,
            zzz_font_28,
            "lm",
        )
        x1, _, x2, _ = zzz_font_28.getbbox(action)
        x = x2 - x1

        line_draw.text(
            (150 + x, 33),
            f"{j['percent']}%",
            GREY,
            zzz_font_24,
            "lm",
        )
        line_draw.text(
            (804, 35),
            f"{j['num']}",
            "white",
            zzz_font_28,
            "rm",
        )

        lenth = 670
        percent_lenth = int(lenth * (j["percent"] / 100))

        line_draw.rounded_rectangle(
            (141, 55, 141 + lenth, 65),
            60,
            (100, 100, 100, 125),
        )
        line_draw.rounded_rectangle(
            (141, 55, 141 + percent_lenth, 65),
            60,
            COLOR_MAP.get(j["action"], (225, 67, 67)),
        )
        img.paste(line, (0, 981 + index * 82), line)

    img_draw.text(
        (475, 1636),
        "*注意，所有数据会有两小时左右的延迟",
        GREY,
        zzz_font_24,
        "mm",
    )
    img = add_footer(img)
    return img


async def _fallback_text(msg: Bot.MessageSession, uid: str, data: dict):
    data_month = data.get("data_month", "")
    month_data = data.get("month_data", {})
    display_month = f"{data_month[:4]}-{data_month[4:]}" if len(data_month) >= 6 else data_month

    lines = [
        I18NContext("zzzerouid.message.monthly.title", uid=uid),
        "",
        I18NContext("zzzerouid.message.monthly.data_month", month=display_month),
        "",
    ]

    for item in month_data.get("list", []):
        data_type = item.get("data_type", "")
        if data_type == "PolychromesData":
            lines.append(I18NContext("zzzerouid.message.monthly.polychromes", count=item.get("count", 0)))
        elif data_type == "MatserTapeData":
            lines.append(I18NContext("zzzerouid.message.monthly.master_tapes", count=item.get("count", 0)))
        elif data_type == "BooponsData":
            lines.append(I18NContext("zzzerouid.message.monthly.boopons", count=item.get("count", 0)))

    income = month_data.get("income_components", [])
    if income:
        lines.extend(["", I18NContext("zzzerouid.message.monthly.income_breakdown")])
        for item in income:
            action = item.get("action", "")
            lines.append(
                I18NContext(
                    f"zzzerouid.message.monthly.income.{action}",
                    num=item.get("num", 0),
                    percent=item.get("percent", 0),
                )
            )

    lines.extend(
        [
            "",
            I18NContext("zzzerouid.message.monthly.delay_note"),
        ]
    )

    await msg.finish(lines)
