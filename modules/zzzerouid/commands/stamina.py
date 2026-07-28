from PIL import Image, ImageDraw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement

from ..api import zzz_api
from ..utils.fonts import zzz_font_26, zzz_font_36, zzz_font_40, zzz_font_50
from ..utils.hint import error_reply
from ..utils.image import (
    GREY,
    YELLOW,
    add_footer,
    get_player_card_min,
    get_zzz_bg,
)
from ..utils.resource import TEXTURE2D_PATH

TEXT_PATH = TEXTURE2D_PATH / "zzzerouid_stamina"
YES = Image.open(TEXT_PATH / "yes.png")
NO = Image.open(TEXT_PATH / "no.png")


async def draw_stamina(msg: Bot.MessageSession, uid: str):
    data = await zzz_api.get_zzz_note_info(uid)
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    try:
        img = await _draw_stamina_image(msg, uid, data)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw stamina image")
        await _fallback_text(msg, uid, data)


async def _draw_stamina_image(
    msg: Bot.MessageSession,
    uid: str,
    data: dict,
) -> Image.Image:
    sender_name = msg.session_info.sender_name
    player_card = await get_player_card_min(uid, sender_name=sender_name)

    energy = data["energy"]["progress"]
    max_energy = energy["max"]
    current_energy = energy["current"]
    radio = current_energy / max_energy
    max_len = 386
    restore = data["energy"]["restore"]
    rh, rm = _convert_seconds_to_hm(restore)
    restore_str = f"{rh}小时{rm}分钟"

    vitality = data["vitality"]["current"]
    max_vitality = data["vitality"]["max"]
    vitality_icon = YES if vitality >= max_vitality else NO

    vhs_sale = data["vhs_sale"]["sale_state"]
    if "Doing" in vhs_sale:
        sale_icon = YES
        sale_text = "正在营业"
    else:
        sale_icon = NO
        sale_text = "尚未营业"

    card_sign = data["card_sign"]
    if "Done" in card_sign:
        card_icon = YES
        card_text = "已抽奖"
    else:
        card_icon = NO
        card_text = "未抽奖"

    bounty = data.get("s2_bounty_commission") or data.get("s1_bounty_commission")
    if bounty:
        cnum = bounty["num"]
        ctotal = bounty["total"]
        bounty_icon = YES if cnum >= ctotal else NO
    else:
        cnum = "-"
        ctotal = "-"
        bounty_icon = NO

    weekly = data.get("weekly_task")
    if weekly:
        wnum = weekly["cur_point"]
        wtotal = weekly["max_point"]
        weekly_icon = YES if wnum >= wtotal else NO
    else:
        wnum = "-"
        wtotal = "-"
        weekly_icon = NO

    img = get_zzz_bg(950, 1700)
    bg = Image.open(TEXT_PATH / "bg.png")
    battery_banner = Image.open(TEXT_PATH / "battery_banner.png")
    active_banner = Image.open(TEXT_PATH / "active_banner.png")
    abyss_banner = Image.open(TEXT_PATH / "abyss_banner.png")
    battery_card = Image.open(TEXT_PATH / "battery_card.png")

    active_bar = Image.open(TEXT_PATH / "bar.png")
    active_draw = ImageDraw.Draw(active_bar)
    gacha_bar = Image.open(TEXT_PATH / "bar.png")
    gacha_draw = ImageDraw.Draw(gacha_bar)
    shop_bar = Image.open(TEXT_PATH / "bar.png")
    shop_draw = ImageDraw.Draw(shop_bar)
    mission_bar = Image.open(TEXT_PATH / "bar.png")
    mission_draw = ImageDraw.Draw(mission_bar)
    point_bar = Image.open(TEXT_PATH / "bar.png")
    point_draw = ImageDraw.Draw(point_bar)
    battery_draw = ImageDraw.Draw(battery_card)

    active_draw.text((188, 51), "今日活跃度", GREY, zzz_font_40, "lm")
    gacha_draw.text((188, 51), "刮刮卡", GREY, zzz_font_40, "lm")
    shop_draw.text((188, 51), "录像店经营", GREY, zzz_font_40, "lm")
    mission_draw.text((188, 51), "悬赏委托", GREY, zzz_font_40, "lm")
    point_draw.text((188, 51), "丽都周纪", GREY, zzz_font_40, "lm")

    active_bar.paste(vitality_icon, (93, 10), vitality_icon)
    gacha_bar.paste(card_icon, (93, 10), card_icon)
    shop_bar.paste(sale_icon, (93, 10), sale_icon)
    mission_bar.paste(bounty_icon, (93, 10), bounty_icon)
    point_bar.paste(weekly_icon, (93, 10), weekly_icon)

    active_draw.text((716, 56), f"/{max_vitality}", GREY, zzz_font_40, "lm")
    active_draw.text((708, 54), f"{vitality}", YELLOW, zzz_font_50, "rm")

    mission_draw.text((716, 56), f"/{ctotal}", GREY, zzz_font_40, "lm")
    mission_draw.text((708, 54), f"{cnum}", YELLOW, zzz_font_50, "rm")

    point_draw.text((716, 56), f"/{wtotal}", GREY, zzz_font_40, "lm")
    point_draw.text((708, 54), f"{wnum}", YELLOW, zzz_font_50, "rm")

    gacha_draw.text((826, 50), card_text, YELLOW, zzz_font_50, "rm")
    shop_draw.text((826, 50), sale_text, YELLOW, zzz_font_50, "rm")

    battery_draw.text(
        (565, 111),
        f"/{max_energy}",
        (165, 165, 165),
        zzz_font_36,
        "lm",
    )
    battery_draw.text(
        (517, 108),
        f"{current_energy}",
        YELLOW,
        zzz_font_50,
        "mm",
    )
    battery_draw.text(
        (454, 152),
        f"{restore_str}",
        "white",
        zzz_font_26,
        "lm",
    )
    battery_draw.rounded_rectangle(
        (415, 230, int(415 + radio * max_len), 246),
        20,
        YELLOW,
    )

    img.paste(bg, (0, 0), bg)
    img.paste(player_card, (0, 224), player_card)
    img.paste(battery_banner, (0, 402), battery_banner)
    img.paste(active_banner, (0, 849), active_banner)
    img.paste(battery_card, (0, 511), battery_card)
    img.paste(abyss_banner, (0, 1264), abyss_banner)

    for index, i in enumerate([active_bar, shop_bar, gacha_bar]):
        img.paste(i, (0, 961 + index * 101), i)

    for index, i in enumerate([mission_bar, point_bar]):
        img.paste(i, (0, 1368 + index * 101), i)

    img = add_footer(img)
    return img


