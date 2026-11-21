#!/usr/bin/env python3
"""把视频标题清洗为安全的文件名 (不含扩展名)。

用法:
    python sanitize.py "<标题>" [--maxlen 60]

输出:
    stdout 只打印清洗后的文件名 (一行)。
"""
import argparse
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ILLEGAL = r'[<>:"/\\|?*\x00-\x1f]'


def sanitize(title: str, maxlen: int = 60) -> str:
    cleaned = re.sub(ILLEGAL, "", title).strip().strip(". ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if len(cleaned) > maxlen:
        cleaned = cleaned[:maxlen].rstrip()
    return cleaned or "video-summary"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("title", nargs="?", default="video-summary")
    parser.add_argument("--maxlen", type=int, default=60)
    args = parser.parse_args()
    print(sanitize(args.title, args.maxlen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
