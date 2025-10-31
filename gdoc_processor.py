"""
Google Docs Processor Module

Handles post-processing of document content like summarization.
"""

import re
from typing import List


def summarize_content(content: str, max_length: int = 500) -> str:
    """
    Create a summary of the document content.

    This is a simple extractive summary that:
    1. Extracts the title and headings
    2. Gets the first paragraph
    3. Counts words and lines
    4. Extracts key sections

    For more advanced summarization, consider integrating an AI model.
    """
    lines = content.split('\n')
    summary_parts = []

    # Extract title (first H1)
    title = None
    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            title = line.replace('# ', '').strip()
            break

    if title:
        summary_parts.append(f"# {title}\n")

    # Extract headings structure
    headings = []
    for line in lines:
        if re.match(r'^#{1,6} ', line):
            headings.append(line.strip())

    if headings:
        summary_parts.append("\n## Document Structure\n")
        for heading in headings[:10]:  # First 10 headings
            summary_parts.append(heading + '\n')

    # Get first substantive paragraph
    first_para = None
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and len(stripped) > 50:
            first_para = stripped
            break

    if first_para:
        summary_parts.append("\n## Opening\n")
        summary_parts.append(first_para[:300] + ('...' if len(first_para) > 300 else '') + '\n')

    # Document statistics
    word_count = len(content.split())
    line_count = len([l for l in lines if l.strip()])
    char_count = len(content)

    summary_parts.append("\n## Statistics\n")
    summary_parts.append(f"- Words: {word_count}\n")
    summary_parts.append(f"- Lines: {line_count}\n")
    summary_parts.append(f"- Characters: {char_count}\n")
    summary_parts.append(f"- Headings: {len(headings)}\n")

    return ''.join(summary_parts)


def extract_headings(content: str) -> List[str]:
    """Extract all headings from markdown content."""
    lines = content.split('\n')
    headings = []
    for line in lines:
        if re.match(r'^#{1,6} ', line):
            headings.append(line.strip())
    return headings


def extract_links(content: str) -> List[tuple]:
    """Extract all links from markdown content."""
    # Matches [text](url) format
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    matches = re.findall(pattern, content)
    return matches


def get_word_count(content: str) -> int:
    """Get word count of content."""
    return len(content.split())


def get_reading_time(content: str, words_per_minute: int = 200) -> int:
    """Estimate reading time in minutes."""
    word_count = get_word_count(content)
    return max(1, word_count // words_per_minute)
