import time
import asyncio
from copy import deepcopy
from typing import Dict, List, Union, Optional, Literal

import httpx

from modules.zzzerouid.database.models import ZzzCookie

from .base_request import BaseMysApi
from .api import (
    ANN_API,
    ENKA_API,
    MINIGG_API,
    ZZZ_API,
    ZZZ_OS_API,
    ZZZ_BIND_API,
    ZZZ_NOTE_API,
    ZZZ_ABYSS_API,
    ZZZ_HADAL_API,
    ZZZ_INDEX_API,
    ZZZ_MONTH_INFO,
    ZZZ_MEM,
    ZZZ_BIND_OS_API,
    ZZZ_CHALLENGE_API,
    ZZZ_GAME_INFO_API,
    ZZZ_BUDDY_INFO_API,
    ZZZ_AVATAR_INFO_API,
    ZZZ_NOTE_WIDGET_API,
    ZZZ_VOID_BATTLE_API,
    ZZZ_AVATAR_BASIC_API,
    ZZZ_GET_GACHA_LOG_API,
)

REGION_MAP = {
    "10": "prod_gf_us",
    "13": "prod_gf_jp",
    "15": "prod_gf_eu",
    "17": "prod_gf_sg",
}


class ZZZApi(BaseMysApi):
    def __init__(self):
        self.ZZZ_HEADER = deepcopy(self._HEADER)
        del self.ZZZ_HEADER["x-rpc-client_type"]
        self.ZZZ_HEADER.update(
            {
                "x-rpc-page": "v1.0.14_#/zzz",
                "x-rpc-platform": "2",
                "Referer": "https://act.mihoyo.com/",
                "Origin": "https://act.mihoyo.com",
            }
        )

    def _get_region(self, uid: str):
        if len(uid) < 10:
            return "prod_gf_cn"
        return REGION_MAP.get(uid[:2], "prod_gf_jp")

    async def zzz_get_ck(self, uid: str, mode: Literal["OWNER", "RANDOM"] = "RANDOM") -> Optional[str]:
        return await self.get_ck(uid, mode, "zzz")

    async def get_stoken(self, uid: str) -> Optional[str]:
        cookie = await ZzzCookie.get_or_none(uid=uid)
        return cookie.stoken if cookie else None

    async def get_zzz_ann(
        self,
        uid: str,
        platform: str = "pc",
        _type: Literal["getAnnList", "getAnnContent", "consumeRemind"] = "getAnnList",
        ann_id: Union[int, str] = "0",
    ):
        params = {
            "game": "nap",
            "game_biz": "nap_cn",
            "lang": "zh-cn",
            "bundle_id": "nap_cn",
            "channel_id": "1",
            "level": "58",
            "platform": platform,
            "region": "prod_gf_cn",
            "uid": uid,
        }
        if _type == "consumeRemind":
            params["ann_id"] = str(ann_id)

        data = await self._mys_request(
            f"{ANN_API}/{_type}",
            "GET",
            params=params,
        )
        if isinstance(data, Dict) and _type == "getAnnList":
            data = data["data"]
        elif isinstance(data, Dict) and _type == "consumeRemind":
            data = data["retcode"]
        return data

    async def get_zzz_user_info_g(self, uid: str) -> Union[Dict, int]:
        is_os = False if len(uid) < 10 else True
        cookie = await ZzzCookie.get_or_none(uid=uid)
        mys_id = cookie.mys_id if cookie else None
        if mys_id is None:
            return -100
        ck = await self.zzz_get_ck(uid, "OWNER")
        if ck is None:
            return -51

        data = await self.get_mihoyo_bbs_info(mys_id, ck, is_os)
        if isinstance(data, int):
            return data
        for i in data:
            if uid == i["game_role_id"] and i["game_id"] == 8:
                return i
        return -51

    async def get_zzz_user_info(self, uid: str) -> Union[int, Dict]:
        base_url = ZZZ_BIND_API if len(uid) < 10 else ZZZ_BIND_OS_API

        header = deepcopy(self.ZZZ_HEADER)
        ck = await self.zzz_get_ck(uid, "OWNER")
        if not ck:
            return -51
        header["Cookie"] = ck
        data = await self._mys_request(
            ZZZ_GAME_INFO_API,
            header=header,
            base_url=base_url,
        )
        if isinstance(data, Dict):
            for i in data["data"]["list"]:
                if uid == i["game_uid"]:
                    return i
            return -51
        return data

    async def get_zzz_enka_data(self, uid: str, API_SOURCE: Literal["ENKA", "MINIGG"] = "ENKA") -> Union[int, Dict]:
        API = ENKA_API if API_SOURCE == "ENKA" else MINIGG_API
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(API.format(uid))
            if resp.status_code != 200:
                return -1
            return resp.json()

    async def get_zzz_note_info(self, uid: str) -> Union[int, Dict]:
        data = await self.simple_zzz_req(ZZZ_NOTE_API, uid)
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_mem_info(self, uid: str, schedule_type: int = 1) -> Union[int, Dict]:
        data = await self.simple_zzz_req(
            ZZZ_MEM,
            uid,
            params={
                "uid": uid,
                "lang": "zh-cn",
                "region": self._get_region(uid),
                "schedule_type": schedule_type,
            },
        )
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_void_info(self, uid: str) -> Union[int, Dict]:
        data = await self.simple_zzz_req(
            ZZZ_VOID_BATTLE_API,
            uid,
            params={
                "uid": uid,
                "region": self._get_region(uid),
                "void_front_id": "102",
            },
        )
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_widget_info(self, uid: str) -> Union[int, Dict]:
        cookie = await ZzzCookie.get_or_none(uid=uid)
        if not cookie or not cookie.stoken:
            return -51
        data = await self.simple_zzz_req(ZZZ_NOTE_WIDGET_API, uid, params=None, cookie=cookie.stoken)
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_index_info(self, uid: str) -> Union[int, Dict]:
        data = await self.simple_zzz_req(ZZZ_INDEX_API, uid)
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_month_info(self, uid: str, month: str = "") -> Union[int, Dict]:
        header = deepcopy(self.ZZZ_HEADER)
        ck = await self.zzz_get_ck(uid, "OWNER")
        if ck is None:
            return -51
        header["Cookie"] = ck
        data = await self._mys_request(
            url=ZZZ_MONTH_INFO,
            base_url="https://api-takumi.mihoyo.com/event/nap_ledger",
            method="GET",
            header=header,
            params={
                "uid": uid,
                "region": self._get_region(uid),
                "month": month,
            },
            game_name="zzz",
        )
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_challenge_info(self, uid: str, schedule_type: int = 1) -> Union[int, Dict]:
        data = await self.simple_zzz_req(ZZZ_CHALLENGE_API, uid, params={"schedule_type": schedule_type})
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_abyss_info(self, uid: str) -> Union[int, Dict]:
        data = await self.simple_zzz_req(ZZZ_ABYSS_API, uid)
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_hadal_info(self, uid: str, schedule_type: int = 1) -> Union[int, Dict]:
        data = await self.simple_zzz_req(ZZZ_HADAL_API, uid, params={"schedule_type": schedule_type})
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_bangboo_info(self, uid: str) -> Union[int, List[Dict]]:
        data = await self.simple_zzz_req(ZZZ_BUDDY_INFO_API, uid)
        if isinstance(data, Dict):
            return data["data"]["list"]
        return data

    async def get_zzz_avatar_info(
        self,
        uid: str,
        id_list: Union[List[int], List[str]],
    ) -> Union[int, List[Dict]]:
        ck = await self.zzz_get_ck(uid, "OWNER")
        if ck is None:
            return -51
        _header = deepcopy(self.ZZZ_HEADER)

        device_id = await self.get_user_device_id(uid, "zzz")
        fp = await self.get_user_fp(uid, "zzz")

        if fp is not None:
            _header["x-rpc-device_fp"] = fp
        if device_id is not None:
            _header["x-rpc-device_id"] = device_id

        tasks = []
        for i in id_list:
            tasks.append(
                self.simple_zzz_req(
                    ZZZ_AVATAR_INFO_API,
                    uid,
                    params={
                        "id_list[]": str(i),
                        "need_wiki": False,
                    },
                    header=_header,
                    cookie=ck,
                )
            )
        data = await asyncio.gather(*tasks)
        if all(isinstance(i, int) for i in data):
            return data[0]
        result = []
        for i in data:
            if isinstance(i, Dict):
                result.extend(i["data"]["avatar_list"])
        return result

    async def get_zzz_avatar_basic_info(self, uid: str) -> Union[int, List[Dict]]:
        data = await self.simple_zzz_req(ZZZ_AVATAR_BASIC_API, uid)
        if isinstance(data, Dict):
            return data["data"]["avatar_list"]
        return data

    async def get_zzz_gacha_log_by_authkey(
        self,
        uid: str,
        authkey: str,
        gacha_type: str = "2001",
        init_log_gacha_base_type: str = "2",
        page: int = 1,
        end_id: str = "0",
    ):
        server_id = self._get_region(uid)
        data = await self._mys_request(
            url=ZZZ_GET_GACHA_LOG_API,
            method="GET",
            header=self._HEADER,
            params={
                "authkey_ver": "1",
                "sign_type": "2",
                "auth_appid": "webview_gacha",
                "init_log_gacha_type": gacha_type,
                "init_log_gacha_base_type": init_log_gacha_base_type,
                "gacha_id": "2c1f5692fdfbb733a08733f9eb69d32aed1d37",
                "timestamp": str(int(time.time())),
                "lang": "zh-cn",
                "device_type": "mobile",
                "plat_type": "ios",
                "region": server_id,
                "authkey": authkey,
                "game_biz": "nap_cn",
                "gacha_type": gacha_type,
                "real_gacha_type": init_log_gacha_base_type,
                "page": page,
                "size": "20",
                "end_id": end_id,
            },
        )
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def get_zzz_gacha_record_by_link(
        self,
        url: str,
        gacha_type: str = "2001",
        page: int = 1,
        page_size: int = 10,
    ) -> Union[int, Dict]:
        if url is None:
            raise Exception("[ZZZ] gacha_record url is None")
        data = await self._mys_request(
            url=url,
            method="GET",
            params={
                "size": page_size,
                "page": page,
                "gacha_type": gacha_type,
                "init_log_gacha_type": gacha_type,
            },
        )
        if isinstance(data, Dict):
            return data["data"]
        return data

    async def simple_zzz_req(
        self,
        URL: str,
        uid: str,
        params: Optional[Dict] = {},  # noqa: B006
        header: Dict = {},  # noqa: B006
        cookie: Optional[str] = None,
    ) -> Union[Dict, int]:
        server_id = self._get_region(uid)
        base_url = ZZZ_API if len(uid) < 10 else ZZZ_OS_API

        if params is None:
            params = {}
        else:
            params.update({"role_id": uid, "server": server_id})

        HEADER = deepcopy(self.ZZZ_HEADER)
        HEADER.update(header)

        if cookie is not None:
            HEADER["Cookie"] = cookie
        elif "Cookie" not in HEADER and isinstance(uid, str):
            ck = await self.zzz_get_ck(uid)
            if ck is None:
                return -51
            HEADER["Cookie"] = ck

        return await self._mys_request(
            url=URL,
            method="GET",
            header=HEADER,
            params=params,
            base_url=base_url,
            game_name="zzz",
        )
