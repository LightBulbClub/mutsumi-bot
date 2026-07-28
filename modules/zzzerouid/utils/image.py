from typing import Any, Union
from pathlib import Path

from PIL import Image, ImageDraw

from ..api import zzz_api
from .download import get_square_avatar, get_square_bangboo
from .fonts import zzz_font_28, zzz_font_30, zzz_font_38
from .resource import CAMP_PATH, MIND_PATH, ROLECIRCLE_PATH, ROLEGENERAL_PATH, SUIT_PATH, TEXTURE2D_PATH

GREY = (216, 216, 216)
BLACK_G = (40, 40, 40)
YELLOW = (255, 200, 1)
BLUE = (1, 183, 255)

YES = Image.open(TEXTURE2D_PATH / "zzzerouid_stamina" / "yes.png")
NO = Image.open(TEXTURE2D_PATH / "zzzerouid_stamina" / "no.png")

ELEMENT_TYPE = {
    203: "电属性",
    205: "以太属性",
    202: "冰属性",
    200: "物理属性",
    201: "火属性",
}

prop_id = {
    "111": "IconHpMax",
    "121": "IconAttack",
    "131": "IconDef",
    "122": "IconBreakStun",
    "201": "IconCrit",
    "211": "IconCritDam",
    "314": "IconElementAbnormalPower",
    "312": "IconElementMystery",
    "231": "IconPenRatio",
    "232": "IconPenValue",
    "305": "IconSpRecover",
    "310": "IconSpGetRatio",
    "115": "IconSpMax",
    "315": "IconPhysDmg",
    "316": "IconFire",
    "317": "IconIce",
    "318": "IconThunder",
    "319": "IconDungeonBuffEther",
}

pro_id = {
    "1": "IconAttack",
    "2": "IconStun",
    "3": "IconAnomaly",
    "4": "IconSupport",
    "5": "IconDefense",
    "6": "IconRupture",
}


