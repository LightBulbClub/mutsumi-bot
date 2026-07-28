import asyncio
from copy import deepcopy
from typing import Any, Dict, Optional, Union

import httpx

from modules.zzzerouid.database.models import ZzzCookie
from modules.zzzerouid.utils.logger import logger

from .api import GS_BASE, GS_BASE_OS, ZZZ_GAME_INFO_API


class BaseMysApi:
    mysVersion = "2.102.1"

    _HEADER = {
        "x-rpc-app_version": mysVersion,
        "X-Requested-With": "com.mihoyo.hyperion",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 "
            f"miHoYoBBS/{mysVersion}"
        ),
        "x-rpc-client_type": "5",
        "Referer": "https://webstatic.mihoyo.com/",
        "Origin": "https://webstatic.mihoyo.com/",
    }

    async def _mys_request(
        self,
        url: str,
        method: str = "GET",
        header: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        base_url: str = "",
        game_name: str = "",
    ) -> Union[Dict[str, Any], int]:
        full_url = f"{base_url}{url}" if base_url else url
        headers = deepcopy(self._HEADER)
        if header:
            headers.update(header)

        for attempt in range(3):
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                try:
                    resp = await client.request(
                        method,
                        full_url,
                        params=params,
                        json=data,
                        headers=headers,
                    )
                    result = resp.json()
                except Exception as e:
                    logger.error(f"Request failed ({attempt + 1}/3): {full_url} {e}")
                    if attempt == 2:
                        return -999
                    await asyncio.sleep(1)
                    continue

            retcode = result.get("retcode", 0)
            if retcode in (10035, 5003, 10041, 1034):
                logger.warning(f"Captcha/risk: {retcode}")
                return retcode
            if retcode != 0:
                return retcode
            return result

        return -999

    async def get_ck(self, uid: str, mode: str = "RANDOM", game_name: str = "zzz") -> Optional[str]:
        cookie = await ZzzCookie.get_or_none(uid=uid)
        return cookie.cookie if cookie else None

    async def get_user_stoken_by_uid(self, uid: str, game_name: str = "zzz") -> Optional[str]:
        cookie = await ZzzCookie.get_or_none(uid=uid)
        return cookie.stoken if cookie else None

    async def get_user_attr_by_uid(self, uid: str, attr: str, game_name: str = "zzz") -> Any:
        cookie = await ZzzCookie.get_or_none(uid=uid)
        if not cookie:
            return None
        return getattr(cookie, attr, None)

    async def get_user_device_id(self, uid: str, game_name: str = "zzz") -> Optional[str]:
        cookie = await ZzzCookie.get_or_none(uid=uid)
        return cookie.device_id if cookie else None

    async def get_user_fp(self, uid: str, game_name: str = "zzz") -> Optional[str]:
        cookie = await ZzzCookie.get_or_none(uid=uid)
        return cookie.device_fp if cookie else None

    async def get_mihoyo_bbs_info(self, mys_id: str, ck: str, is_os: bool = False) -> Union[Dict[str, Any], int]:
        base_url = GS_BASE_OS if is_os else GS_BASE
        headers = {"Cookie": ck}
        return await self._mys_request(
            ZZZ_GAME_INFO_API,
            "GET",
            header=headers,
            base_url=base_url,
        )
