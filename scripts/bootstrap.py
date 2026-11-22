#!/usr/bin/env python3
"""检查并安装 xin-v-study 运行所需的 Python 依赖。

用法:
    python bootstrap.py            # 装齐全部依赖 (含本地转录引擎)
    python bootstrap.py --no-asr   # 只装抽帧/下载依赖, 跳过转录引擎

依赖说明:
    imageio-ffmpeg : 自带 ffmpeg 二进制, 用于从视频抽关键帧 / 抽音频 (无需系统装 ffmpeg)
    yt-dlp         : 下载在线视频 (B站/YouTube 等主流平台)
    faster-whisper : 本地语音转录引擎 (transcribe.py 使用), 不依赖任何宿主工具。

说明: faster-whisper 的 pip 包本身不大, 但模型在首次转录时才下载 (small 约 470 MB),
缓存到本机后即可离线工作。国内模型下载慢可设环境变量 HF_ENDPOINT=https://hf-mirror.com。
"""
import importlib.util
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CORE_REQUIREMENTS = {
    "imageio_ffmpeg": "imageio-ffmpeg>=0.6.0",
    "yt_dlp": "yt-dlp>=2024.1.1",
}
ASR_REQUIREMENTS = {
    "faster_whisper": "faster-whisper>=1.0.0",
}


def main() -> int:
    no_asr = "--no-asr" in sys.argv[1:]
    requirements = dict(CORE_REQUIREMENTS)
    if not no_asr:
        requirements.update(ASR_REQUIREMENTS)

    missing = []
    for module, package in requirements.items():
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        if not found:
            missing.append(package)

    if not missing:
        names = ", ".join(requirements.keys())
        print(f"OK: 依赖已就绪 ({names})")
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
