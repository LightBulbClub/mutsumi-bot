import random
from copy import deepcopy
from typing import Dict, Union

from modules.zzzerouid.database.models import ZzzCookie

from .api import GET_AUTHKEY_URL
from .base_request import BaseMysApi
from .ds import get_web_ds_token, random_hex, random_text


def _build_stoken_cookie(cookie_info: ZzzCookie) -> str:
    """Build a valid Cookie header for the stoken-based genAuthKey request.

    The stored ``stoken`` may be either a cookie-formatted string
    (e.g. ``stuid=xxx;stoken=xxx;mid=xxx``) or a raw stoken token.
    """
    stoken = cookie_info.stoken or ""
    if not stoken:
        return ""
    if "=" in stoken:
        return stoken
    parts = []
    if cookie_info.mys_id:
        parts.append(f"stuid={cookie_info.mys_id}")
    parts.append(f"stoken={stoken}")
    return ";".join(parts)


class SignMysApi(BaseMysApi):
    async def get_authkey_by_cookie(self, uid: str, game_biz: str = "nap_cn", server_id: str = "") -> Union[Dict, int]:
        if not server_id:
            server_id = self.get_server_id(uid)
        HEADER = deepcopy(self._HEADER)
        cookie_info = await ZzzCookie.get_or_none(uid=uid)
        if cookie_info is None or not cookie_info.stoken:
            return -51
        HEADER["Cookie"] = _build_stoken_cookie(cookie_info)
        HEADER["DS"] = get_web_ds_token(True)
        HEADER["User-Agent"] = "okhttp/4.8.0"
        HEADER["x-rpc-app_version"] = self.mysVersion
        HEADER["x-rpc-sys_version"] = "12"
        HEADER["x-rpc-client_type"] = "5"
        HEADER["x-rpc-channel"] = "mihoyo"
        HEADER["x-rpc-device_id"] = random_hex(32)
        HEADER["x-rpc-device_name"] = random_text(random.randint(1, 10))
        HEADER["x-rpc-device_model"] = "Mi 10"
        HEADER["Referer"] = "https://app.mihoyo.com"
        HEADER["Host"] = "api-takumi.mihoyo.com"
        data = await self._mys_request(
            url=GET_AUTHKEY_URL,
            method="POST",
            header=HEADER,
            data={
                "auth_appid": "webview_gacha",
                "game_biz": game_biz,
                "game_uid": uid,
                "region": server_id,
            },
        )
        if isinstance(data, Dict):
            return data["data"]
        return data

    def check_os(self, uid: str) -> bool:
        return len(str(uid)) >= 10

    def get_server_id(self, uid: str) -> str:
        if self.check_os(uid):
            region_map = {
                "10": "prod_gf_us",
                "13": "prod_gf_jp",
                "15": "prod_gf_eu",
                "17": "prod_gf_sg",
            }
            return region_map.get(str(uid)[:2], "prod_gf_jp")
        return "prod_gf_cn"
