from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import orjson

MAP_PATH = Path(__file__).parent / "map"
ALIAS_LIST = Path(__file__).parent / "alias"
CHAR_ALIAS = ALIAS_LIST / "char_alias.json"

# Map files follow the version pattern from the original project.
_PARTENER_FILE = sorted(MAP_PATH.glob("PartnerId2Data_*.json"))[-1]
_WEAPON_FILE = sorted(MAP_PATH.glob("WeaponId2Data_*.json"))[-1]
_EQUIP_FILE = sorted(MAP_PATH.glob("EquipId2Data_*.json"))[-1]


def _load_json(path: Path):
    with open(path, "r", encoding="UTF-8") as f:
        return orjson.loads(f.read())


char_alias_data: Dict[str, List[str]] = _load_json(CHAR_ALIAS)
partener_data: Dict[str, Dict[str, Any]] = _load_json(_PARTENER_FILE)
weapon_data: Dict[str, Any] = _load_json(_WEAPON_FILE)
equip_data: Dict[str, Dict] = _load_json(_EQUIP_FILE)


def char_id_to_sprite(char_id: str) -> str:
    char_id = str(char_id)
    if char_id in partener_data:
        return partener_data[char_id]["sprite_id"]
    else:
        return "28"


def char_id_to_full_name(char_id: str) -> str:
    char_id = str(char_id)
    if char_id in partener_data:
        return partener_data[char_id]["full_name"]
    else:
        return "绳匠"


def equip_id_to_sprite(equip_id: Union[str, int]) -> Optional[str]:
    equip_id = str(equip_id)
    if len(equip_id) == 5:
        suit_id = equip_id[:3] + "00"
        if suit_id in equip_data:
            return equip_data[suit_id]["sprite_file"]


def alias_to_char_name(char_name: str) -> str:
    for i in char_alias_data:
        if (char_name in i) or (char_name in char_alias_data[i]):
            return i
    return char_name


def char_id_to_char_name(char_id: str) -> Optional[str]:
    if char_id in partener_data:
        return partener_data[char_id]["name"]
    else:
        return None


def char_name_to_char_id(char_name: str) -> Optional[str]:
    char_name = alias_to_char_name(char_name)
    for i in partener_data:
        chars = partener_data[i]
        if char_name == chars["name"]:
            return i
    else:
        return None


def get_weapon_data(weapon_id: str) -> Optional[Dict]:
    return weapon_data.get(str(weapon_id))
