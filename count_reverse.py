#!/usr/bin/env -S uv run --script

import sys
import re
from pathlib import Path

# Hanzi ranges: common CJK + ext A + ext B-F + compatibility ideographs
HANZI_RE = re.compile(
    r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff'
    r'\U00020000-\U0002a6df\U0002a700-\U0002b73f'
    r'\U0002b740-\U0002b81f\U0002b820-\U0002ceaf'
    r'\U0002ceb0-\U0002ebef\U0002f800-\U0002fa1f]'
)

PART_HEADER_RE = re.compile(r'^---\s*Part\s+(\d+)\s*:\s*(.*?)\s*---\s*$')
# Reverse script lines are usually like "角色名: 台词"
SPEAKER_RE = re.compile(r'^[^\s:：]{1,40}[：:](.*)$')

# Lines to ignore entirely for story-wordcount purposes
SKIP_PATTERNS = [
    re.compile(r'^===.*===\s*$'),
    re.compile(r'^\s*COMBAT\s*$'),
]


def print_help() -> None:
    print("Reverse 1999 Chapter Hanzi Counter")
    print("=================================")
    print("Usage: python count_reverse.py [filename]")
    print("")
    print("Description:")
    print("  Splits a Reverse 1999 script file into chapters using lines like:")
    print("    --- Part 1: 谶 ---")
    print("  Then counts Hanzi (字) per chapter.")
    print("")
    print("Behavior:")
    print("  - Excludes speaker names before ':' or '：' by default")
    print("  - Includes narration")
    print("  - Skips version headers like '=== 不老春 (Version 3.4) ==='")
    print("  - Skips standalone lines like 'COMBAT'")
    print("")
    print("Options:")
    print("  -h, --help              Show this help message and exit")
    print("  --include-speakers      Count speaker names too")


def is_skippable_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    return any(pat.match(stripped) for pat in SKIP_PATTERNS)


def strip_speaker_prefix(line: str) -> str:
    """Remove leading '角色名:' while keeping the actual spoken text.

    This deliberately only strips short single-segment prefixes before a colon,
    which matches the script format well and avoids mangling narration.
    """
    m = SPEAKER_RE.match(line.strip())
    if m:
        return m.group(1).strip()
    return line


def count_hanzi(text: str) -> int:
    return len(HANZI_RE.findall(text))


def parse_reverse_file(text: str, include_speakers: bool = False):
    parts = []
    current = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip('\n')

        header = PART_HEADER_RE.match(line.strip())
        if header:
            part_num = int(header.group(1))
            part_title = header.group(2)
            current = {
                'part_num': part_num,
                'part_title': part_title,
                'count': 0,
            }
            parts.append(current)
            continue

        if current is None:
            # Ignore anything before the first Part header.
            continue

        if is_skippable_line(line):
            continue

        content = line if include_speakers else strip_speaker_prefix(line)
        current['count'] += count_hanzi(content)

    return parts


def print_table(parts, filename: str) -> None:
    title_width = max(len('CHAPTER'), *(len(f"Part {p['part_num']}: {p['part_title']}") for p in parts)) if parts else len('CHAPTER')
    count_width = max(len('字数'), *(len(str(p['count'])) for p in parts)) if parts else len('字数')

    print(f"File: {filename}")
    print(f"{'CHAPTER':<{title_width}} | {'字数':>{count_width}}")
    print('-' * (title_width + count_width + 3))

    total = 0
    for p in parts:
        label = f"Part {p['part_num']}: {p['part_title']}"
        print(f"{label:<{title_width}} | {p['count']:>{count_width}}")
        total += p['count']

    print('-' * (title_width + count_width + 3))
    print(f"{'TOTAL':<{title_width}} | {total:>{count_width}}")


def main() -> None:
    args = sys.argv[1:]

    if args and args[0] in ['-h', '--help']:
        print_help()
        sys.exit(0)

    include_speakers = False
    if '--include-speakers' in args:
        include_speakers = True
        args = [a for a in args if a != '--include-speakers']

    if len(args) > 1:
        print("Error: Too many arguments.", file=sys.stderr)
        print("Usage: python count_reverse.py [filename] [--include-speakers]", file=sys.stderr)
        sys.exit(1)

    if len(args) == 1:
        path = Path(args[0])
        try:
            text = path.read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"Error: File '{path}' not found.", file=sys.stderr)
            sys.exit(1)
        except UnicodeDecodeError:
            print("Error: Input must be UTF-8 encoded.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        filename = str(path)
    else:
        try:
            text = sys.stdin.read()
        except UnicodeDecodeError:
            print("Error: Input must be UTF-8 encoded.", file=sys.stderr)
            sys.exit(1)
        filename = '<stdin>'

    parts = parse_reverse_file(text, include_speakers=include_speakers)

    if not parts:
        print("No chapter markers found. Expected lines like: --- Part 1: 谶 ---", file=sys.stderr)
        sys.exit(1)

    print_table(parts, filename)


if __name__ == '__main__':
    main()
