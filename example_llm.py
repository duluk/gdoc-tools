#!/usr/bin/env python3
"""
Example script demonstrating Google Gemini LLM integration with gdoc reader.

This shows how to:
1. Read a Google Doc
2. Send its content to Gemini for analysis
3. Use different types of LLM operations
"""

import sys
from pathlib import Path
from gdoc_reader import GdocReader
from gdoc_fetcher import fetch_document_content
from gdoc_llm import send_prompt, analyze_document, chat_conversation, configure_gemini


def example_basic_prompt():
    """Example: Send a simple prompt to Gemini."""
    print("=== Basic Prompt Example ===")
    configure_gemini()  # Uses GEMINI_API_KEY from environment

    response = send_prompt(
        "Explain what Google Docs is in one sentence.",
        temperature=0.7
    )
    print(f"Response: {response}\n")


def example_document_summary(gdoc_file: str):
    """Example: Summarize a Google Doc using Gemini."""
    print("=== Document Summary Example ===")

    # Read the .gdoc file
    reader = GdocReader(gdoc_file)
    reader.parse_gdoc_file()

    # Fetch the document content
    content = fetch_document_content(
        reader.doc_id,
        output_format='text'
    )

    print(f"Document length: {len(content)} characters")

    # Analyze with Gemini
    summary = analyze_document(
        document_content=content,
        analysis_type="summary"
    )

    print(f"Summary:\n{summary}\n")


def example_document_key_points(gdoc_file: str):
    """Example: Extract key points from a Google Doc."""
    print("=== Key Points Extraction Example ===")

    reader = GdocReader(gdoc_file)
    reader.parse_gdoc_file()

    content = fetch_document_content(
        reader.doc_id,
        output_format='text'
    )

    key_points = analyze_document(
        document_content=content,
        analysis_type="key_points"
    )

    print(f"Key Points:\n{key_points}\n")


def example_custom_analysis(gdoc_file: str):
    """Example: Custom analysis with a specific prompt."""
    print("=== Custom Analysis Example ===")

    reader = GdocReader(gdoc_file)
    reader.parse_gdoc_file()

    content = fetch_document_content(
        reader.doc_id,
        output_format='text'
    )

    # Custom analysis: identify action items
    analysis = analyze_document(
        document_content=content,
        analysis_type="custom",
        custom_prompt="Identify all action items, tasks, or to-do items mentioned in this document. List them as bullet points."
    )

    print(f"Action Items:\n{analysis}\n")


def example_chat():
    """Example: Multi-turn conversation with Gemini."""
    print("=== Chat Conversation Example ===")
    configure_gemini()

    messages = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "model", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What is its population?"}
    ]

    response = chat_conversation(messages, temperature=0.5)
    print(f"Chat response: {response}\n")


def example_document_qa(gdoc_file: str):
    """Example: Question-answering about a document."""
    print("=== Document Q&A Example ===")

    reader = GdocReader(gdoc_file)
    reader.parse_gdoc_file()

    content = fetch_document_content(
        reader.doc_id,
        output_format='text'
    )

    # Ask a question about the document
    question = "What are the main topics discussed in this document?"
    prompt = f"""Based on the following document, answer this question: {question}

Document:
{content}

Answer:"""

    answer = send_prompt(prompt, temperature=0.3)
    print(f"Question: {question}")
    print(f"Answer: {answer}\n")


def main():
    """Run examples."""
    if len(sys.argv) < 2:
        print("Usage: python example_llm.py <command> [gdoc_file]")
        print("\nCommands:")
        print("  basic              - Basic prompt example (no file needed)")
        print("  summary <file>     - Summarize a Google Doc")
        print("  keypoints <file>   - Extract key points from a doc")
        print("  custom <file>      - Custom analysis (action items)")
        print("  chat               - Chat conversation example (no file needed)")
        print("  qa <file>          - Question-answering about a doc")
        print("\nSetup:")
        print("  1. Set GEMINI_API_KEY environment variable")
        print("  2. For doc commands, ensure you have credentials.json for Google Docs API")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "basic":
            example_basic_prompt()
        elif command == "chat":
            example_chat()
        elif len(sys.argv) < 3:
            print(f"Error: {command} command requires a .gdoc file")
            sys.exit(1)
        else:
            gdoc_file = sys.argv[2]
            if not Path(gdoc_file).exists():
                print(f"Error: File not found: {gdoc_file}")
                sys.exit(1)

            if command == "summary":
                example_document_summary(gdoc_file)
            elif command == "keypoints":
                example_document_key_points(gdoc_file)
            elif command == "custom":
                example_custom_analysis(gdoc_file)
            elif command == "qa":
                example_document_qa(gdoc_file)
            else:
                print(f"Unknown command: {command}")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
