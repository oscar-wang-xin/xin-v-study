#!/usr/bin/env python3
"""扫描视频摘要目录, 生成/更新卡片导航页 _list.html。

用法:
    python update_index.py [output_dir]

默认目录的解析顺序 (先命中先用):
    1. 命令行参数 output_dir
    2. 同项目根目录的 config.json       -> default_output_dir
    3. 同项目根目录的 config.example.json -> default_output_dir
    4. 项目根目录下的 output/
相对路径按项目根目录解析。

行为:
    - 扫描 output_dir 顶层的 *.html (排除 _list.html 和隐藏文件)
    - 从每份摘要提取: 标题、简介、视频来源、创建日期、时长
      优先读结构化 meta 标签, 缺失时降级从页面正文中提取
    - 用 assets/index_template.html 生成自包含的 _list.html
"""
import html as html_module
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
INDEX_NAME = "_list.html"
TEMPLATE = ROOT / "assets" / "index_template.html"


def default_output_dir() -> Path:
    """按 config.json -> config.example.json -> ROOT/output 的顺序取默认目录。"""
    for name in ("config.json", "config.example.json"):
        cfg = ROOT / name
        if not cfg.exists():
            continue
        try:
            value = json.loads(cfg.read_text(encoding="utf-8")).get("default_output_dir")
        except (OSError, ValueError, TypeError) as exc:
            print(f"忽略无效配置 {cfg.name}: {exc}", file=sys.stderr)
            continue
        if not isinstance(value, str) or not value.strip():
            continue
        path = Path(value.strip()).expanduser()
        return path if path.is_absolute() else ROOT / path
    return ROOT / "output"


class MetaParser(HTMLParser):
    """收集 <meta name=... content=...> 和 <title>。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            name = (attrs.get("name") or "").lower().strip()
            content = attrs.get("content")
            if name and content is not None:
                self.meta[name] = content.strip()
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html_module.unescape(fragment)
    return re.sub(r"\s+", " ", fragment).strip()


def find_fragment(source: str, pattern: str) -> str:
    match = re.search(pattern, source, re.DOTALL | re.IGNORECASE)
    return strip_tags(match.group(1)) if match else ""


def to_timestamp(date_text: str, fallback: float) -> float:
    if date_text:
        try:
            return datetime.strptime(date_text[:10], "%Y-%m-%d").timestamp()
        except (ValueError, TypeError):
            pass
    return fallback


def extract_card(path: Path) -> dict:
    source = path.read_text(encoding="utf-8", errors="replace")
    parser = MetaParser()
    try:
        parser.feed(source)
    except Exception:
        pass

    meta = parser.meta
    stat = path.stat()
    fallback_ts = stat.st_ctime

    title = (
        meta.get("video-title")
        or parser.title.strip()
        or path.stem
    )
    desc = (
        meta.get("summary-desc")
        or meta.get("description")
        or find_fragment(source, r'<div\s+class="verdict"[^>]*>.*?<p[^>]*>(.*?)</p>')
    )
    video_source = (
        meta.get("video-source")
        or find_fragment(source, r"来源\s*<b>(.*?)</b>")
    )
    duration = (
        meta.get("video-duration")
        or find_fragment(source, r"时长\s*<b>(.*?)</b>")
        or "—"
    )
    date = (
        meta.get("summary-date")
        or find_fragment(source, r"整理\s*<b>(.*?)</b>")
        or datetime.fromtimestamp(fallback_ts).strftime("%Y-%m-%d")
    )

    return {
        "title": title[:120],
        "desc": desc[:180],
        "source": video_source[:120],
        "date": date[:10],
        "duration": duration[:40],
        "file": path.name,
        "ts": to_timestamp(date, fallback_ts),
    }


def main() -> int:
    output_dir = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    cards = []
    for path in sorted(output_dir.glob("*.html")):
        if path.name == INDEX_NAME or path.name.startswith("."):
            continue
        try:
            cards.append(extract_card(path))
        except Exception as exc:
            print(f"跳过 {path.name}: {exc}", file=sys.stderr)

    cards.sort(key=lambda c: c["ts"], reverse=True)
    payload = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))

    if not TEMPLATE.exists():
        print(f"找不到索引模板: {TEMPLATE}", file=sys.stderr)
        return 1

    template = TEMPLATE.read_text(encoding="utf-8")
    template = re.sub(r"<!--\s*视频摘要索引页模板.*?-->", "", template, count=1, flags=re.DOTALL)
    marker = "/*__CARD_DATA__*/[]"
    if marker not in template:
        print("索引模板缺少数据占位符", file=sys.stderr)
        return 1

    index_html = template.replace(marker, payload, 1)
    index_path = output_dir / INDEX_NAME
    index_path.write_text(index_html, encoding="utf-8")

    print(f"OK: 已生成 {index_path} ({len(cards)} 份摘要)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
