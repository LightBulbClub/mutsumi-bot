import json
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement

from ..api import zzz_api
from ..utils.fonts import zzz_font_18, zzz_font_20, zzz_font_24, zzz_font_32
from ..utils.hint import error_reply
from ..utils.image import (
    add_footer,
    get_element_img,
    get_general_role_img,
    get_player_card_min,
    get_rarity_img,
    get_skill_dict,
    get_zzz_bg,
)
from ..utils.resource import PLAYER_PATH, TEXTURE2D_PATH
from ..utils.uid import get_uid

TEXT_PATH = TEXTURE2D_PATH / "zzzerouid_char_list"
COLOR_MAP = {
    "S": (255, 188, 0),
    "A": (208, 0, 255),
}
RANK1, RANK2, RANK3, RANK4, RANK5, RANK6 = (
    (189, 33, 33),
    (189, 89, 33),
    (134, 33, 189),
    (33, 69, 189),
    (39, 127, 47),
    (39, 106, 74),
)
shape = Image.open(TEXT_PATH / "shape.png")
banner = Image.open(TEXT_PATH / "banner.png")


async def draw_roster(msg: Bot.MessageSession):
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(I18NContext("zzzerouid.message.bind_uid_hint"))
        return

    path = PLAYER_PATH / str(uid)
    if not path.exists():
        await msg.finish(I18NContext("zzzerouid.message.card.need_refresh", name="any character"))
        return

    char_paths = list(path.rglob("[0-9][0-9][0-9][0-9].json"))
    if not char_paths:
        await msg.finish(I18NContext("zzzerouid.message.card.need_refresh", name="any character"))
        return

    try:
        img = await _draw_char_list_image(msg, uid, char_paths)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw char list image")
        await _fallback_text(msg, uid)


