from pathlib import Path

ASSETS_PATH = Path(__file__).parents[3] / "assets"
RES_PATH = ASSETS_PATH / "modules" / "zzzerouid"

TEXTURE2D_PATH = RES_PATH / "texture2d"
FONT_PATH = RES_PATH / "fonts"
PLAYER_PATH = RES_PATH / "players"
CU_BG_PATH = RES_PATH / "custom"
WIKI_PATH = RES_PATH / "wiki"
GUIDE_PATH = RES_PATH / "guide"
FLOWER_GUIDE_PATH = GUIDE_PATH / "flower"
CAT_GUIDE_PATH = GUIDE_PATH / "cat"
CUSTOM_PATH = RES_PATH / "custom"

RESOURCE_PATH = RES_PATH / "resource"
WEAPON_PATH = RESOURCE_PATH / "weapon"
ROLECIRCLE_PATH = RESOURCE_PATH / "role_circle"
ROLEGENERAL_PATH = RESOURCE_PATH / "role_general"
ROLE_PATH = RESOURCE_PATH / "role"
SUIT_PATH = RESOURCE_PATH / "suit"
SUIT_3D_PATH = RESOURCE_PATH / "3d_suit"
CAMP_PATH = RESOURCE_PATH / "camp"
MIND_PATH = RESOURCE_PATH / "mind"
SQUARE_BANGBOO = RESOURCE_PATH / "square_bangbo"
SQUARE_AVATAR = RESOURCE_PATH / "square_avatar"
BBS_T_PATH = RESOURCE_PATH / "bbs_t"
MONSTER_PATH = RESOURCE_PATH / "monster"
TEMP_PATH = RESOURCE_PATH / "temp"

ZZZ_DATA_PATH = RES_PATH / "zzz_data"
CHAR_DATA_PATH = ZZZ_DATA_PATH / "char"


def resource_path(name: str) -> Path:
    return RES_PATH / name


def texture2d_path(name: str) -> Path:
    return TEXTURE2D_PATH / name


def ensure_dirs():
    for p in [
        RES_PATH,
        TEXTURE2D_PATH,
        FONT_PATH,
        PLAYER_PATH,
        CU_BG_PATH,
        WIKI_PATH,
        GUIDE_PATH,
        FLOWER_GUIDE_PATH,
        CAT_GUIDE_PATH,
        CUSTOM_PATH,
        RESOURCE_PATH,
        WEAPON_PATH,
        ROLECIRCLE_PATH,
        ROLEGENERAL_PATH,
        ROLE_PATH,
        SUIT_PATH,
        SUIT_3D_PATH,
        CAMP_PATH,
        MIND_PATH,
        SQUARE_BANGBOO,
        SQUARE_AVATAR,
        BBS_T_PATH,
        MONSTER_PATH,
        TEMP_PATH,
        ZZZ_DATA_PATH,
        CHAR_DATA_PATH,
    ]:
        p.mkdir(parents=True, exist_ok=True)


ensure_dirs()
