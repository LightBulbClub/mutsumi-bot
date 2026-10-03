#!/usr/bin/env python3
"""把目录下的 PNG 转成高质量 JPEG，并把已有的 JPEG 原地重新压缩。

默认处理 assets/modules/wife（递归遍历其下所有角色文件夹）。

用法::

    # 预览：只统计，不写文件、不删文件
    python core/scripts/convert_png_to_jpeg.py --dry-run

    # PNG -> JPEG，画质拉满（quality=100，色度采样 4:4:4）
    python core/scripts/convert_png_to_jpeg.py

    # 把目录里所有图片（含已有 jpg/jpeg）统一重压到 q92
    python core/scripts/convert_png_to_jpeg.py -q 92 --extensions png,jpg,jpeg

    # 换目录 / 只生成 jpg 不删原图
    python core/scripts/convert_png_to_jpeg.py assets/modules/husband -q 95 --keep-original

说明：
* JPEG 不支持透明通道，带透明度的 PNG 会合成到白色背景上。
* 若目标 ``xxx.jpg`` 已存在（同目录下另一个不同图片），默认改为写入 ``xxx_1.jpg``，
  绝不覆盖已有文件；可用 ``--on-collision`` 改为 skip / overwrite。
* ``jpg`` / ``jpeg`` 属于原地重压缩：覆盖同名文件，不产生副本。重新编码有损图
  必然带来一点点代际损失，这类文件请确保有备份（例如 git）。
"""

from __future__ import annotations

import argparse
import os
import stat as stat_module
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "assets" / "modules" / "wife"
JPEG_SUFFIXES = {".jpg", ".jpeg"}


def human_size(num_bytes: float) -> str:
    sign = "-" if num_bytes < 0 else ""
    size = abs(float(num_bytes))
    if size < 1024:
        return f"{sign}{int(size)} B"
    for unit in ("KB", "MB", "GB"):
        size /= 1024
        if size < 1024 or unit == "GB":
            return f"{sign}{size:.1f} {unit}"
    return f"{sign}{size:.1f} GB"


