import asyncio
import json
from datetime import datetime
from typing import Dict

from core.builtins.bot import Bot
from core.builtins.message.elements import I18NContextElement
from core.builtins.message.internal import I18NContext, Image as ImageElement, Plain
from PIL import Image, ImageDraw

from ..api import zzz_api
from ..api.sign_request import SignMysApi
from ..utils.download import get_square_avatar, get_square_bangboo, get_weapon
from ..utils.fonts import zzz_font_18, zzz_font_20, zzz_font_32
from ..utils.hint import error_reply
from ..utils.image import add_footer, get_player_card_min, get_rank_img, get_zzz_bg
from ..utils.resource import PLAYER_PATH
from ..utils.uid import get_uid

sign_api = SignMysApi()

GACHA_TYPE_META = {
    "音擎频段": ["3001"],
    "独家频段": ["2001"],
    "常驻频段": ["1001"],
    "邦布频段": ["5001"],
}


async def refresh_gacha(msg: Bot.MessageSession):
    uid = await _get_uid(msg)
    if not uid:
        return

    result = await _save_gachalogs(uid, is_force=True)
    if isinstance(result, int):
        await msg.finish(error_reply(result))
        return
    await msg.finish(result)


async def draw_gacha(msg: Bot.MessageSession):
    uid = await _get_uid(msg)
    if not uid:
        return

    path = PLAYER_PATH / str(uid) / "gacha_logs.json"
    if not path.exists():
        await msg.finish(I18NContext("zzzerouid.message.gacha.empty"))
        return

    with open(path, "r", encoding="UTF-8") as f:
        data = json.load(f)

    try:
        img = await _draw_gacha_image(uid, data)
        await msg.finish(ImageElement.assign(img))
    except Exception:
        from ..utils.logger import logger

        logger.exception("Failed to draw gacha image")
        await _fallback_text(msg, uid, data)


async def _save_gachalogs(uid: str, is_force: bool = False) -> I18NContextElement | int:
    path = PLAYER_PATH / str(uid)
    path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H-%M-%S")

    gachalogs_path = path / "gacha_logs.json"
    if gachalogs_path.exists():
        with open(gachalogs_path, "r", encoding="UTF-8") as f:
            gacha_log = json.load(f)
        gachalogs_history = gacha_log.get("data", {})
    else:
        gachalogs_history = {}

    raw_data = await _get_new_gachalog(uid, gachalogs_history, is_force)
    if isinstance(raw_data, int):
        return raw_data

    result = {
        "uid": uid,
        "data_time": current_time,
        "normal_gacha_num": len(raw_data.get("常驻频段", [])),
        "char_gacha_num": len(raw_data.get("独家频段", [])),
        "weapon_gacha_num": len(raw_data.get("音擎频段", [])),
        "bangboo_gacha_num": len(raw_data.get("邦布频段", [])),
        "data": raw_data,
    }

    for i in raw_data:
        if len(raw_data[i]) > 1:
            raw_data[i].sort(key=lambda x: -int(x["id"]))

    with open(gachalogs_path, "w", encoding="UTF-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    total_add = (
        result["normal_gacha_num"]
        + result["char_gacha_num"]
        + result["weapon_gacha_num"]
        + result["bangboo_gacha_num"]
        - sum(len(gachalogs_history.get(k, [])) for k in GACHA_TYPE_META)
    )

    if total_add <= 0:
        return I18NContext("zzzerouid.message.gacha.no_new_data", uid=uid)
    return I18NContext(
        "zzzerouid.message.gacha.refreshed",
        uid=uid,
        total=total_add,
        normal=result["normal_gacha_num"],
        char=result["char_gacha_num"],
        weapon=result["weapon_gacha_num"],
        bangboo=result["bangboo_gacha_num"],
    )


