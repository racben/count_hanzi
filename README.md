# Arknights Story Counter (Markdown/HTML Version)

## Overview
This script (`count_arknights_md.py`) is designed specifically to parse Arknights story data that has been converted into Markdown format.

The raw story files contain a mix of **Dialogue**, **Metadata**, **Speaker Names**, and **System Codes**. This script uses structure-aware parsing to isolate the actual story content (Dialogue + Narration) while ignoring the rest.

## The Logic
The script processes the file in three phases to ensure accuracy:

### Phase 1: Dialogue Extraction (HTML Parsing)
The Markdown file uses HTML tables for dialogue.
- **Target:** `<td class="td-text">...</td>`
- **Action:** The script extracts text *only* from these cells. This captures the spoken lines.
- **Exclusion:** It intentionally ignores `<td class="td-name">`, so **Speaker Names are NOT counted** toward the total.

### Phase 2: Table Removal
Once dialogue is extracted, the script deletes all HTML tables (`<table>...</table>`) from the memory buffer. This leaves behind only the Narration and Metadata.

### Phase 3: Narration Filtering (Regex)
The script iterates through the remaining lines to count Narration, applying strict filters to ignore metadata:
- **YAML Frontmatter:** Ignores lines starting with `---`, `title:`, etc.
- **Markdown Headers:** Ignores `# Chapter Title` (e.g., `## 11-1`, `## H12-4`).
- **Images:** Ignores `![](...)`.
- **Game Data:** Ignores system codes like `avg_npc_408`, `bg_black`, `choice_1`, etc.

## Usage

```bash
python count_arknights_md.py final.md
