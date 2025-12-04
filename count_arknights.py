import sys
import re
from collections import defaultdict

def count_hanzi(text):
    """
    Counts Chinese characters using the comprehensive regex ranges.
    """
    if not text:
        return 0
        
    hanzi_pattern = re.compile(r'['
        r'\u4e00-\u9fff'          # Basic
        r'\u3400-\u4dbf'          # Ext A
        r'\U00020000-\U0002a6df'  # Ext B
        r'\U0002a700-\U0002b73f'  # Ext C
        r'\U0002b740-\U0002b81f'  # Ext D
        r'\U0002b820-\U0002ceaf'  # Ext E
        r'\uf900-\ufaff'          # Compatibility
        r'\U0002f800-\U0002fa1f'  # Compat Supplement
    r']')
    return len(hanzi_pattern.findall(text))

def clean_html_tags(text):
    """Removes <p>, <br>, etc. from a string."""
    return re.sub(r'<[^>]+>', '', text)

def process_block(content):
    """
    Processes a specific block of text (chapter or section) to count
    Dialogue and Narration characters.
    """
    dialogue_count = 0
    narration_count = 0
    
    # --- PHASE 1: Extract Dialogue (The "td-text" cells) ---
    dialogue_pattern = re.compile(r'<td class="td-text"[^>]*>(.*?)</td>', re.DOTALL)
    
    dialogue_matches = dialogue_pattern.findall(content)
    for match in dialogue_matches:
        clean_text = clean_html_tags(match)
        dialogue_count += count_hanzi(clean_text)

    # --- PHASE 2: Remove Tables to isolate Narration ---
    content_without_tables = re.sub(r'<table.*?</table>', '', content, flags=re.DOTALL)

    # --- PHASE 3: Process Narration (What's left) ---
    lines = content_without_tables.splitlines()
    for line in lines:
        s = line.strip()
        
        # SKIP: Empty lines
        if not s: continue
        
        # SKIP: YAML Frontmatter and Metadata headers
        if s.startswith('---') or s.startswith('title:') or s.startswith('author:') or s.startswith('lang:'):
            continue

        # SKIP: Images (![](...))
        if s.startswith('!['):
            continue
            
        # SKIP: System/Asset Codes & Metadata
        if re.match(r'^[a-zA-Z0-9_#\$\{\}\[\]\.]+$', s):
            continue
        
        # SKIP: Specific Game Data headers
        if s.startswith('Script Version') or s.startswith('Game data'):
            continue
            
        # SKIP: Game Logic (Options/Medal descriptions)
        if s.startswith(':::') or s.startswith('medal_'):
            continue

        narration_count += count_hanzi(s)

    return dialogue_count, narration_count

def main():
    content = ""
    if len(sys.argv) < 2:
        content = sys.stdin.read()
    else:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Split the content by Level 2 Markdown Headers (## Chapter Title)
    # capturing the delimiter so we know which chapter it is.
    parts = re.split(r'(^##\s+.*$)', content, flags=re.MULTILINE)

    chapter_stats = defaultdict(int)
    total_d = 0
    total_n = 0

    # 1. Process Preamble (Before first ##)
    # usually metadata, but good to check
    d, n = process_block(parts[0])
    total_d += d
    total_n += n

    # 2. Process Chapters
    # re.split returns [Preamble, Header1, Body1, Header2, Body2, ...]
    for i in range(1, len(parts), 2):
        header_line = parts[i].strip()
        body_text = parts[i+1]

        # Extract Chapter ID (e.g. "11-1" from "## 11-1 维护荣耀")
        clean_header = header_line.replace('#', '').strip()
        if not clean_header: continue
        
        # Assume the first word is the Chapter ID
        chapter_id = clean_header.split()[0]

        d, n = process_block(body_text)
        
        # Aggregate counts (handles cases like "11-1 Before" and "11-1 After" separately but sums them)
        chapter_stats[chapter_id] += (d + n)
        total_d += d
        total_n += n

    # --- OUTPUT ---
    
    # 1. Chapter Breakdown
    print(f"{'CHAPTER':<15} | {'COUNT':>8}")
    print("-" * 26)
    # We iterate directly to preserve file order (insertion order)
    for chap, count in chapter_stats.items():
        print(f"{chap:<15} | {count:>8}")
    print("-" * 26)
    print()

    # 2. Grand Totals
    print("-" * 30)
    print(f"Dialogue (Talk):   {total_d:>6}")
    print(f"Narration (Prose): {total_n:>6}")
    print("-" * 30)
    print(f"TOTAL STORY HANZI: {total_d + total_n:>6}")
    print("-" * 30)

if __name__ == "__main__":
    main()