async def _get_new_gachalog(uid: str, full_data: Dict, is_force: bool):
    temp = []
    server_id = zzz_api._get_region(uid)

    authkey_rawdata = await sign_api.get_authkey_by_cookie(uid, "nap_cn", server_id)
    if isinstance(authkey_rawdata, int):
        return authkey_rawdata
    authkey = authkey_rawdata.get("authkey")
    if not authkey:
        return -51

    for gacha_name in GACHA_TYPE_META:
        for gacha_type in GACHA_TYPE_META[gacha_name]:
            end_id = "0"
            for page in range(1, 999):
                data = await zzz_api.get_zzz_gacha_log_by_authkey(
                    uid,
                    authkey,
                    gacha_type,
                    gacha_type[0],
                    page,
                    end_id,
                )
                await asyncio.sleep(0.5)
                if isinstance(data, int):
                    return data
                items = data.get("list", [])
                if not items:
                    break
                end_id = items[-1]["id"]

                if gacha_name not in full_data:
                    full_data[gacha_name] = []

                if items[-1] in full_data[gacha_name] and not is_force:
                    for item in items:
                        if item not in full_data[gacha_name]:
                            temp.append(item)
                    full_data[gacha_name][0:0] = temp
                    temp = []
                    break

                if len(full_data[gacha_name]) >= 1:
                    full_id = full_data[gacha_name][0]["id"]
                    if int(items[0]["id"]) <= int(full_id):
                        full_data[gacha_name][0:0] = items
                    else:
                        full_data[gacha_name].extend(items)
                else:
                    full_data[gacha_name][0:0] = items
                await asyncio.sleep(0.3)
    return full_data


async def _get_uid(msg: Bot.MessageSession) -> str | None:
    uid = await get_uid(msg)
    if not uid:
        await msg.finish(I18NContext("zzzerouid.message.bind_uid_hint"))
        return None
    return uid


