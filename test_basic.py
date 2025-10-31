#!/usr/bin/env python3
"""
Basic test script for gdoc_reader functionality
"""

import sys
from pathlib import Path
from gdoc_reader import GdocReader

def test_parse_gdoc():
    """Test parsing a .gdoc file"""
    print("Testing .gdoc file parsing...")

    gdoc_file = "An Essay Concerning the Word of the Perfect Person: A Hermeneutic of TPR.gdoc"

    if not Path(gdoc_file).exists():
        print(f"❌ Test file not found: {gdoc_file}")
        return False

    try:
        reader = GdocReader(gdoc_file)
        data = reader.parse_gdoc_file()

        print(f"✓ Successfully parsed .gdoc file")
        print(f"  - Document ID: {reader.doc_id}")
        print(f"  - Email: {data.get('email', 'N/A')}")
        print(f"  - URL: {reader.get_doc_url()}")
        print(f"  - Export URL (txt): {reader.get_export_url('txt')}")

        return True
    except Exception as e:
        print(f"❌ Failed to parse: {e}")
        return False

def test_processor():
    """Test content processing functions"""
    print("\nTesting content processor...")

    try:
        from gdoc_processor import (
            extract_headings,
            extract_links,
            get_word_count,
            get_reading_time
        )

        sample_content = """
# Main Title

## Section 1

This is some sample content with a [link](https://example.com).

### Subsection

More content here.

## Section 2

Additional text.
"""

        headings = extract_headings(sample_content)
        links = extract_links(sample_content)
        word_count = get_word_count(sample_content)
        reading_time = get_reading_time(sample_content)

        print(f"✓ Processor functions working")
        print(f"  - Headings found: {len(headings)}")
        print(f"  - Links found: {len(links)}")
        print(f"  - Word count: {word_count}")
        print(f"  - Reading time: {reading_time} min")

        return True
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        return False

def main():
    print("Running basic tests for gdoc_reader...\n")

    tests = [
        test_parse_gdoc,
        test_processor,
    ]

    results = [test() for test in tests]

    print(f"\n{'='*50}")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("\n✓ All basic tests passed!")
        print("\nTo fetch content from Google Docs, you'll need to:")
        print("1. Set up credentials.json from Google Cloud Console")
        print("2. Run: python3 gdoc_reader.py '<file>.gdoc' --fetch")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
