#!/usr/bin/env python3
"""把视频里的讲解语音转录成文字稿 —— xin-v-study 的本地转录后端。

纯 Python 命令行，任何 Agent 工具（WorkBuddy / Claude Code / Cursor / Codex /
Gemini CLI / ...）只要能执行命令即可调用。不依赖任何宿主专有工具，模型首次
下载后可完全离线工作。

用法:
    python transcribe.py <video> [options]

参数:
    video              本地视频/音频文件路径（mp4/mkv/mov/mp3/wav ... 均可）

选项:
    --model MODEL      模型规格: tiny / base / small / medium / large-v3（默认 small）
    --language LANG    语言代码, 如 zh / en / ja；不填则自动检测
    --device DEVICE    cpu 或 cuda（默认 cpu）
    --compute-type T   int8 / int8_float16 / float16 / float32（默认 int8）
    --out FILE         文字稿写入文件；不填则写到 stdout
    --srt              输出 SRT 字幕格式（带时间戳）而非纯文字稿
    --timestamps       纯文字稿每行带 [起-止] 时间戳前缀
    --model-dir DIR    模型缓存目录（默认用 HuggingFace 默认缓存）
    --keep-wav         保留抽取的临时 wav（调试用）

首次运行:
    需先安装本地 ASR 引擎:
        python -m pip install faster-whisper
    首次转录会下载所选模型（small 约 470 MB，medium 约 1.5 GB），缓存在本机；
    之后离线可用。中文建议至少 small，追求准确率用 medium / large-v3。

    国内若 HuggingFace 下载慢或失败，先设镜像再运行:
        # Linux / macOS
        export HF_ENDPOINT=https://hf-mirror.com
        # Windows PowerShell
        $env:HF_ENDPOINT="https://hf-mirror.com"
        # Windows CMD
        set HF_ENDPOINT=https://hf-mirror.com

输出:
    stdout（或 --out 指定文件）只有文字稿；诊断信息走 stderr。
    失败返回非零退出码。

模型选择参考（速度与中文准确率的取舍）:
    tiny     最快，中文较差，仅适合确认有没有语音
    base     快，中文一般
    small    默认，中文可用，CPU 上 13 分钟视频约 1-3 分钟
    medium   明显更准，CPU 上较慢，建议有显卡时用
    large-v3 最准，最重，建议 cuda
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

INSTALL_HINT = "python -m pip install faster-whisper"


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def fmt_time(seconds: float) -> str:
    """秒 -> HH:MM:SS,mmm（SRT 用的格式）。"""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def find_ffmpeg() -> str:
    """优先用 imageio-ffmpeg 自带二进制，退而找系统 PATH 里的 ffmpeg。"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        from shutil import which
        exe = which("ffmpeg")
        if exe:
            return exe
    return ""


def extract_wav(video: str, wav_path: Path) -> bool:
    """用 ffmpeg 抽 16kHz 单声道 wav；失败返回 False，让调用方回退到直接喂视频。"""
    exe = find_ffmpeg()
    if not exe:
        log("提示: 未找到 ffmpeg，将直接把原文件交给 ASR 引擎解码。")
        return False
    cmd = [
        exe, "-y", "-i", video,
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(wav_path),
    ]
    try:
        subprocess.check_call(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600
        )
        return wav_path.exists() and wav_path.stat().st_size > 0
    except Exception as exc:
        log(f"抽音频失败，将直接把原文件交给 ASR 引擎解码: {exc}")
        return False


def transcribe(args, audio_path: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        log("缺少本地转录引擎 faster-whisper。请先安装:")
        log("    " + INSTALL_HINT)
        log("安装后重试即可。模型首次使用会自动下载（国内可设 HF_ENDPOINT 镜像，见脚本头部说明）。")
        return None

    model_kwargs = dict(device=args.device, compute_type=args.compute_type)
    if args.model_dir:
        model_kwargs["download_root"] = args.model_dir
    try:
        log(f"加载模型 {args.model}（device={args.device}, compute={args.compute_type}）...")
        model = WhisperModel(args.model, **model_kwargs)
    except Exception as exc:
        log(f"模型加载失败: {exc}")
        if "hf-mirror" not in os.environ.get("HF_ENDPOINT", ""):
            log("若是网络下载失败，国内可设镜像后重试:")
            log('    export HF_ENDPOINT=https://hf-mirror.com   # Windows 用 set 或 $env:')
        return None

    segments, info = model.transcribe(
        audio_path,
        language=args.language,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    log(f"检测语言: {info.language} (置信度 {info.language_probability:.2f})，时长约 {info.duration:.0f} 秒")
    return segments


def render(segments, mode: str) -> str:
    lines = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        if mode == "srt":
            lines.append(f"{len(lines) + 1}")
            lines.append(f"{fmt_time(seg.start)} --> {fmt_time(seg.end)}")
            lines.append(text)
            lines.append("")
        elif mode == "timestamps":
            lines.append(f"[{fmt_time(seg.start)[:-4]} - {fmt_time(seg.end)[:-4]}] {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="本地转录视频语音为文字稿（faster-whisper，无宿主依赖）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="首次使用: " + INSTALL_HINT + "\n模型下载慢时设 HF_ENDPOINT=https://hf-mirror.com",
    )
    parser.add_argument("video")
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--out", default=None)
    parser.add_argument("--srt", action="store_true")
    parser.add_argument("--timestamps", action="store_true")
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--keep-wav", action="store_true")
    args = parser.parse_args()

    video = Path(args.video).expanduser()
    if not video.exists():
        log(f"文件不存在: {video}")
        return 2

    mode = "srt" if args.srt else ("timestamps" if args.timestamps else "text")
    tmp_ctx = tempfile.TemporaryDirectory(prefix="xvs-asr-")
    work = Path(tmp_ctx.name)
    audio = str(video)
    try:
        wav = work / "audio.wav"
        if extract_wav(str(video), wav):
            audio = str(wav)
            log(f"抽音频完成: {wav}")
        segments = transcribe(args, audio)
        if segments is None:
            return 3
        text = render(segments, mode)
        if args.out:
            out = Path(args.out).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            log(f"文字稿已写入: {out.resolve()}")
        else:
            sys.stdout.write(text + "\n")
        return 0
    finally:
        if args.keep_wav:
            tmp_ctx._finalizer.detach()
            log(f"临时文件保留在: {work}")
        else:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