async def _draw_char_list_image(
    msg: Bot.MessageSession,
    uid: str,
    char_paths: List[Path],
) -> Image.Image:
    sender_name = msg.session_info.sender_name
    player_card = await get_player_card_min(uid, sender_name=sender_name)

    char_num = len(char_paths)
    w, h = 1000, 600 + char_num * 92 + 90
    img = get_zzz_bg(w, h, "bg")
    title = Image.open(TEXT_PATH / "title.png")
    title_draw = ImageDraw.Draw(title)
    img.paste(player_card, (25, 70), player_card)
    img.paste(banner, (25, 487), banner)

    srank_weapon = 0
    high_avatar = 0
    high_shadow = 0
    srank_avatar = 0
    frame = Image.open(TEXT_PATH / "frame.png")
    weapon_mask = Image.open(TEXT_PATH / "weapon_mask.png")

    datas: List[Dict] = []
    for i in char_paths:
        with open(i, mode="r", encoding="UTF-8") as f:
            data: Dict = json.load(f)

        base_score = 250 if data["rarity"] == "S" else 50
        score = (data["rank"] + 1) * base_score
        score += data["level"]
        for skill in data.get("skills", []):
            score += skill["level"] * 10

        if data.get("weapon"):
            score += 210 if data["weapon"]["rarity"] == "S" else 60
            score += data["weapon"]["level"]

        data["score"] = score
        datas.append(data)

    datas.sort(key=lambda x: x["score"], reverse=True)

    for index, data in enumerate(datas):
        char_id = data["id"]
        char_img = get_general_role_img(char_id)
        element_icon = get_element_img(data["element_type"], 30, 30)
        level = data["level"]
        level_str = f"Lv{level}"
        level_color = _get_color(
            level,
            {
                60: RANK1,
                50: RANK2,
                40: RANK3,
                30: RANK4,
                20: RANK5,
                10: RANK6,
            },
        )
        rank = data["rank"]
        if rank >= 5:
            high_shadow += 1
        rank_str = f"{rank}影"
        rank_color = _get_color(
            rank,
            {
                6: RANK1,
                5: RANK2,
                4: RANK3,
                3: RANK4,
                2: RANK5,
                1: RANK6,
            },
        )

        rarity = data["rarity"]
        if rarity == "S":
            srank_avatar += 1
        color = COLOR_MAP.get(rarity, (255, 188, 0))

        skill_dict = get_skill_dict(data)
        bar = Image.open(TEXT_PATH / "bar.png")
        bar_draw = ImageDraw.Draw(bar)

        bar.paste(char_img, (103, 14), char_img)

        skill_bar = Image.open(TEXT_PATH / "skill_bar.png")
        skill_draw = ImageDraw.Draw(skill_bar)

        skill_all_level = 0
        for skill_pos_num in skill_dict:
            skill_level, skill_color = skill_dict[skill_pos_num]
            skill_all_level += skill_level
            skill_draw.text(
                (int(32 + skill_pos_num * 50.3), 50),
                f"{skill_level}",
                skill_color,
                zzz_font_18,
                "mm",
            )

        if skill_all_level / 6 >= 8:
            high_avatar += 1

        weapon = data.get("weapon")
        if weapon:
            from ..utils.download import get_weapon

            weapon_img = await get_weapon(weapon["id"])
            weapon_img = weapon_img.resize((133, 133))
            weapon_name = weapon["name"]
            weapon_level = weapon["level"]
            wlevel_str = f"Lv{weapon_level}"
            wlevel_color = _get_color(
                weapon_level,
                {
                    60: RANK1,
                    50: RANK2,
                    40: RANK3,
                    30: RANK4,
                    20: RANK5,
                    10: RANK6,
                },
            )
            weapon_star = weapon["star"]
            star_str = f"{weapon_star}精"
            star_color = _get_color(
                weapon_star,
                {
                    6: RANK1,
                    5: RANK2,
                    4: RANK3,
                    3: RANK4,
                    2: RANK5,
                    1: RANK6,
                },
            )
            weapon_rarity = weapon["rarity"]
            if weapon_rarity == "S":
                srank_weapon += 1
            rarity_icon = get_rarity_img(weapon_rarity, 40, 40)
            bar.paste(weapon_img, (648, -20), weapon_mask)

        bar.paste(element_icon, (287, 16), element_icon)

        color_bar = Image.new("RGBA", bar.size, color)
        bar.paste(color_bar, (0, 0), frame)

        level_tag = _get_shape(level_str, level_color)
        rank_tag = _get_shape(rank_str, rank_color)
        bar.paste(rank_tag, (75, 14), rank_tag)
        bar.paste(level_tag, (220, 47), level_tag)

        if weapon:
            wlevel_tag = _get_shape(wlevel_str, wlevel_color)
            star_tag = _get_shape(star_str, star_color)
            bar.paste(rarity_icon, (780, 10), rarity_icon)
            bar.paste(wlevel_tag, (837, 47), wlevel_tag)
            bar.paste(star_tag, (755, 47), star_tag)
            bar_draw.text(
                (820, 30),
                weapon_name[:5],
                "white",
                zzz_font_20,
                "lm",
            )

        bar.paste(skill_bar, (309, 8), skill_bar)
        img.paste(bar, (0, 600 + index * 92), bar)

    savatar_str = f"{srank_avatar}/{char_num}"
    highshadow_str = f"{high_shadow}/{char_num}"
    highavatar_str = f"{high_avatar}/{char_num}"
    srank_weapon_rate = str(round(srank_weapon / char_num, 2) * 100) + "%"

    for sindex, s in enumerate([savatar_str, highshadow_str, highavatar_str, srank_weapon_rate]):
        title_draw.text(
            (221 + sindex * 177, 166),
            s,
            (24, 24, 24),
            zzz_font_32,
            "mm",
        )

    img.paste(title, (0, 228), title)
    img = add_footer(img)
    return img


def _get_color(value: int, value_ramp: Dict[int, tuple]):
    for i in sorted(value_ramp.keys(), reverse=True):
        if value >= i:
            return Image.new("RGBA", (90, 30), value_ramp[i])
    return Image.new("RGBA", (90, 30), (58, 58, 58))


def _get_shape(value: str, color: Image.Image):
    img = Image.new("RGBA", shape.size)
    img.paste(color, (0, 0), shape)
    img_draw = ImageDraw.Draw(img)
    img_draw.text((45, 15), value, "white", zzz_font_24, "mm")
    return img


async def _fallback_text(msg: Bot.MessageSession, uid: str):
    data = await zzz_api.get_zzz_avatar_basic_info(uid)
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    lines = [I18NContext("zzzerouid.message.roster.title", uid=uid), ""]
    for avatar in data:
        name = avatar.get("name", "Unknown")
        level = avatar.get("level", 0)
        rank = avatar.get("rank", 0)
        rarity = avatar.get("rarity", "?")
        lines.append(f"{rarity} {name} Lv.{level} M{rank}")
    await msg.finish(I18NContext("zzzerouid.message.roster.text", list="\n".join(lines)))
