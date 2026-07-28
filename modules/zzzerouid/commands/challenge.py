from datetime import datetime

from PIL import Image, ImageDraw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement

from ..api import zzz_api
from ..utils.fonts import zzz_font_20, zzz_font_30, zzz_font_32, zzz_font_40, zzz_font_60
from ..utils.hint import error_reply
from ..utils.image import (
    GREY,
    add_footer,
    draw_avatar,
    draw_bangboo,
    get_level_img,
    get_player_card_min,
    get_rank_img,
    get_rank_tier,
    get_zzz_bg,
)
from ..utils.resource import TEXTURE2D_PATH

TEXT_PATH = TEXTURE2D_PATH / "zzzerouid_challenge"
RANK_COLOR = {"B": (39, 193, 255), "A": (206, 34, 247), "S": (255, 135, 0)}


def _format_timestamp(timestamp: int):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%m/%d")


def _format_seconds(seconds: float):
    minute = int(seconds % 3600 // 60)
    second = int(seconds % 60)
    return f"{minute}分钟{second}秒"


def _format_times(e: dict):
    return f"{e.get('day', 0)}天{e.get('hour', 0)}时{e.get('minute', 0)}分{e.get('second', 0)}秒"


async def draw_challenge(msg: Bot.MessageSession, uid: str, schedule_type: int = 1):
    data = await zzz_api.get_zzz_hadal_info(uid, schedule_type)
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    try:
        img = await _draw_challenge_image(msg, uid, data)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw challenge image")
        await _fallback_text(msg, uid, data)


async def _draw_challenge_image(
    msg: Bot.MessageSession,
    uid: str,
    data: dict,
) -> Image.Image:
    hadal = data.get("hadal_info_v2", {})
    brief = hadal.get("brief", {})
    fourth = hadal.get("fourth_layer_detail", {})
    fifth = hadal.get("fitfh_layer_detail", {})

    if not fourth:
        raise ValueError("No challenge record")

    sender_name = msg.session_info.sender_name
    player_card = await get_player_card_min(uid, sender_name=sender_name)

    abyss_data_5 = []
    abyss_data_4 = []

    if fifth and "layer_challenge_info_list" in fifth and fifth["layer_challenge_info_list"]:
        abyss_data_5 = fifth["layer_challenge_info_list"]

    if fourth and "layer_challenge_info_list" in fourth and fourth["layer_challenge_info_list"]:
        abyss_data_4 = [fourth]

    w, h = 950, 710 + 100
    if abyss_data_4:
        h += 700
    if abyss_data_5:
        h += 1000

    img = get_zzz_bg(w, h, "bg2")
    title = Image.open(TEXT_PATH / "title.png")
    banner = Image.open(TEXT_PATH / "banner.png")
    title_draw = ImageDraw.Draw(title)

    if "battle_time" in brief:
        fast_layer_time = brief["battle_time"]
        layer_time = _format_seconds(fast_layer_time)
        title_draw.text((302, 367), layer_time, "white", zzz_font_32, "lm")

    max_layer = brief["cur_period_zone_layer_count"]
    layer_name = f"第{max_layer}防线"
    begin = _format_timestamp(int(hadal["begin_time"]))
    end = _format_timestamp(int(hadal["end_time"]))

    s_num, a_num, b_num = 0, 0, 0
    for i in abyss_data_5 + abyss_data_4:
        rating = i.get("rating", "S")
        if rating == "B":
            b_num += 1
        elif rating == "A":
            a_num += 1
        else:
            s_num += 1

    for index, num in enumerate([s_num, a_num, b_num]):
        title_draw.text(
            (402 + 109 * index, 285),
            f"{num}",
            "white",
            zzz_font_30,
            "mm",
        )

    title_draw.text((723, 367), layer_name, "white", zzz_font_32, "lm")
    title_draw.text((224, 256), begin, (81, 81, 81), zzz_font_60, "mm")
    title_draw.text((733, 256), end, (81, 81, 81), zzz_font_60, "mm")

    img.paste(player_card, (0, 70), player_card)
    img.paste(title, (0, 190), title)
    img.paste(banner, (0, 610), banner)

    y = 720

    for floor_num, floor_data in enumerate(abyss_data_4):
        floor_img = Image.open(TEXT_PATH / "floor.png")
        floor_draw = ImageDraw.Draw(floor_img)
        rating = floor_data["rating"]
        zone_name = "第四节点"
        color = RANK_COLOR.get(rating, "white")

        rank_img = get_rank_img(rating, 51, 51)
        floor_img.paste(rank_img, (76, 57), rank_img)
        floor_draw.text(
            (138, 83),
            zone_name,
            "black",
            zzz_font_40,
            "lm",
            stroke_width=5,
            stroke_fill="black",
        )
        floor_draw.text((138, 83), zone_name, color, zzz_font_40, "lm")

        await _draw_team(
            floor_data["layer_challenge_info_list"][0],
            floor_img,
            0,
            115,
        )
        await _draw_team(
            floor_data["layer_challenge_info_list"][1],
            floor_img,
            1,
            385,
        )
        img.paste(floor_img, (0, 720 + floor_num * 700), floor_img)
        y += 700

    if abyss_data_5:
        floor_img = Image.open(TEXT_PATH / "floor5.png")
        floor_draw = ImageDraw.Draw(floor_img)
        rating = brief["rating"]
        score = brief["score"]
        zone_name = f"{layer_name}"
        color = RANK_COLOR.get(rating, "white")

        rank_percent = brief["rank_percent"] / 100
        rank_tier = get_rank_tier(rank_percent)
        rank_img = get_rank_img(rating, 64, 64)
        floor_img.paste(rank_img, (70, 50), rank_img)
        floor_img.paste(rank_tier, (618, 33), rank_tier)

        floor_draw.text((645, 84), f"{score}分", "white", zzz_font_40, "rm")
        floor_draw.text(
            (138, 83),
            zone_name,
            "black",
            zzz_font_40,
            "lm",
            stroke_width=5,
            stroke_fill="black",
        )
        floor_draw.text((138, 83), zone_name, color, zzz_font_40, "lm")

        for idx, offset in enumerate([138, 408, 678]):
            if len(abyss_data_5) > idx:
                await _draw_team(abyss_data_5[idx], floor_img, idx, offset)
        img.paste(floor_img, (0, y), floor_img)

    img = add_footer(img)
    return img


async def _draw_team(node: dict, floor_img: Image.Image, team_index: int, pos_y: int):
    if "score" in node:
        rating = node["rating"]
        _p = TEXT_PATH / f"team_bar_{rating.lower()}.png"
        if _p.exists():
            team_bar = Image.open(_p)
        else:
            team_bar = Image.open(TEXT_PATH / "team_bar.png")
    else:
        team_bar = Image.open(TEXT_PATH / "team_bar.png")

    team_draw = ImageDraw.Draw(team_bar)
    battle_time = node["challenge_time"]
    battle_time_str = _format_times(battle_time)

    team_draw.text((818, 42), battle_time_str, GREY, zzz_font_20, "rm")
    if "score" in node:
        score = node["score"]
        team_draw.text((184, 38), f"{score}分", "white", zzz_font_30, "lm")
        level = get_level_img(node["rating"], 51, 51)
        team_bar.paste(level, (121, 12), level)
    else:
        team_draw.text((135, 38), f"队伍{team_index + 1}", "white", zzz_font_30, "lm")

    floor_img.paste(team_bar, (0, pos_y), team_bar)

    for aindex, agent in enumerate(node["avatar_list"]):
        avatar_img = await draw_avatar(agent)
        floor_img.paste(
            avatar_img,
            (105 + aindex * 190, pos_y + 55),
            avatar_img,
        )

    if "buddy" in node and node["buddy"]:
        bangboo_img = await draw_bangboo(node["buddy"])
        bangboo_img = bangboo_img.resize((152, 176))
        floor_img.paste(bangboo_img, (685, pos_y + 91), bangboo_img)


async def _fallback_text(msg: Bot.MessageSession, uid: str, data: dict):
    hadal = data.get("hadal_info_v2", {})
    brief = hadal.get("brief", {})
    fourth = hadal.get("fourth_layer_detail", {})
    fifth = hadal.get("fitfh_layer_detail", {})

    if not fourth:
        await msg.finish(I18NContext("zzzerouid.message.challenge.no_record"))
        return

    lines = [
        I18NContext("zzzerouid.message.challenge.title", uid=uid),
        "",
        I18NContext(
            "zzzerouid.message.challenge.period",
            begin=_format_timestamp(int(hadal.get("begin_time", 0))),
            end=_format_timestamp(int(hadal.get("end_time", 0))),
        ),
        I18NContext(
            "zzzerouid.message.challenge.layer",
            layer=brief.get("cur_period_zone_layer_count", 0),
        ),
        I18NContext(
            "zzzerouid.message.challenge.rating",
            rating=brief.get("rating", "Unknown"),
        ),
        I18NContext("zzzerouid.message.challenge.score", score=brief.get("score", 0)),
    ]

    if "battle_time" in brief:
        lines.append(
            I18NContext(
                "zzzerouid.message.challenge.fastest",
                time=_format_seconds(brief["battle_time"]),
            )
        )

    if fourth and "layer_challenge_info_list" in fourth:
        lines.extend(["", I18NContext("zzzerouid.message.challenge.fourth_layer")])
        for idx, node in enumerate(fourth["layer_challenge_info_list"], 1):
            lines.append(
                I18NContext(
                    "zzzerouid.message.challenge.team",
                    index=idx,
                    rating=node.get("rating", "-"),
                    time=_format_times(node.get("challenge_time", {})),
                )
            )

    if fifth and "layer_challenge_info_list" in fifth:
        lines.extend(["", I18NContext("zzzerouid.message.challenge.fifth_layer")])
        for idx, node in enumerate(fifth["layer_challenge_info_list"], 1):
            lines.append(
                I18NContext(
                    "zzzerouid.message.challenge.node",
                    index=idx,
                    rating=node.get("rating", "-"),
                    score=node.get("score", 0),
                    time=_format_times(node.get("challenge_time", {})),
                )
            )

    await msg.finish(lines)
