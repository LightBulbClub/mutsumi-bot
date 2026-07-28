from PIL import Image, ImageDraw

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement

from ..api import zzz_api
from ..utils.download import draw_boss, download_image
from ..utils.fonts import zzz_font_38, zzz_font_50, zzz_font_54, zzz_font_thin
from ..utils.hint import error_reply
from ..utils.image import (
    GREY,
    YELLOW,
    add_footer,
    draw_avatar,
    draw_bangboo,
    get_player_card_min,
    get_rank_tier,
    get_zzz_bg,
)
from ..utils.resource import TEMP_PATH, TEXTURE2D_PATH

TEXT_PATH = TEXTURE2D_PATH / "zzzerouid_mem"


async def draw_mem(msg: Bot.MessageSession, uid: str, schedule_type: int = 1):
    data = await zzz_api.get_zzz_mem_info(uid, schedule_type)
    if isinstance(data, int):
        await msg.finish(error_reply(data))
        return

    if not data.get("list"):
        await msg.finish(I18NContext("zzzerouid.message.mem.no_record"))
        return

    try:
        img = await _draw_mem_image(msg, uid, data)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw mem image")
        await _fallback_text(msg, uid, data)


async def _draw_mem_image(
    msg: Bot.MessageSession,
    uid: str,
    data: dict,
) -> Image.Image:
    sender_name = msg.session_info.sender_name
    player_card = await get_player_card_min(uid, sender_name=sender_name)

    w, h = 950, 730 + 420 * len(data["list"])

    rank_percent = data["rank_percent"] / 100
    rank_img = get_rank_tier(rank_percent, TEXT_PATH)

    all_score = sum(i["score"] for i in data["list"])
    all_star = sum(i["star"] for i in data["list"])

    img = get_zzz_bg(w, h, "bg4")
    title = Image.open(TEXT_PATH / "title.png")
    title_draw = ImageDraw.Draw(title)
    title_draw.text(
        (368, 94),
        f"{all_score}",
        font=zzz_font_50,
        fill="white",
        anchor="mm",
        stroke_width=2,
        stroke_fill="black",
    )
    title.paste(rank_img, (424, 45), rank_img)
    img.paste(title, (0, -11), title)

    banner = Image.open(TEXT_PATH / "banner.png")
    bar = Image.open(TEXT_PATH / "bar.png")
    bar_draw = ImageDraw.Draw(bar)
    bar_draw.text(
        (807, 217),
        f"x{all_star}",
        font=zzz_font_38,
        fill="white",
        anchor="lm",
    )
    img.paste(bar, (0, 264), bar)
    img.paste(player_card, (0, 330), player_card)
    img.paste(banner, (0, 552), banner)

    star_full = Image.open(TEXT_PATH / "star_full.png")
    star_empty = Image.open(TEXT_PATH / "star_empty.png")

    for i, mem in enumerate(data["list"]):
        card = Image.open(TEXT_PATH / "card_bg.png")
        card_draw = ImageDraw.Draw(card)

        _time = mem["challenge_time"]
        time_str1 = f"{_time['year']}.{_time['month']}.{_time['day']}"
        time_str2 = f"{_time['hour']}:{_time['minute']}:{_time['second']}"
        time_str = f"通关时刻 {time_str1} {time_str2}"

        boss_img = await draw_boss(mem["boss"][0], TEXT_PATH)
        card.paste(boss_img, (62, 51), boss_img)

        card_draw.text(
            (333, 91),
            mem["boss"][0]["name"],
            font=zzz_font_54,
            fill=YELLOW,
            anchor="lm",
        )
        card_draw.text(
            (333, 155),
            f"{mem['score']}",
            font=zzz_font_50,
            fill="white",
            anchor="lm",
        )
        card_draw.text(
            (333, 202),
            time_str,
            font=zzz_font_thin(20),
            fill=GREY,
            anchor="lm",
        )

        mem_star = mem["star"]
        for j in range(3):
            if j < mem_star:
                card.paste(star_full, (515 + j * 30, 133), star_full)
            else:
                card.paste(star_empty, (515 + j * 30, 133), star_empty)

        buff = mem["buffer"][0]
        buff_icon = buff["icon"]
        buff_name = buff_icon.split("/")[-1]
        buff_path = TEMP_PATH / buff_name
        if not buff_path.exists():
            await download_image(buff_icon, TEMP_PATH, buff_name)
        if buff_path.exists():
            buff_img = Image.open(buff_path).resize((78, 78))
            card.paste(buff_img, (851, 13), buff_img)

        for aindex, agent in enumerate(mem["avatar_list"]):
            avatar_img = await draw_avatar(agent)
            avatar_img = avatar_img.resize((152, 176))
            card.paste(
                avatar_img,
                (320 + aindex * 146, 221),
                avatar_img,
            )

        if "buddy" in mem and mem["buddy"]:
            bangboo_img = await draw_bangboo(mem["buddy"])
            bangboo_img = bangboo_img.resize((123, 143))
            card.paste(bangboo_img, (770, 251), bangboo_img)

        img.paste(card, (0, 660 + i * 420), card)

    img = add_footer(img)
    return img


async def _fallback_text(msg: Bot.MessageSession, uid: str, data: dict):
    rank_percent = data.get("rank_percent", 0) / 100
    total_score = sum(item.get("score", 0) for item in data["list"])
    total_star = sum(item.get("star", 0) for item in data["list"])

    lines = [
        I18NContext("zzzerouid.message.mem.title", uid=uid),
        "",
        I18NContext("zzzerouid.message.mem.rank", rank=f"{rank_percent:.2f}%"),
        I18NContext("zzzerouid.message.mem.total_score", score=total_score),
        I18NContext("zzzerouid.message.mem.total_star", star=total_star),
        "",
    ]

    for idx, item in enumerate(data["list"], 1):
        boss = item.get("boss", [{}])[0]
        time = item.get("challenge_time", {})
        lines.append(
            I18NContext(
                "zzzerouid.message.mem.boss",
                index=idx,
                name=boss.get("name", "Unknown"),
                score=item.get("score", 0),
                star=item.get("star", 0),
                year=time.get("year", 0),
                month=time.get("month", 0),
                day=time.get("day", 0),
                hour=time.get("hour", 0),
                minute=time.get("minute", 0),
                second=time.get("second", 0),
            )
        )

    await msg.finish(lines)