def crop_center_img(img: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = img.size
    left = (iw - w) // 2
    top = (ih - h) // 2
    right = left + w
    bottom = top + h
    return img.crop((left, top, right, bottom)).resize((w, h))


def get_camp_img(camp_name: str):
    camp_map = {
        "白祇重工": "BelobogIndustries",
        "奥波勒斯小队": "Obols",
        "狡兔屋": "GentleHouse",
        "对空洞特别行动部第六课": "H.S.O-S6",
        "卡吕冬之子": "SonsOfCalydon",
        "维多利亚家政": "VictoriaHousekeepingCo.",
        "新艾利都治安局": "N.E.P.S.",
        "刑侦特勤组": "JaneBadge",
        "天琴座": "StarsOfLyra",
        "防卫军·白银小队": "Silvers",
        "防卫军·奥波勒斯小队": "Obols",
        "反舌鸟": "MockingBird",
        "云岿山": "Suibian",
        "怪啖屋": "SpookShack",
        "坎卜斯黑枝": "BlackRoot",
        "妄想天使": "A.O.D",
        "罗斯凯利法·外务筹策局": "E.S.D.",
    }
    name = camp_map.get(camp_name, "BelobogIndustries")
    return Image.open(CAMP_PATH / f"IconCamp{name}.png")


def get_mind_role_img(_id: Union[str, int], _type: str = "3"):
    path = MIND_PATH / f"Mindscape_{_id}_{_type}.png"
    if not path.exists():
        path = MIND_PATH / "Mindscape_1291_1.png"
    return Image.open(path)


def get_general_role_img(_id: Union[str, int], w: int = 180, h: int = 64):
    from .name_convert import char_id_to_sprite

    char_id = str(_id)
    sprite_id = char_id_to_sprite(char_id)
    path = ROLEGENERAL_PATH / f"IconRoleGeneral{sprite_id}.png"
    if not path.exists():
        path = ROLEGENERAL_PATH / "IconRoleGeneral03.png"
    return Image.open(path).resize((w, h)).convert("RGBA")


def get_circle_role_img(_id: Union[str, int], w: int = 142, h: int = 142):
    from .name_convert import char_id_to_sprite

    char_id = str(_id)
    sprite_id = char_id_to_sprite(char_id)
    path = ROLECIRCLE_PATH / f"IconRoleCircle{sprite_id}.png"
    if not path.exists():
        path = ROLECIRCLE_PATH / "IconRoleCircle03.png"
    return Image.open(path).resize((w, h)).convert("RGBA")


def get_pro_img(_id: Union[str, int], w: int = 50, h: int = 50):
    img = Image.new("RGBA", (100, 100))
    propid = str(_id)
    prop_icon = pro_id.get(propid)
    if not prop_icon:
        return img.resize((w, h))

    icon = Image.open(TEXTURE2D_PATH / "pro" / f"{prop_icon}.png")
    return icon.resize((w, h)).convert("RGBA")


def get_prop_img(_id: Union[str, int], w: int = 40, h: int = 40):
    img = Image.new("RGBA", (70, 70))
    propid = str(_id)
    if propid.isdigit():
        propid = propid[:3]
        prop_icon = prop_id.get(propid)
    else:
        prop_icon = propid

    if not prop_icon:
        return img.resize((w, h))

    icon = Image.open(TEXTURE2D_PATH / "prop" / f"{prop_icon}.png")
    x, y = icon.size
    img.paste(icon, (35 - x // 2, 35 - y // 2), icon)
    return img.resize((w, h))


def get_element_img(elemet_id: Union[int, str], w: int = 40, h: int = 40):
    elemet_id = int(elemet_id)
    if elemet_id not in ELEMENT_TYPE:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img = Image.open(TEXTURE2D_PATH / f"{ELEMENT_TYPE[elemet_id]}.png")
    return img.resize((w, h)).convert("RGBA")


def get_equip_img(equip_id: str, w: int = 90, h: int = 90):
    from .name_convert import equip_id_to_sprite

    sprite_id = equip_id_to_sprite(equip_id)
    if sprite_id:
        sprite_id = sprite_id[2:]
        img = Image.open(SUIT_PATH / f"{sprite_id}.png")
        return img.resize((w, h)).convert("RGBA")
    else:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def get_rarity_img(rank: str, w: int = 80, h: int = 80):
    rank = rank.upper()
    if rank in ["S", "A", "B", "C"]:
        img = Image.open(TEXTURE2D_PATH / f"Rarity_{rank}.png")
        return img.resize((w, h)).convert("RGBA")
    else:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def get_level_img(level: str, w: int = 40, h: int = 40):
    if level in ["S", "A", "B", "S+"]:
        img = Image.open(TEXTURE2D_PATH / f"level_{level.lower()}.png")
        return img.resize((w, h)).convert("RGBA")
    else:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def get_rank_img(rank: str, w: int = 40, h: int = 40):
    rank = rank.upper()
    if rank in ["S", "A", "B", "S+"]:
        img = Image.open(TEXTURE2D_PATH / f"{rank}RANK.png")
        return img.resize((w, h)).convert("RGBA")
    else:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def get_zzz_bg(w: int, h: int, bg: Union[str, Path] = "bg") -> Image.Image:
    if isinstance(bg, Path):
        img = Image.open(bg).convert("RGBA")
    else:
        img = Image.open(TEXTURE2D_PATH / f"{bg}.jpg").convert("RGBA")
    return crop_center_img(img, w, h)


def get_footer():
    return Image.open(TEXTURE2D_PATH / "footer.png")


def add_footer(img: Image.Image, w: int = 0) -> Image.Image:
    footer = get_footer()
    w = img.size[0] if not w else w
    if w != footer.size[0]:
        footer = footer.resize(
            (w, int(footer.size[1] * w / footer.size[0])),
        )
    x, y = (
        int((img.size[0] - footer.size[0]) / 2),
        img.size[1] - footer.size[1] - 10,
    )
    img.paste(footer, (x, y), footer)
    return img


def draw_bar(
    title: str,
    cur_value: Any,
    max_value: Any,
    max_yes: bool = True,
    bar_path: Path = TEXTURE2D_PATH / "bar.png",
):
    from .fonts import zzz_font_40, zzz_font_50

    bar = Image.open(bar_path)
    bar_draw = ImageDraw.Draw(bar)

    if max_yes:
        icon = YES if cur_value >= max_value else NO
    else:
        icon = YES if cur_value <= max_value else NO

    bar.paste(icon, (93, 10), icon)
    bar_draw.text((188, 51), f"{title}", GREY, zzz_font_40, "lm")
    bar_draw.text((716, 56), f"/{max_value}", GREY, zzz_font_40, "lm")
    bar_draw.text((708, 54), f"{cur_value}", YELLOW, zzz_font_50, "rm")
    return bar


async def get_player_card_min(
    uid: str,
    sender_name: str | None = None,
    world: str = "",
):
    data = await zzz_api.get_zzz_user_info_g(uid)
    if isinstance(data, int):
        nickname = sender_name or "Unknown"
    else:
        nickname = data.get("nickname", sender_name or "Unknown")
        world = world or data.get("region_name", "Unknown")

    player_card = Image.open(TEXTURE2D_PATH / "player_card_min.png")
    card_draw = ImageDraw.Draw(player_card)

    card_draw.text((290, 120), f"UID {uid}", GREY, zzz_font_30, "lm")
    card_draw.text((290, 64), nickname, "white", zzz_font_38, "lm")

    text_lenth = card_draw.textlength(nickname, zzz_font_38)

    xs, ys = 290 + text_lenth + 20, 45
    xt, yt = xs + 90 + 12, 45
    card_draw.rounded_rectangle((xs, ys, xs + 90, ys + 35), 10, YELLOW)
    card_draw.rounded_rectangle((xt, yt, xt + 144, yt + 35), 10, BLUE)

    card_draw.text(
        (xs + 45, ys + 17),
        "Lv.?",
        BLACK_G,
        zzz_font_28,
        "mm",
    )
    card_draw.text(
        (xt + 72, yt + 17),
        world,
        BLACK_G,
        zzz_font_28,
        "mm",
    )
    return player_card


def get_skill_dict(data: dict) -> dict:
    skills = data.get("skills", [])
    result = {}
    skill_map = {0: 0, 2: 1, 6: 2, 1: 3, 3: 4, 5: 5}
    for skill in skills:
        skill_type = skill["skill_type"]
        skill_pos_num = skill_map.get(skill_type, 0)
        skill_level = skill["level"]
        if skill_level >= 11:
            skill_color = YELLOW
        elif skill_level >= 6:
            skill_color = BLUE
        elif skill_level >= 3:
            skill_color = (255, 255, 255)
        else:
            skill_color = GREY
        result[skill_pos_num] = skill_level, skill_color
    return result


async def draw_avatar(agent: dict, text_path: Path | None = None) -> Image.Image:
    from .fonts import zzz_font_24

    if text_path is None:
        text_path = TEXTURE2D_PATH / "zzzerouid_roleinfo"
    char_fg = Image.open(text_path / "char_fg.png")

    rarity = agent["rarity"]
    rank_icon = get_rank_img(rarity)
    element_icon = get_element_img(agent["element_type"])
    rank_bg = Image.open(text_path / f"{rarity}RANK_BG.png")
    rank_draw = ImageDraw.Draw(rank_bg)
    agent_icon = await get_square_avatar(agent["id"])
    rank_bg.paste(agent_icon, (19, 17), agent_icon)
    rank_bg.paste(char_fg, (0, 0), char_fg)
    rank_bg.paste(rank_icon, (20, 20), rank_icon)
    rank_bg.paste(element_icon, (130, 21), element_icon)

    RANK_COLOR_MAP = {
        0: (131, 132, 131),
        1: (26, 122, 26),
        2: (1, 139, 222),
        3: (231, 14, 192),
        4: (255, 141, 0),
        5: (249, 81, 0),
        6: (249, 0, 0),
    }

    if "rank" in agent:
        rank = agent["rank"]
        rank_color = RANK_COLOR_MAP.get(rank, (131, 132, 131))
        rank_draw.rectangle((19, 165, 76, 202), rank_color)
        rank_draw.text(
            (48, 184),
            f"{rank}命",
            "white",
            zzz_font_24,
            "mm",
        )
        lx = 123
    else:
        lx = 94
    rank_draw.text(
        (lx, 184),
        f"等级{agent['level']}",
        GREY,
        zzz_font_24,
        "mm",
    )
    return rank_bg


async def draw_bangboo(bangboo: dict, text_path: Path | None = None) -> Image.Image:
    from .fonts import zzz_font_24

    if text_path is None:
        text_path = TEXTURE2D_PATH / "zzzerouid_roleinfo"
    bangboo_fg = Image.open(text_path / "bangboo_fg.png")

    rarity = bangboo["rarity"]
    rank_icon = get_rank_img(rarity)
    rank_bg = Image.open(text_path / f"{rarity}RANK_BG.png")
    rank_draw = ImageDraw.Draw(rank_bg)
    bangboo_icon = await get_square_bangboo(bangboo["id"])
    rank_bg.paste(bangboo_icon, (19, 17), bangboo_icon)
    rank_bg.paste(bangboo_fg, (0, 0), bangboo_fg)
    rank_bg.paste(rank_icon, (20, 20), rank_icon)
    rank_draw.text(
        (94, 184),
        f"等级{bangboo['level']}",
        GREY,
        zzz_font_24,
        "mm",
    )
    return rank_bg


def get_rank_tier(percent: Union[int, float], text_path: Path | None = None):
    from .fonts import zzz_font_38

    if text_path is None:
        text_path = TEXTURE2D_PATH / "zzzerouid_mem"
    rank_percent = percent
    color = BLACK_G
    if rank_percent <= 1:
        rank_tag = "tier_5"
    elif rank_percent <= 10:
        rank_tag = "tier_4"
    elif rank_percent <= 25:
        rank_tag = "tier_3"
    elif rank_percent <= 50:
        rank_tag = "tier_2"
    else:
        color = "white"
        rank_tag = "tier_1"

    rank_img = Image.open(text_path / f"{rank_tag}.png").convert("RGBA")
    rank_draw = ImageDraw.Draw(rank_img)
    rank_draw.text(
        (140, 49),
        f"{rank_percent:.2f}%",
        font=zzz_font_38,
        fill=color,
        anchor="mm",
    )
    return rank_img


def pil_image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    from io import BytesIO

    bio = BytesIO()
    img.save(bio, format=fmt)
    return bio.getvalue()