def flatten_to_rgb(image: Image.Image) -> Image.Image:
    """把各种模式的图片统一成不带透明度的 RGB（透明部分填白）。"""
    has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    if has_alpha:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def unique_destination(destination: Path) -> Path:
    """目标已存在时，返回一个不冲突的 ``name_1.jpg`` 之类的路径。"""
    if not destination.exists():
        return destination
    index = 1
    while True:
        candidate = destination.with_name(f"{destination.stem}_{index}{destination.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def verify_jpeg(path: Path, expected_size: tuple[int, int]) -> None:
    """确认写出来的文件真的是能读的 JPEG 且尺寸正确，否则抛异常。"""
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        if image.format != "JPEG":
            raise ValueError(f"输出不是 JPEG：{image.format}")
        if image.size != expected_size:
            raise ValueError(f"尺寸不符：{image.size} != {expected_size}")


@dataclass
class Stats:
    total: int = 0
    converted: int = 0
    skipped: int = 0
    failed: int = 0
    renamed: int = 0
    src_bytes: int = 0
    dst_bytes: int = 0


def convert_one(
    src: Path,
    *,
    quality: int,
    subsampling: int,
    optimize: bool,
    on_collision: str,
    keep_original: bool,
    dry_run: bool,
) -> tuple[str, Path | None, int | None]:
    """转换单个文件，返回 (状态, 目标路径, 目标字节数)。状态为 ok/skip/fail。"""
    in_place = src.suffix.lower() in JPEG_SUFFIXES
    if in_place:
        destination = src
    else:
        destination = src.with_suffix(".jpg")
        if destination.exists() and on_collision == "skip":
            return "skip", None, None
        if destination.exists() and on_collision == "rename":
            destination = unique_destination(destination)

    if dry_run:
        return "ok", destination, None

    src_stat = src.stat()
    with Image.open(src) as image:
        image = ImageOps.exif_transpose(image)
        image.load()
        rgb = flatten_to_rgb(image)
        size = rgb.size

    temp_path = destination.with_name(f".{destination.name}.tmp")
    try:
        rgb.save(
            temp_path,
            format="JPEG",
            quality=quality,
            subsampling=subsampling,
            optimize=optimize,
            progressive=False,
        )
        verify_jpeg(temp_path, size)
        os.replace(temp_path, destination)
        os.chmod(destination, stat_module.S_IMODE(src_stat.st_mode))
        os.utime(destination, ns=(src_stat.st_atime_ns, src_stat.st_mtime_ns))
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    if not in_place and not keep_original:
        src.unlink()

    return "ok", destination, destination.stat().st_size


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="把目录下所有 PNG 转成高质量 JPEG，成功后删除原 PNG。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=DEFAULT_ROOT,
        help="要遍历的目录",
    )
    parser.add_argument("-q", "--quality", type=int, default=100, help="JPEG 质量（1-100）")
    parser.add_argument(
        "--extensions",
        default="png",
        help="要扫描的扩展名，逗号分隔。png 会转成 jpg 并删除原图，jpg/jpeg 会原地重压缩",
    )
    parser.add_argument(
        "--subsampling",
        type=int,
        default=0,
        choices=(0, 1, 2),
        help="色度采样：0=4:4:4（最好），1=4:2:2，2=4:2:0",
    )
    parser.add_argument("--no-optimize", action="store_true", help="关闭 Huffman 优化（更快但文件略大）")
    parser.add_argument(
        "--on-collision",
        choices=("rename", "skip", "overwrite"),
        default="rename",
        help="同名 jpg 已存在时的处理方式",
    )
    parser.add_argument("--keep-original", action="store_true", help="只生成 jpg，不删除原 PNG")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写任何文件")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root: Path = args.root

    if not root.is_dir():
        print(f"目录不存在：{root}", file=sys.stderr)
        return 2
    if not 1 <= args.quality <= 100:
        print("quality 必须在 1-100 之间", file=sys.stderr)
        return 2

    suffixes = {f".{part.strip().lstrip('.').lower()}" for part in args.extensions.split(",") if part.strip()}
    if not suffixes:
        print("--extensions 至少要指定一个扩展名", file=sys.stderr)
        return 2

    sources = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in suffixes)
    if not sources:
        print(f"{root} 下没有找到 {'/'.join(sorted(suffixes))} 图片。")
        return 0

    stats = Stats(total=len(sources))
    for index, src in enumerate(sources, start=1):
        rel = src.relative_to(root)
        before = src.stat().st_size
        stats.src_bytes += before
        try:
            status, destination, after = convert_one(
                src,
                quality=args.quality,
                subsampling=args.subsampling,
                optimize=not args.no_optimize,
                on_collision=args.on_collision,
                keep_original=args.keep_original,
                dry_run=args.dry_run,
            )
        except Exception as error:  # noqa: BLE001 - 单个文件失败不应中断整批任务
            stats.failed += 1
            print(f"[{index}/{stats.total}] 失败 {rel}: {error}")
            continue

        if status == "skip":
            stats.skipped += 1
            stats.src_bytes -= before
            print(f"[{index}/{stats.total}] 跳过 {rel}（{destination.name} 已存在）")
            continue

        stats.converted += 1
        assert destination is not None
        # 原地重压缩（destination 就是源文件）不算改名；只有真的写了别的文件名才算。
        if destination != src and destination.name != f"{src.stem}.jpg":
            stats.renamed += 1
        if after is None:
            print(f"[{index}/{stats.total}] 预演 {rel} -> {destination.name}（{human_size(before)}）")
            continue

        stats.dst_bytes += after
        ratio = (1 - after / before) * 100 if before else 0.0
        if destination == src:
            action = "原地重压缩"
        elif args.keep_original:
            action = "保留原图"
        else:
            action = "已删除原 PNG"
        print(
            f"[{index}/{stats.total}] {rel} -> {destination.name}  "
            f"{human_size(before)} -> {human_size(after)}（{ratio:+.1f}%，{action}）"
        )

    print("\n汇总：")
    print(f"  扫描文件：{stats.total}")
    print(f"  转换成功：{stats.converted}（其中因同名冲突改名：{stats.renamed}）")
    print(f"  跳过：{stats.skipped}    失败：{stats.failed}")
    if args.dry_run:
        print(f"  预演模式，未改动任何文件。原文件合计：{human_size(stats.src_bytes)}")
    else:
        print(f"  原文件合计：{human_size(stats.src_bytes)}")
        print(f"  新文件合计：{human_size(stats.dst_bytes)}")
        saved = stats.src_bytes - stats.dst_bytes
        if stats.src_bytes:
            print(f"  体积变化：{human_size(saved)}（{(saved / stats.src_bytes) * 100:+.1f}%）")
    if stats.renamed:
        print("  提示：有同名 jpg 冲突，已改用 xxx_1.jpg 等新名字，请自行确认是否需要合并。")
    return 1 if stats.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
