#!/usr/bin/env python3
import argparse
import re
import sys
from collections import OrderedDict
from pathlib import Path


HANZI_RE = re.compile(
    r"["
    r"\u4e00-\u9fff"          # CJK Unified Ideographs
    r"\u3400-\u4dbf"          # Extension A
    r"\U00020000-\U0002a6df"  # Extension B
    r"\U0002a700-\U0002b73f"  # Extension C
    r"\U0002b740-\U0002b81f"  # Extension D
    r"\U0002b820-\U0002ceaf"  # Extension E
    r"\uf900-\ufaff"          # Compatibility Ideographs
    r"\U0002f800-\U0002fa1f"  # Compatibility Supplement
    r"]"
)

HEADING_RE = re.compile(r"^#{1,6}\s+")
HTML_TAG_RE = re.compile(r"<[^>]+>")

# A line like: **凯尔希：**
# Also catches: **〇〇 选项 1：** and **＞＞ 选项 1 结果：**
SPEAKER_OR_LABEL_RE = re.compile(r"^\*\*[^*\n]{1,100}[：:]\*\*$")

# Asset-code lines like:
# char_003_kalts_1#2
# avg_4088_hodrer_1#1\$1
# bg_coldforest
ASSET_ID_RE = re.compile(r"^[A-Za-z0-9_./#${}\\-]+(?:\.\w+)?$")


def count_hanzi(text: str) -> int:
    return len(HANZI_RE.findall(text))


def strip_light_markup(text: str) -> str:
    """Remove markup that may surround story text, without removing the story text itself."""
    text = HTML_TAG_RE.sub("", text)
    text = text.replace(r"\...", "...")
    text = text.replace(r"\$", "$")
    text = re.sub(r"[*_`~]+", "", text)
    return text


def chapter_id_from_heading(heading_line: str) -> str:
    """
    Extracts the first token after a Markdown heading.

    Example:
      '## 13-22 灾厄积渐 幕间' -> '13-22'
      '## H13-1 湍流行动-1' -> 'H13-1'
    """
    clean = heading_line.lstrip("#").strip()
    return clean.split()[0] if clean else "UNKNOWN"


def count_story_block(
    block: str,
    *,
    include_headings: bool = False,
    include_descriptions: bool = False,
    include_speaker_tags: bool = False,
) -> tuple[int, dict[str, int]]:
    """
    Count Hanzi in one Markdown story block.

    By default, this excludes:
    - Markdown headings
    - speaker labels such as **凯尔希：**
    - choice/result labels such as **〇〇 选项 1：**
    - image lines and asset ID lines
    - ::: description blocks
    """
    total = 0
    skipped = {
        "headings": 0,
        "descriptions": 0,
        "speaker_tags": 0,
        "images": 0,
        "asset_ids": 0,
    }

    in_description_block = False

    for raw_line in block.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        # Toggle fenced description blocks:
        # ::: description
        # ...
        # :::
        if line.startswith(":::"):
            in_description_block = not in_description_block
            continue

        if in_description_block and not include_descriptions:
            skipped["descriptions"] += count_hanzi(line)
            continue

        if HEADING_RE.match(line):
            if include_headings:
                total += count_hanzi(strip_light_markup(line))
            else:
                skipped["headings"] += count_hanzi(line)
            continue

        if line.startswith("!["):
            skipped["images"] += count_hanzi(line)
            continue

        if SPEAKER_OR_LABEL_RE.match(line):
            if include_speaker_tags:
                total += count_hanzi(strip_light_markup(line))
            else:
                skipped["speaker_tags"] += count_hanzi(line)
            continue

        if ASSET_ID_RE.match(line):
            skipped["asset_ids"] += count_hanzi(line)
            continue

        total += count_hanzi(strip_light_markup(line))

    return total, skipped


def split_markdown_chapters(content: str) -> list[tuple[str, str]]:
    """
    Split content into sections by level-2 Markdown headings.

    Returns:
      [(chapter_id, header + body), ...]
    """
    parts = re.split(r"(^##\s+.*$)", content, flags=re.MULTILINE)

    chapters: list[tuple[str, str]] = []

    # Optional preamble before the first ##.
    if parts and parts[0].strip():
        chapters.append(("PREAMBLE", parts[0]))

    # re.split shape:
    # [preamble, header1, body1, header2, body2, ...]
    for i in range(1, len(parts), 2):
        heading = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        chapter_id = chapter_id_from_heading(heading)
        chapters.append((chapter_id, heading + body))

    return chapters


def read_input(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()

    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count Chinese characters in Arknights Markdown story exports."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Markdown/text file to count. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--include-speaker-tags",
        action="store_true",
        help="Include lines like **凯尔希：** in the count.",
    )
    parser.add_argument(
        "--include-headings",
        action="store_true",
        help="Include Markdown headings like ## 13-22 灾厄积渐.",
    )
    parser.add_argument(
        "--include-descriptions",
        action="store_true",
        help="Include ::: description blocks.",
    )
    parser.add_argument(
        "--show-skipped",
        action="store_true",
        help="Show how many Hanzi were skipped by category.",
    )

    args = parser.parse_args()
    content = read_input(args.file)

    chapter_counts: OrderedDict[str, int] = OrderedDict()
    skipped_totals = {
        "headings": 0,
        "descriptions": 0,
        "speaker_tags": 0,
        "images": 0,
        "asset_ids": 0,
    }

    for chapter_id, block in split_markdown_chapters(content):
        count, skipped = count_story_block(
            block,
            include_headings=args.include_headings,
            include_descriptions=args.include_descriptions,
            include_speaker_tags=args.include_speaker_tags,
        )

        # Avoid printing empty boundary headings, e.g. a dangling next-section header.
        if count == 0 and chapter_id != "PREAMBLE":
            continue

        chapter_counts[chapter_id] = chapter_counts.get(chapter_id, 0) + count

        for key, value in skipped.items():
            skipped_totals[key] += value

    print(f"{'CHAPTER':<15} | {'COUNT':>8}")
    print("-" * 26)

    total = 0
    for chapter_id, count in chapter_counts.items():
        print(f"{chapter_id:<15} | {count:>8}")
        total += count

    print("-" * 26)
    print()
    print("-" * 30)
    print(f"TOTAL STORY HANZI: {total:>6}")
    print("-" * 30)

    if args.show_skipped:
        print()
        print("Skipped Hanzi:")
        for key, value in skipped_totals.items():
            print(f"  {key:<14} {value:>6}")


if __name__ == "__main__":
    main()
