#!/usr/bin/env python3
"""
Google Docs Reader Tool

A flexible CLI tool to read Google Docs content from .gdoc files and output
in various formats (markdown, plain text, JSON) or save to files.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class GdocReader:
    """Main class for reading and processing Google Docs files."""

    def __init__(self, gdoc_path: str):
        """Initialize reader with path to .gdoc file."""
        self.gdoc_path = Path(gdoc_path)
        self.gdoc_data: Optional[Dict[str, Any]] = None
        self.doc_id: Optional[str] = None

    def parse_gdoc_file(self) -> Dict[str, Any]:
        """Parse the .gdoc file and extract metadata."""
        if not self.gdoc_path.exists():
            raise FileNotFoundError(f"File not found: {self.gdoc_path}")

        if not self.gdoc_path.suffix == '.gdoc':
            raise ValueError(f"Not a .gdoc file: {self.gdoc_path}")

        with open(self.gdoc_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            self.gdoc_data = json.loads(content)

        # Extract doc_id (could be 'doc_id' or extracted from 'url')
        if 'doc_id' in self.gdoc_data:
            self.doc_id = self.gdoc_data['doc_id']
        elif 'url' in self.gdoc_data:
            # Extract from URL if present
            url = self.gdoc_data['url']
            if '/d/' in url:
                self.doc_id = url.split('/d/')[1].split('/')[0]

        if not self.doc_id:
            raise ValueError("Could not find document ID in .gdoc file")

        return self.gdoc_data

    def get_doc_url(self) -> str:
        """Get the full URL to the Google Doc."""
        if not self.doc_id:
            raise ValueError("Document ID not found. Call parse_gdoc_file() first.")
        return f"https://docs.google.com/document/d/{self.doc_id}/edit"

    def get_export_url(self, format: str = 'txt') -> str:
        """Get the export URL for the document in specified format."""
        if not self.doc_id:
            raise ValueError("Document ID not found. Call parse_gdoc_file() first.")
        # Available formats: txt, html, pdf, docx, odt, rtf, epub, zip (for html with images)
        return f"https://docs.google.com/document/d/{self.doc_id}/export?format={format}"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Read and process Google Docs from .gdoc files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.gdoc --info
  %(prog)s document.gdoc --url
  %(prog)s document.gdoc --fetch --format markdown
  %(prog)s document.gdoc --fetch --output output.md
  %(prog)s document.gdoc --fetch --summarize
        """
    )

    parser.add_argument('gdoc_file', help='Path to .gdoc file')

    # Output options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('--info', action='store_true',
                            help='Show metadata from .gdoc file')
    output_group.add_argument('--url', action='store_true',
                            help='Print the Google Docs URL')
    output_group.add_argument('--fetch', action='store_true',
                            help='Fetch document content (requires auth)')

    # Fetch options
    parser.add_argument('--format', choices=['markdown', 'text', 'html', 'json'],
                       default='markdown',
                       help='Output format (default: markdown)')
    parser.add_argument('--output', '-o', metavar='FILE',
                       help='Save to file instead of stdout')
    parser.add_argument('--summarize', action='store_true',
                       help='Summarize content instead of full output')

    # API options
    parser.add_argument('--credentials', metavar='FILE',
                       default='credentials.json',
                       help='Path to Google API credentials file')
    parser.add_argument('--export', action='store_true',
                       help='Use export URL (no auth) instead of API (limited formats)')

    args = parser.parse_args()

    try:
        reader = GdocReader(args.gdoc_file)
        reader.parse_gdoc_file()

        # Handle different commands
        if args.info:
            print(json.dumps(reader.gdoc_data, indent=2))
        elif args.url:
            print(reader.get_doc_url())
        elif args.fetch:
            # Import here to avoid requiring dependencies for simple operations
            from gdoc_fetcher import fetch_document_content

            content = fetch_document_content(
                reader.doc_id,
                credentials_path=args.credentials,
                use_export=args.export,
                output_format=args.format
            )

            if args.summarize:
                from gdoc_processor import summarize_content
                content = summarize_content(content)

            if args.output:
                output_path = Path(args.output)
                output_path.write_text(content, encoding='utf-8')
                print(f"Content saved to: {output_path}", file=sys.stderr)
            else:
                print(content)
        else:
            # Default: show info
            print(json.dumps(reader.gdoc_data, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
