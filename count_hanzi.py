#!/usr/bin/env -S uv run --script

# env needs the -S to use arguments

import sys
import re

def get_char_breakdown(text):
    """
    Returns a dictionary with counts for different CJK ranges.
    """
    # 1. Basic CJK Unified Ideographs (Common)
    # Range: U+4E00 - U+9FFF
    basic_matches = re.findall(r'[\u4e00-\u9fff]', text)

    # 2. Extension A (Rare / Specialized)
    # Range: U+3400 - U+4DBF
    ext_a_matches = re.findall(r'[\u3400-\u4dbf]', text)

    # 3. Extensions B, C, D, E, F (Historical / Classical / Huge)
    # Ranges: Plane 2 and 3. Grouped together as they are rare in modern context.
    # Note: \U000xxxxx format is required for chars outside the basic plane.
    ext_historic_matches = re.findall(r'['
        r'\U00020000-\U0002a6df' # Ext B
        r'\U0002a700-\U0002b73f' # Ext C
        r'\U0002b740-\U0002b81f' # Ext D
        r'\U0002b820-\U0002ceaf' # Ext E
        r'\U0002ceb0-\U0002ebef' # Ext F
    r']', text)

    # 4. Compatibility Ideographs (The "look-alikes")
    # Ranges: F900-FAFF and 2F800-2FA1F
    compat_matches = re.findall(r'[\uf900-\ufaff\U0002f800-\U0002fa1f]', text)

    return {
        "Basic (Common)": len(basic_matches),
        "Extension A (Rare)": len(ext_a_matches),
        "Extension B-F (Historical)": len(ext_historic_matches),
        "Compatibility (Roundtrip)": len(compat_matches)
    }

def print_help():
    print("Generic Hanzi Counter (Detailed)")
    print("================================")
    print("Usage: python count_hanzi.py [filename]")
    print("")
    print("Description:")
    print("  Counts Chinese characters (Hanzi/Kanji) in a text file or stdin.")
    print("  Includes standard CJK, Extensions A-F, and Compatibility characters.")
    print("  Excludes punctuation, alphabets, and numbers.")
    print("")
    print("Options:")
    print("  -h, --help    Show this help message and exit")
    print("")
    print("NOTE ON ARKNIGHTS DATA:")
    print("  This script is for general purpose text.")
    print("  If you are processing Arknights story files (Markdown with HTML tables),")
    print("  please use the specialized 'count_arknights.py' script")
    print("  (often found in the 'arknights' branch).")

def main():
    # Check for help arguments
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_help()
        sys.exit(0)

    totals = {
        "Basic (Common)": 0,
        "Extension A (Rare)": 0,
        "Extension B-F (Historical)": 0,
        "Compatibility (Roundtrip)": 0
    }
    
    input_source = None

    if len(sys.argv) > 1:
        try:
            input_source = open(sys.argv[1], 'r', encoding='utf-8')
        except FileNotFoundError:
            print(f"Error: File '{sys.argv[1]}' not found.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        input_source = sys.stdin

    try:
        for line in input_source:
            line_stats = get_char_breakdown(line)
            for k, v in line_stats.items():
                totals[k] += v
    except UnicodeDecodeError:
        print("Error: Input must be UTF-8 encoded.", file=sys.stderr)
    finally:
        if input_source is not sys.stdin:
            input_source.close()

    # Calculate Grand Total
    grand_total = sum(totals.values())

    # Print Report
    print(f"{'CATEGORY':<30} | {'COUNT':>8}")
    print("-" * 41)
    for category, count in totals.items():
        if count > 0: 
            print(f"{category:<30} | {count:>8}")
    print("-" * 41)
    print(f"{'TOTAL HANZI (字)':<30} | {grand_total:>8}")

if __name__ == "__main__":
    main()
