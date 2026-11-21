#!/usr/bin/env python3
"""检查并安装 xin-v-study 运行所需的 Python 依赖。

用法:
    python bootstrap.py

依赖说明:
    imageio-ffmpeg : 自带 ffmpeg 二进制, 用于从视频抽关键帧 (无需系统安装 ffmpeg)
    yt-dlp         : 下载在线视频 (B站/YouTube 等主流平台)
"""
import importlib.util
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REQUIREMENTS = {
    "imageio_ffmpeg": "imageio-ffmpeg>=0.6.0",
    "yt_dlp": "yt-dlp>=2024.1.1",
}


def main() -> int:
    missing = []
    for module, package in REQUIREMENTS.items():
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        if not found:
            missing.append(package)

    if not missing:
        print("OK: 依赖已就绪 (imageio-ffmpeg, yt-dlp)")
        return 0

    print("缺少依赖, 正在安装: " + ", ".join(missing))
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *missing]
        )
    except subprocess.CalledProcessError as exc:
        print(f"依赖安装失败: {exc}", file=sys.stderr)
        return 1

    print("OK: 依赖安装完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
