import sys
import re

def count_chinese_chars(text):
    """
    Counts Chinese characters (CJK Unified Ideographs) in a string.
    Excludes punctuation, numbers, and Roman script.
    """
    # Regex pattern for the most common CJK Unified Ideographs
    # Range: U+4E00 to U+9FFF
    pattern = r'[\u4e00-\u9fff]'
    matches = re.findall(pattern, text)
    return len(matches)

def main():
    total_count = 0
    input_source = None

    # check if a file argument is provided
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
        # Default to standard input (stdin)
        input_source = sys.stdin

    try:
        # Process line by line to handle large files efficiently
        for line in input_source:
            total_count += count_chinese_chars(line)
    except UnicodeDecodeError:
        print("Error: Input must be UTF-8 encoded.", file=sys.stderr)
    finally:
        if input_source is not sys.stdin:
            input_source.close()

    print(total_count)

if __name__ == "__main__":
    main()
