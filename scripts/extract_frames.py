#!/usr/bin/env python3
"""从视频中均匀抽取关键帧, 供 HTML 摘要配图使用。

用法:
    python extract_frames.py <video> <out_dir> [--count 10]

输出:
    - 在 out_dir 下生成 frame_001.jpg / frame_002.jpg ...
    - 写入 manifest.json: [{"file": 绝对路径, "time_sec": 时间点秒数}, ...]
    - stdout 打印 manifest.json 的绝对路径 (一行)

设计说明:
    - 用 imageio-ffmpeg 自带的 ffmpeg 二进制, 不依赖系统全局 ffmpeg.
    - 先探测视频时长, 再按 count 计算均匀间隔, 保证覆盖全片而非只在开头抽.
    - 抽出的帧是视频真实画面, 不做任何生成/篡改, 满足"配图不失真"要求.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def get_ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def get_duration(exe: str, video: str):
    result = subprocess.run(
        [exe, "-i", video], capture_output=True, text=True, errors="replace"
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", result.stderr)
    if not match:
        return None
    hours, minutes, seconds = int(match.group(1)), int(match.group(2)), float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("out_dir")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()

    out = Path(args.out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("frame_*.jpg"):
        stale.unlink()

    exe = get_ffmpeg()
    duration = get_duration(exe, args.video)
    if not duration or duration <= 0:
        print("无法探测时长, 退化为每 10 秒抽一帧", file=sys.stderr)
        interval = 10.0
    else:
        interval = max(duration / max(args.count, 1), 0.5)

    raw = out / "_raw"
    raw.mkdir(exist_ok=True)
    for stale in raw.glob("*.jpg"):
        stale.unlink()

    cmd = [
        exe, "-y", "-i", args.video,
        "-vf", f"fps=1/{interval:.4f},scale=800:-2",
        "-q:v", "3",
        str(raw / "f_%04d.jpg"),
    ]
    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        print(f"抽帧失败: {exc}", file=sys.stderr)
        return 1

    frames = sorted(raw.glob("f_*.jpg"))
    if not frames:
        print("未抽出任何帧", file=sys.stderr)
        return 1

    if len(frames) > args.count:
        if args.count <= 1:
            picked = [0]
        else:
            picked = sorted(
                {round(i * (len(frames) - 1) / (args.count - 1)) for i in range(args.count)}
            )
        frames = [frames[i] for i in picked]

    manifest = []
    for index, src in enumerate(frames, 1):
        dst = out / f"frame_{index:03d}.jpg"
        src.replace(dst)
        manifest.append({"file": str(dst.resolve()), "time_sec": round((index - 1) * interval, 1)})

    try:
        raw.rmdir()
    except OSError:
        pass

    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(manifest_path.resolve()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
