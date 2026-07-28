from PIL import Image, ImageDraw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement

from ..api import zzz_api
from ..utils.fonts import zzz_font_44
from ..utils.hint import error_reply
from ..utils.image import (
    add_footer,
    draw_avatar,
    draw_bangboo,
    get_player_card_min,
    get_zzz_bg,
)
from ..utils.resource import TEXTURE2D_PATH

TEXT_PATH = TEXTURE2D_PATH / "zzzerouid_roleinfo"


async def draw_role_info(msg: Bot.MessageSession, uid: str):
    data = await zzz_api.get_zzz_index_info(uid)
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    avatar_data = await zzz_api.get_zzz_avatar_basic_info(uid)
    if isinstance(avatar_data, int):
        await msg.finish(error_reply(avatar_data))
        return

    bangboo_data = await zzz_api.get_zzz_bangboo_info(uid)
    if isinstance(bangboo_data, int):
        await msg.finish(error_reply(bangboo_data))
        return

    try:
        img = await _draw_role_image(msg, uid, data, avatar_data, bangboo_data)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw role info image")
        await _fallback_text(msg, uid, data)


async def _draw_role_image(
    msg: Bot.MessageSession,
    uid: str,
    data: dict,
    avatar_data: list,
    bangboo_data: list,
) -> Image.Image:
    stats = data["stats"]
    sender_name = msg.session_info.sender_name
    player_card = await get_player_card_min(
        uid,
        sender_name=sender_name,
        world=stats.get("world_level_name", ""),
    )

    base_info = Image.open(TEXT_PATH / "base_info.png")
    agent_banner = Image.open(TEXT_PATH / "agent_banner.png")
    bangboo_banner = Image.open(TEXT_PATH / "bangboo_banner.png")
    base_draw = ImageDraw.Draw(base_info)

    base_draw.text((202, 239), f"{stats.get('active_days', 0)}", "white", zzz_font_44, "mm")
    base_draw.text((378, 239), f"{stats.get('avatar_num', 0)}", "white", zzz_font_44, "mm")
    base_draw.text((556, 239), f"{stats.get('buddy_num', 0)}", "white", zzz_font_44, "mm")
    base_draw.text(
        (734, 239),
        f"{stats.get('cur_period_zone_layer_count', 0)}",
        "white",
        zzz_font_44,
        "mm",
    )

    agent_num = len(avatar_data)
    bangboo_num = len(bangboo_data)
    agent_h = ((agent_num - 1) // 4 + 1) * 220
    w, h = (
        950,
        660 + agent_h + ((bangboo_num - 1) // 4 + 1) * 220 + 100 + 80,
    )
    img = get_zzz_bg(w, h)

    img.paste(player_card, (0, 37), player_card)
    img.paste(base_info, (0, 137), base_info)
    img.paste(agent_banner, (0, 551), agent_banner)
    img.paste(bangboo_banner, (0, 651 + agent_h), bangboo_banner)

    for aindex, agent in enumerate(avatar_data):
        rank_bg = await draw_avatar(agent, TEXT_PATH)
        img.paste(
            rank_bg,
            (94 + aindex % 4 * 190, 659 + aindex // 4 * 220),
            rank_bg,
        )

    for bindex, bangboo in enumerate(bangboo_data):
        if bangboo:
            rank_bg = await draw_bangboo(bangboo, TEXT_PATH)
            img.paste(
                rank_bg,
                (94 + bindex % 4 * 190, 659 + bindex // 4 * 220 + agent_h + 100),
                rank_bg,
            )

    img = add_footer(img)
    return img


async def _fallback_text(msg: Bot.MessageSession, uid: str, data: dict):
    stats = data.get("stats", {})
    avatar_list = data.get("avatar_list", [])
    nick = data.get("nickname", "Unknown")
    await msg.finish(
        I18NContext(
            "zzzerouid.message.info.text",
            uid=uid,
            nick=nick,
            active_days=stats.get("active_days", 0),
            avatar_count=stats.get("avatar_count", len(avatar_list)),
            achievement_count=stats.get("achievement_count", 0),
        )
    )
