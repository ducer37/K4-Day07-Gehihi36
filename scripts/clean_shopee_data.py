#!/usr/bin/env python3
"""Data cleaning script for Shopee public policy documents.

Reads raw Markdown files from data/shopee_full (or data/shopee),
cleans boilerplate UI noise, normalizes spaces and unicode characters,
restructures fragmented lists/tables, and outputs cleaned files to data/shopee_cleaned.
"""

import re
import sys
from pathlib import Path

# Headers / footers to discard
BOILERPLATE_PATTERNS = [
    re.compile(r".*Shopee Trung tâm trợ giúp.*", re.IGNORECASE),
    re.compile(r".*Xin chào, Shopee có thể giúp gì.*", re.IGNORECASE),
    re.compile(r".*Bạn có hài lòng với bài viết này.*", re.IGNORECASE),
    re.compile(r"^Hài lòng$", re.IGNORECASE),
    re.compile(r"^Không hài lòng$", re.IGNORECASE),
    re.compile(r"^Cảm ơn bạn đã gửi ý kiến đánh giá!$", re.IGNORECASE),
    re.compile(r"^Bài viết liên quan$", re.IGNORECASE),
]


def clean_unicode_and_spaces(text: str) -> str:
    """Normalize non-breaking spaces, zero-width spaces, and control characters."""
    # Replace non-breaking space \xa0 and zero-width space \u200b
    text = text.replace("\xa0", " ").replace("\u200b", "")
    # Remove trailing whitespace from each line
    lines = [re.sub(r"[ \t]+$", "", line) for line in text.splitlines()]
    return "\n".join(lines)


def clean_frontmatter_and_body(content: str) -> tuple[str, str]:
    """Separate YAML frontmatter from document body."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = f"---{parts[1]}---\n"
            body = parts[2].strip()
            return frontmatter, body
    return "", content.strip()


def remove_boilerplate_lines(lines: list[str], title: str = "") -> list[str]:
    """Filter out UI search bars, headers, footers, and redundant title repeats."""
    cleaned_lines = []
    h1_found = False

    for line in lines:
        stripped = line.strip()
        
        # Skip matched boilerplate lines
        if any(pattern.match(stripped) for pattern in BOILERPLATE_PATTERNS):
            continue

        # Detect H1 title to avoid duplicate title lines right after header noise
        if stripped.startswith("# "):
            h1_found = True
            cleaned_lines.append(line)
            continue

        # Skip duplicate title right after header if it matches the document title
        if h1_found and title and stripped.lower() == title.lower() and len(cleaned_lines) <= 4:
            continue

        cleaned_lines.append(line)

    return cleaned_lines


def join_broken_lines(lines: list[str]) -> list[str]:
    """Merge lines that were split mid-sentence by inline HTML tag wrappers."""
    joined: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if joined and joined[-1] != "":
                joined.append("")
            continue

        if joined and joined[-1] != "":
            prev = joined[-1]
            # Avoid merging headers, list items, table rows, or lines ending with terminal punctuation
            if not prev.startswith(("#", "-", "|", "*")) and not prev.endswith((".", ":", "!", "?", ";", "—")):
                if stripped.startswith((",", ".", ")", "]", ";")) or stripped[0].islower() or (stripped[0].isdigit() and not re.match(r"^\d+[\.\)]\s*", stripped)):
                    joined[-1] = prev + " " + stripped
                    joined[-1] = re.sub(r"\s+([,.\)])", r"\1", joined[-1])
                    continue
        joined.append(stripped)
    return joined


def format_tables_and_lists(lines: list[str]) -> list[str]:
    """Reformat fragmented lines, table columns, and empty bullet gaps."""
    lines = join_broken_lines(lines)
    formatted = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Collapse empty lines
        if not stripped:
            if formatted and formatted[-1].strip() != "":
                formatted.append("")
            i += 1
            continue

        formatted.append(line)
        i += 1

    return formatted


def clean_document(raw_content: str) -> str:
    """Apply full cleaning pipeline on a raw Markdown document."""
    # Step 1: Normalize unicode and basic space formatting
    content = clean_unicode_and_spaces(raw_content)

    # Step 2: Extract frontmatter and body
    frontmatter, body = clean_frontmatter_and_body(content)

    # Extract title from frontmatter if available
    title_match = re.search(r'^title:\s*"(.*?)"', frontmatter, re.MULTILINE)
    title = title_match.group(1) if title_match else ""

    # Step 3: Split into lines and filter boilerplate
    lines = body.splitlines()
    cleaned_lines = remove_boilerplate_lines(lines, title)

    # Step 4: Reformat lines and remove excessive blank lines
    formatted_lines = format_tables_and_lists(cleaned_lines)

    # Step 5: Final collapse of 3+ newlines to max 2
    cleaned_body = "\n".join(formatted_lines)
    cleaned_body = re.sub(r"\n{3,}", "\n\n", cleaned_body).strip()

    if frontmatter:
        return f"{frontmatter}\n{cleaned_body}\n"
    return f"{cleaned_body}\n"


def process_directory(input_dir: Path, output_dir: Path) -> None:
    """Process all Markdown files in input_dir and write to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(input_dir.glob("*.md"))

    if not md_files:
        print(f"No .md files found in {input_dir}", file=sys.stderr)
        return

    print(f"Processing {len(md_files)} files from {input_dir} -> {output_dir}...")
    success_count = 0

    for file_path in md_files:
        raw_text = file_path.read_text(encoding="utf-8")
        cleaned_text = clean_document(raw_text)

        target_file = output_dir / file_path.name
        target_file.write_text(cleaned_text, encoding="utf-8")
        print(f"  [Cleaned] {file_path.name} -> {target_file.name}")
        success_count += 1

    print(f"\nSuccessfully cleaned {success_count} files in {output_dir}")


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    
    # Check input source: prefer data/shopee_full if exists, else data/shopee
    input_dir = base_dir / "data" / "shopee_full"
    if not input_dir.exists() or not list(input_dir.glob("*.md")):
        input_dir = base_dir / "data" / "shopee"

    output_dir = base_dir / "data" / "shopee_cleaned"

    if not input_dir.exists():
        print(f"Error: Neither data/shopee_full nor data/shopee exists in {base_dir}", file=sys.stderr)
        sys.exit(1)

    process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()
