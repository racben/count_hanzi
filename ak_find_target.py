#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path


HANZI_RE = re.compile(
    r"["
    r"\u4e00-\u9fff"
    r"\u3400-\u4dbf"
    r"\U00020000-\U0002a6df"
    r"\U0002a700-\U0002b73f"
    r"\U0002b740-\U0002b81f"
    r"\U0002b820-\U0002ceaf"
    r"\uf900-\ufaff"
    r"\U0002f800-\U0002fa1f"
    r"]"
)

HEADING_RE = re.compile(r"^#{1,6}\s+")
HTML_TAG_RE = re.compile(r"<[^>]+>")
SPEAKER_OR_LABEL_RE = re.compile(r"^\*\*[^*\n]{1,100}[：:]\*\*$")
ASSET_ID_RE = re.compile(r"^[A-Za-z0-9_./#${}\\-]+(?:\.\w+)?$")


def count_hanzi(text: str) -> int:
    return len(HANZI_RE.findall(text))


def strip_light_markup(text: str) -> str:
    text = HTML_TAG_RE.sub("", text)
    text = text.replace(r"\...", "...")
    text = text.replace(r"\$", "$")
    text = re.sub(r"[*_`~]+", "", text)
    return text


def chapter_id_from_heading(heading_line: str) -> str:
    clean = heading_line.lstrip("#").strip()
    return clean.split()[0] if clean else "UNKNOWN"


def split_markdown_chapters(content: str) -> list[tuple[str, str]]:
    parts = re.split(r"(^##\s+.*$)", content, flags=re.MULTILINE)
    chapters = []

    for i in range(1, len(parts), 2):
        heading = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        chapter_id = chapter_id_from_heading(heading)
        chapters.append((chapter_id, heading + body))

    return chapters


def line_countable_hanzi(raw_line: str, in_description_block: bool) -> int:
    line = raw_line.strip()

    if not line:
        return 0

    if in_description_block:
        return 0

    if HEADING_RE.match(line):
        return 0

    if line.startswith("!["):
        return 0

    if SPEAKER_OR_LABEL_RE.match(line):
        return 0

    if ASSET_ID_RE.match(line):
        return 0

    return count_hanzi(strip_light_markup(line))


def visible_text(raw_line: str) -> str:
    return strip_light_markup(raw_line.strip())


def find_target_line(block: str, target: int):
    cumulative = 0
    in_description_block = False
    lines = block.splitlines()

    for idx, raw_line in enumerate(lines):
        stripped = raw_line.strip()

        if stripped.startswith(":::"):
            in_description_block = not in_description_block
            continue

        n = line_countable_hanzi(raw_line, in_description_block)

        if n == 0:
            continue

        before = cumulative
        after = cumulative + n

        if before < target <= after:
            return idx, before, after

        cumulative = after

    return None, cumulative, cumulative


def print_context(lines: list[str], center_idx: int, before: int = 4, after: int = 6) -> None:
    start = max(0, center_idx - before)
    end = min(len(lines), center_idx + after + 1)

    for i in range(start, end):
        raw = lines[i]
        clean = visible_text(raw)

        if not clean:
            continue

        pointer = ">>>" if i == center_idx else "   "
        print(f"{pointer} {clean}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find the line near X counted Hanzi into an Arknights Markdown chapter."
    )
    parser.add_argument("file", help="Markdown/text file")
    parser.add_argument("chapter", help="Chapter ID, e.g. 13-5 or 13-22")
    parser.add_argument("target", type=int, help="Counted Hanzi into that chapter")
    parser.add_argument(
        "--context",
        type=int,
        default=5,
        help="Number of surrounding lines to print. Default: 5.",
    )

    args = parser.parse_args()

    content = Path(args.file).read_text(encoding="utf-8")
    chapters = dict(split_markdown_chapters(content))

    if args.chapter not in chapters:
        print(f"Chapter not found: {args.chapter}", file=sys.stderr)
        print("Available chapters:", file=sys.stderr)
        print(", ".join(chapters.keys()), file=sys.stderr)
        sys.exit(1)

    block = chapters[args.chapter]
    lines = block.splitlines()

    idx, before_count, after_count = find_target_line(block, args.target)

    if idx is None:
        print(
            f"Target {args.target} 字 is beyond the end of {args.chapter}. "
            f"Chapter has about {before_count} counted 字.",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    print(f"{args.chapter}: target {args.target:,} 字 lands on this line:")
    print(f"Count before line: {before_count:,}")
    print(f"Count after line:  {after_count:,}")
    print()
    print_context(lines, idx, before=args.context, after=args.context)

    search_phrase = visible_text(lines[idx])
    if len(search_phrase) > 40:
        search_phrase = search_phrase[:40]

    print()
    print("Kindle search phrase:")
    print(search_phrase)


if __name__ == "__main__":
    main()
