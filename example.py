#!/usr/bin/env python3
"""
Example script showing how to use gdoc_reader as a library
"""

from gdoc_reader import GdocReader
from gdoc_processor import summarize_content, extract_headings, get_word_count

def example_basic_info():
    """Example: Get basic info from a .gdoc file"""
    print("Example 1: Basic Info\n" + "="*50)

    reader = GdocReader("An Essay Concerning the Word of the Perfect Person: A Hermeneutic of TPR.gdoc")
    metadata = reader.parse_gdoc_file()

    print(f"Document ID: {reader.doc_id}")
    print(f"User Email: {metadata.get('email')}")
    print(f"Google Docs URL: {reader.get_doc_url()}")
    print()

def example_with_api():
    """Example: Fetch content using API (requires credentials)"""
    print("Example 2: Fetch with API\n" + "="*50)

    try:
        from gdoc_fetcher import fetch_document_content

        reader = GdocReader("An Essay Concerning the Word of the Perfect Person: A Hermeneutic of TPR.gdoc")
        reader.parse_gdoc_file()

        # Fetch as markdown
        content = fetch_document_content(
            reader.doc_id,
            credentials_path='credentials.json',
            output_format='markdown'
        )

        # Process the content
        headings = extract_headings(content)
        word_count = get_word_count(content)

        print(f"Fetched document successfully!")
        print(f"Word count: {word_count}")
        print(f"Number of headings: {len(headings)}")
        print(f"\nFirst 500 characters:\n{content[:500]}...")
        print()

    except FileNotFoundError as e:
        print(f"Note: {e}")
        print("You'll need to set up credentials.json to use the API.")
        print()

def example_batch_processing():
    """Example: Process multiple .gdoc files"""
    print("Example 3: Batch Processing\n" + "="*50)

    import glob
    from pathlib import Path

    # Find all .gdoc files
    gdoc_files = glob.glob("*.gdoc")

    if not gdoc_files:
        print("No .gdoc files found in current directory")
        return

    print(f"Found {len(gdoc_files)} .gdoc file(s):\n")

    for gdoc_file in gdoc_files:
        try:
            reader = GdocReader(gdoc_file)
            reader.parse_gdoc_file()

            filename = Path(gdoc_file).name
            print(f"📄 {filename}")
            print(f"   ID: {reader.doc_id}")
            print(f"   URL: {reader.get_doc_url()}")
            print()
        except Exception as e:
            print(f"❌ Error processing {gdoc_file}: {e}\n")

def main():
    print("\nGoogle Docs Reader - Usage Examples\n")
    print("="*70 + "\n")

    # Run examples
    example_basic_info()
    example_batch_processing()

    # API example requires credentials
    # example_with_api()

    print("\nFor more examples, see README.md and QUICKSTART.md")

if __name__ == '__main__':
    main()
