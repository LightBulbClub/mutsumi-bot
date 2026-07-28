from pathlib import Path
from typing import Union

from PIL import Image, UnidentifiedImageError

from core.utils.http import download

from ..api.api import (
    V2_ZZZ_SQUARE_AVATAR,
    V2_ZZZ_SQUARE_BANGBOO,
    ZZZ_SQUARE_AVATAR,
    ZZZ_SQUARE_BANGBOO,
)
from .name_convert import get_weapon_data
from .resource import (
    BBS_T_PATH,
    MONSTER_PATH,
    SQUARE_AVATAR,
    SQUARE_BANGBOO,
    TEMP_PATH,
    TEXTURE2D_PATH,
    WEAPON_PATH,
)


def get_source(img: Union[Image.Image, Path], w: int, h: int):
    if isinstance(img, Path):
        _img = Image.open(img).convert("RGBA")
    else:
        _img = img.convert("RGBA")
    scale = w / _img.size[0]
    img = _img.resize((w, int(_img.size[1] * scale)))
    return img


async def get_square_avatar(char_id: Union[str, int]) -> Image.Image:
    name = f"role_square_avatar_{char_id}.png"
    url = f"{ZZZ_SQUARE_AVATAR}/{name}"
    new_url = f"{V2_ZZZ_SQUARE_AVATAR}/{name}"
    path = SQUARE_AVATAR / name

    if path.exists():
        try:
            return get_source(path, 152, 186)
        except UnidentifiedImageError:
            pass

    result = await download(new_url, filename=name, path=SQUARE_AVATAR)
    if result is None:
        await download(url, filename=name, path=SQUARE_AVATAR)

    return get_source(path, 152, 186)


async def get_square_bangboo(bangboo_id: Union[str, int]) -> Image.Image:
    name = f"bangboo_rectangle_avatar_{bangboo_id}.png"
    url = f"{ZZZ_SQUARE_BANGBOO}/{name}"
    new_url = f"{V2_ZZZ_SQUARE_BANGBOO}/{name}"
    path = SQUARE_BANGBOO / name

    if path.exists():
        try:
            return get_source(path, 152, 186)
        except UnidentifiedImageError:
            pass

    result = await download(new_url, filename=name, path=SQUARE_BANGBOO)
    if result is None:
        await download(url, filename=name, path=SQUARE_BANGBOO)

    return get_source(path, 152, 186)


async def download_image(url: str, path: Path, name: str) -> Image.Image | None:
    file_path = path / name
    if file_path.exists():
        try:
            return Image.open(file_path).convert("RGBA")
        except UnidentifiedImageError:
            pass

    result = await download(url, filename=name, path=path)
    if result is None:
        return None
    return Image.open(result).convert("RGBA")


async def get_weapon(weapon_id: Union[str, int]) -> Image.Image:
    img = Image.new("RGBA", (400, 400))
    weapon_info = get_weapon_data(str(weapon_id))
    if not weapon_info:
        return img
    path_1 = WEAPON_PATH / f"{weapon_info['code_name']}.png"
    path_2 = WEAPON_PATH / f"{weapon_info['code_name']}_High.png"
    if path_2.exists():
        weapon_img = Image.open(path_2)
    elif path_1.exists():
        weapon_img = Image.open(path_1)
    else:
        return img
    weapon_img = weapon_img.convert("RGBA")
    x, y = weapon_img.size
    img.paste(weapon_img, (200 - x // 2, 200 - y // 2), weapon_img)
    return img


async def draw_boss(boss: dict, text_path: Path | None = None) -> Image.Image:
    if text_path is None:
        text_path = TEXTURE2D_PATH / "zzzerouid_mem"

    boss_mask = Image.open(text_path / "monster_mask.png")
    boss_fg = Image.open(text_path / "monster_fg.png")
    boss_card = Image.new("RGBA", (241, 333))

    boss_name = boss["name"]
    boss_race = boss.get("race_icon", "")
    race_name = boss_race.split("/")[-1] if boss_race else ""
    boss_icon = boss["icon"]
    boss_bg = boss["bg_icon"]
    boss_bg_name = boss_bg.split("/")[-1]

    bg_path = BBS_T_PATH / boss_bg_name
    if not bg_path.exists():
        await download_image(boss_bg, BBS_T_PATH, boss_bg_name)
    if bg_path.exists():
        bg_img = Image.open(bg_path).resize((241, 333))
    else:
        bg_img = Image.new("RGBA", (241, 333), (0, 0, 0, 0))

    boss_path = MONSTER_PATH / f"{boss_name}.png"
    if "?" in boss_name or "？" in boss_name:
        boss_name = boss_icon.split("/")[-1].split(".")[0]
        boss_path = MONSTER_PATH / f"{boss_name}.png"

    if not boss_path.exists():
        await download_image(boss_icon, MONSTER_PATH, f"{boss_name}.png")
    if boss_path.exists():
        boss_img = Image.open(boss_path).resize((241, 333))
        bg_img.paste(boss_img, (0, 0), boss_img)

    if boss_race:
        race_path = TEMP_PATH / race_name
        if not race_path.exists():
            await download_image(boss_race, TEMP_PATH, race_name)
        if race_path.exists():
            race_img = Image.open(race_path).resize((110, 110))
            bg_img.paste(race_img, (115, 212), race_img)

    bg_img.paste(boss_fg, (0, 0), boss_fg)
    boss_card.paste(bg_img, (0, 0), boss_mask)
    return boss_card
