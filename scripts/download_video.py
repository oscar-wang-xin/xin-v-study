#!/usr/bin/env python3
"""把视频来源统一解析为一个本地文件路径。

用法:
    python download_video.py <source> <work_dir>

    source   : 本地视频文件路径, 或视频网页地址, 或媒体直链(.mp4/.m4a/...)
    work_dir : 下载文件的存放目录 (会被自动创建)

输出:
    stdout 只打印最终本地视频文件的绝对路径 (一行), 供调用方直接取用.
    诊断信息走 stderr.
    失败返回非零退出码.

注意:
    B站/YouTube 等平台若需登录态 (会员/高码率/年龄段), 由调用方按 workflow.md
    的指引配置 cookies, 本脚本不内置任何账号凭据.
"""
import subprocess
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DIRECT_EXT = (
    ".mp4", ".m4a", ".mp3", ".webm", ".mov", ".mkv",
    ".avi", ".flv", ".aac", ".ogg", ".wav", ".ts",
)


def is_direct_media(url: str) -> bool:
    path = url.split("?")[0].split("#")[0].lower()
    return path.endswith(DIRECT_EXT)


def download_direct(url: str, out_path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp, open(out_path, "wb") as fh:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: download_video.py <source> <work_dir>", file=sys.stderr)
        return 2

    source, work_dir = sys.argv[1], sys.argv[2]
    work = Path(work_dir).expanduser()
    work.mkdir(parents=True, exist_ok=True)

    # 1) 本地已存在的普通文件 -> 直接返回; 目录不是视频, 明确报错
    src = Path(source).expanduser()
    if src.is_dir():
        print(f"来源是个目录, 不是视频文件: {source}", file=sys.stderr)
        return 1
    if src.is_file():
        print(str(src.resolve()))
        return 0

    # 2) 网络来源
    if source.startswith(("http://", "https://")):
        if is_direct_media(source):
            ext = Path(source.split("?")[0]).suffix.lower() or ".mp4"
            out = work / f"downloaded{ext}"
            print(f"下载媒体直链 -> {out}", file=sys.stderr)
            try:
                download_direct(source, out)
            except Exception as exc:
                print(f"直链下载失败: {exc}", file=sys.stderr)
                return 1
        else:
            print("用 yt-dlp 下载网页视频...", file=sys.stderr)
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "-f", "best[ext=mp4]/best[height<=1080]/best",
                "--no-playlist",
                "-o", str(work / "downloaded.%(ext)s"),
                source,
            ]
            try:
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as exc:
                print(f"yt-dlp 下载失败: {exc}", file=sys.stderr)
                return 1
            candidates = sorted(
                work.glob("downloaded.*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not candidates:
                print("下载后未找到视频文件", file=sys.stderr)
                return 1
            out = candidates[0]

        print(str(out.resolve()))
        return 0

    print(f"来源既不是本地文件也不是 http(s) 地址: {source}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