def _convert_seconds_to_hm(seconds: int):
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    minutes = remaining_seconds // 60
    return hours, minutes


async def _fallback_text(msg: Bot.MessageSession, uid: str, data: dict):
    energy = data.get("energy", {})
    vitality = data.get("vitality", {})
    vhs_sale = data.get("vhs_sale", {})
    card_sign = data.get("card_sign", "None")

    lines = [
        I18NContext("zzzerouid.message.stamina.title", uid=uid),
        "",
        I18NContext("zzzerouid.message.stamina.battery"),
        I18NContext(
            "zzzerouid.message.stamina.battery.current",
            current=energy.get("progress", {}).get("current", 0),
            max=energy.get("progress", {}).get("max", 0),
        ),
        I18NContext(
            "zzzerouid.message.stamina.battery.restore",
            restore=_format_seconds(energy.get("restore", 0)),
        ),
        "",
        I18NContext("zzzerouid.message.stamina.vitality"),
        I18NContext(
            "zzzerouid.message.stamina.vitality.current",
            current=vitality.get("current", 0),
            max=vitality.get("max", 0),
        ),
        "",
        I18NContext("zzzerouid.message.stamina.card_sign"),
        I18NContext("zzzerouid.message.stamina.card_sign.state", state=card_sign),
        "",
        I18NContext("zzzerouid.message.stamina.vhs_sale"),
        I18NContext(
            "zzzerouid.message.stamina.vhs_sale.state",
            state=vhs_sale.get("sale_state", "Unknown"),
        ),
    ]

    bounty = data.get("s2_bounty_commission") or data.get("s1_bounty_commission")
    if bounty:
        lines.extend(
            [
                "",
                I18NContext("zzzerouid.message.stamina.bounty"),
                I18NContext(
                    "zzzerouid.message.stamina.bounty.current",
                    num=bounty.get("num", 0),
                    total=bounty.get("total", 0),
                ),
            ]
        )

    weekly = data.get("weekly_task")
    if weekly:
        lines.extend(
            [
                "",
                I18NContext("zzzerouid.message.stamina.weekly"),
                I18NContext(
                    "zzzerouid.message.stamina.weekly.current",
                    cur=weekly.get("cur_point", 0),
                    max=weekly.get("max_point", 0),
                ),
            ]
        )

    await msg.finish(lines)


def _format_seconds(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h{minutes}m"
