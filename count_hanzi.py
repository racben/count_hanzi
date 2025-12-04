import sys
import re

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

def process_file(content):
    dialogue_count = 0
    narration_count = 0
    
    # --- PHASE 1: Extract Dialogue (The "td-text" cells) ---
    # We use Regex with DOTALL so it captures newlines inside the HTML tags.
    # This specifically targets the speech text column, ignoring the speaker name column.
    dialogue_pattern = re.compile(r'<td class="td-text"[^>]*>(.*?)</td>', re.DOTALL)
    
    dialogue_matches = dialogue_matches = dialogue_pattern.findall(content)
    for match in dialogue_matches:
        clean_text = clean_html_tags(match)
        dialogue_count += count_hanzi(clean_text)

    # --- PHASE 2: Remove Tables to isolate Narration ---
    # Now that we've counted dialogue, we strip the ENTIRE HTML table out.
    # This ensures we don't double count, and we automatically kill Speaker Names (td-name).
    content_without_tables = re.sub(r'<table.*?</table>', '', content, flags=re.DOTALL)

    # --- PHASE 3: Process Narration (What's left) ---
    lines = content_without_tables.splitlines()
    for line in lines:
        s = line.strip()
        
        # SKIP: Empty lines
        if not s: continue
        
        # SKIP: YAML Frontmatter (--- title: ...)
        if s.startswith('---') or s.startswith('title:') or s.startswith('author:') or s.startswith('lang:'):
            continue

        # SKIP: Markdown Headers (Generalized Chapter detection)
        # Ignores "# 11-1", "## H9-4", "### 12-3", etc.
        if s.startswith('#'):
            continue
            
        # SKIP: Images (![](...))
        if s.startswith('!['):
            continue
            
        # SKIP: System/Asset Codes & Metadata
        # Detects lines like "27_g11_lentinobleroom", "avg_npc_408", "main_11", "[]{#p1...}"
        if re.match(r'^[a-zA-Z0-9_#\$\{\}\[\]\.]+$', s):
            continue
        
        # SKIP: Specific Game Data headers
        if s.startswith('Script Version') or s.startswith('Game data'):
            continue
            
        # SKIP: Game Logic (Options/Medal descriptions)
        if s.startswith(':::') or s.startswith('medal_'):
            continue

        # Whatever is left is likely Narration (Story text not in a dialogue box)
        narration_count += count_hanzi(s)

    return dialogue_count, narration_count

def main():
    if len(sys.argv) < 2:
        # Defaults to stdin if no file passed
        content = sys.stdin.read()
    else:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    d_count, n_count = process_file(content)
    
    print("-" * 30)
    print(f"Dialogue (Talk):   {d_count:>6}")
    print(f"Narration (Prose): {n_count:>6}")
    print("-" * 30)
    print(f"TOTAL STORY HANZI: {d_count + n_count:>6}")
    print("-" * 30)

if __name__ == "__main__":
    main()