async def _draw_gacha_image(uid: str, raw_data: dict) -> Image.Image:
    gachalogs = raw_data.get("data", {})
    player_card = await get_player_card_min(uid, sender_name=None)

    total_data = {}
    for gacha_name in gachalogs:
        total_data[gacha_name] = {
            "total": 0,
            "avg": 0,
            "avg_up": 0,
            "remain": 0,
            "time_range": "",
            "r_num": [],
            "up_list": [],
            "rank_s_list": [],
            "level": 0,
        }

    for gacha_name in gachalogs:
        num = 1
        gacha_data = gachalogs[gacha_name]
        current_data = total_data[gacha_name]
        for index, data in enumerate(gacha_data[::-1]):
            if index == 0:
                current_data["time_range"] = data["time"]
            if index == len(gacha_data) - 1:
                current_data["time_range"] += "~" + data["time"]

            if data["rank_type"] == "4":
                data["gacha_num"] = num
                data["is_up"] = data["name"] not in NORMAL_LIST
                current_data["r_num"].append(num)
                current_data["rank_s_list"].append(data)
                if data["is_up"]:
                    current_data["up_list"].append(data)
                num = 1
            else:
                num += 1
            current_data["total"] += 1

        current_data["remain"] = num - 1
        if current_data["rank_s_list"]:
            current_data["avg"] = round(sum(current_data["r_num"]) / len(current_data["r_num"]), 2)
        else:
            current_data["avg"] = "-"
        if current_data["up_list"]:
            current_data["avg_up"] = round(sum(current_data["r_num"]) / len(current_data["up_list"]), 2)
        else:
            current_data["avg_up"] = "-"

    oset = 260
    bset = 130
    _numlen = 0
    for name in total_data:
        _num = len(total_data[name]["rank_s_list"])
        _numlen += bset * _get_num_h(_num, 4)
    w, h = 950, 350 + len(total_data) * oset + _numlen

    card_img = get_zzz_bg(w, h)
    card_img.paste(player_card, (0, 50), player_card)
    card_draw = ImageDraw.Draw(card_img)

    y = 0
    for gindex, gacha_name in enumerate(total_data):
        gacha_data = total_data[gacha_name]
        title = _draw_gacha_title(gacha_name, gacha_data)
        card_img.paste(title, (0, 227 + y + gindex * oset), title)
        s_list = gacha_data["rank_s_list"]
        for index, item in enumerate(s_list):
            item_bg = await _draw_gacha_item(item)
            _x = 88 + 186 * (index % 4)
            _y = 510 + bset * (index // 4) + y + gindex * oset
            card_img.paste(item_bg, (_x, _y), item_bg)
        if not s_list:
            card_draw.text(
                (475, 505 + y + gindex * oset),
                "当前该卡池暂未有S_Rank数据噢!",
                (157, 157, 157),
                zzz_font_20,
                "mm",
            )
        y += _get_num_h(len(s_list), 4) * 130

    card_img = add_footer(card_img)
    return card_img


def _draw_gacha_title(gacha_name: str, gacha_data: dict) -> Image.Image:
    title = Image.new("RGBA", (950, 240), (40, 40, 40, 200))
    draw = ImageDraw.Draw(title)
    draw.text((50, 40), gacha_name, "white", zzz_font_32, "lm")
    draw.text(
        (50, 90),
        f"Time: {gacha_data['time_range'] or '暂未抽过卡!'}",
        (220, 220, 220),
        zzz_font_18,
        "lm",
    )
    draw.text(
        (50, 130),
        f"Avg: {gacha_data['avg']} | Avg UP: {gacha_data['avg_up']} | Total: {gacha_data['total']} | Remain: {gacha_data['remain']}",
        "white",
        zzz_font_20,
        "lm",
    )
    return title


async def _draw_gacha_item(item: dict) -> Image.Image:
    item_bg = Image.new("RGBA", (186, 130), (30, 30, 30, 200))
    item_draw = ImageDraw.Draw(item_bg)

    try:
        if item["item_type"] == "音擎":
            item_icon = await get_weapon(item["item_id"])
            item_icon = item_icon.resize((100, 100)).convert("RGBA")
            item_bg.paste(item_icon, (43, 5), item_icon)
        elif item["item_type"] == "邦布":
            item_icon = await get_square_bangboo(item["item_id"])
            item_icon = item_icon.resize((100, 100)).convert("RGBA")
            item_bg.paste(item_icon, (43, 5), item_icon)
        else:
            item_icon = await get_square_avatar(item["item_id"])
            item_icon = item_icon.resize((100, 100)).convert("RGBA")
            item_bg.paste(item_icon, (43, 5), item_icon)
    except Exception:
        pass

    gnum = item["gacha_num"]
    gcolor = (255, 20, 20) if gnum >= 80 else (63, 255, 0) if gnum <= 60 else "white"
    item_draw.text((42, 110), f"{gnum}抽", gcolor, zzz_font_20, "mm")
    rank_str = RANK_MAP.get(item["rank_type"], "S")
    rank_icon = get_rank_img(rank_str, 40, 40)
    item_bg.paste(rank_icon, (130, 70), rank_icon)

    if item.get("is_up"):
        item_draw.text((10, 10), "UP", (255, 200, 0), zzz_font_18, "lm")
    return item_bg


def _get_num_h(num: int, column: int):
    if num == 0:
        return 0
    return ((num - 1) // column) + 1


async def _fallback_text(msg: Bot.MessageSession, uid: str, data: dict):
    records = data.get("data", {})
    lines = [f"[ZZZ] UID {uid} Gacha Records", ""]
    for name, items in records.items():
        lines.append(f"{name}: {len(items)} records")
        if items:
            rank5 = sum(1 for i in items if i.get("rank_type") == "4")
            rank4 = sum(1 for i in items if i.get("rank_type") == "3")
            lines.append(f"  S: {rank5}, A: {rank4}")
    await msg.finish(Plain("\n".join(lines)))


RANK_MAP = {
    "4": "S",
    "3": "A",
    "2": "B",
}

NORMAL_LIST = [
    "「11号」",
    "猫又",
    "莱卡恩",
    "丽娜",
    "格莉丝",
    "珂蕾妲",
    "拘缚者",
    "燃狱齿轮",
    "嵌合编译器",
    "钢铁肉垫",
    "硫磺石",
    "啜泣摇篮",
]
