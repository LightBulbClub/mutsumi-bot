import asyncio
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup
from core.builtins.bot import Bot
from core.builtins.message.internal import Plain
from core.utils.http import get_url
from httpx import AsyncClient

from ..config import RESOURCE_CDN
from ..utils.resource import (
    CAMP_PATH,
    CAT_GUIDE_PATH,
    CUSTOM_PATH,
    FLOWER_GUIDE_PATH,
    MIND_PATH,
    ROLECIRCLE_PATH,
    ROLEGENERAL_PATH,
    ROLE_PATH,
    SQUARE_BANGBOO,
    SUIT_3D_PATH,
    SUIT_PATH,
    WEAPON_PATH,
)

EPATH_MAP = {
    "guide/flower": FLOWER_GUIDE_PATH,
    "guide/cat": CAT_GUIDE_PATH,
    "resource/weapon": WEAPON_PATH,
    "resource/role_circle": ROLECIRCLE_PATH,
    "resource/role_general": ROLEGENERAL_PATH,
    "resource/role": ROLE_PATH,
    "resource/3d_suit": SUIT_3D_PATH,
    "resource/suit": SUIT_PATH,
    "resource/camp": CAMP_PATH,
    "resource/mind": MIND_PATH,
    "resource/square_bangbo": SQUARE_BANGBOO,
    "custom": CUSTOM_PATH,
}

DEFAULT_CDN = "https://file.minigg.cn/sayu-bot/ZZZeroUID"
BATCH_SIZE = 1_500_000


async def _list_directory(url: str) -> list[tuple[str, str, int | None]]:
    """Return (name, href, size_bytes or None) for directory entries."""
    html = await get_url(url, timeout=30)
    soup = BeautifulSoup(html, "html.parser")
    pre = soup.find("pre")
    if pre is None:
        return []
    items: list[tuple[str, str, int | None]] = []
    for a in pre.find_all("a"):
        href = a.get("href")
        if not href or href == "../":
            continue
        name = unquote(href.rstrip("/").split("/")[-1])
        size_text = ""
        node = a.next_sibling
        while node and not getattr(node, "name", None):
            size_text += str(node)
            node = node.next_sibling
        size_text = size_text.strip()
        size: int | None = None
        if size_text and size_text.replace("-", ""):
            try:
                size = int(size_text)
            except ValueError:
                size = None
        items.append((name, href, size))
    return items


async def _download_directory(
    base_url: str,
    endpoint: str,
    local_dir: Path,
    client: AsyncClient,
    lines: list[str],
) -> int:
    url = f"{base_url}/{endpoint}/"
    try:
        entries = await _list_directory(url)
    except Exception as e:
        lines.append(f"  {endpoint}: list failed ({type(e).__name__})")
        return 0

    if not entries:
        lines.append(f"  {endpoint}: empty")
        return 0

    tasks: list[asyncio.Task] = []
    total_size = 0
    downloaded = 0

    for name, href, size in entries:
        if href.endswith("/"):
            sub_endpoint = f"{endpoint}/{href.rstrip('/')}"
            sub_dir = local_dir / name
            sub_dir.mkdir(parents=True, exist_ok=True)
            tasks.append(asyncio.create_task(_download_directory(base_url, sub_endpoint, sub_dir, client, lines)))
            continue

        file_path = local_dir / name
        if file_path.exists() and size is not None:
            if file_path.stat().st_size == size:
                continue

        file_url = f"{url}{href}"
        tasks.append(asyncio.create_task(_download_file(file_url, file_path, client)))
        downloaded += 1
        if size:
            total_size += size
        if total_size >= BATCH_SIZE:
            await asyncio.gather(*tasks)
            tasks.clear()
            total_size = 0

    if tasks:
        await asyncio.gather(*tasks)

    lines.append(f"  {endpoint}: {downloaded} new/changed")
    return downloaded


async def _download_file(url: str, path: Path, client: AsyncClient) -> None:
    resp = await client.get(url)
    resp.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)


async def download_assets(msg: Bot.MessageSession):
    cdn_url = str(RESOURCE_CDN)
    lines = [f"[ZZZ] Start downloading resources from {cdn_url}", ""]
    total = 0

    async with AsyncClient(timeout=300) as client:
        for endpoint, path in EPATH_MAP.items():
            total += await _download_directory(cdn_url, endpoint, path, client, lines)

    lines.append("")
    lines.append(msg.locale.t("zzzerouid.message.download.done", count=total))
    await msg.finish(Plain("\n".join(lines)))
