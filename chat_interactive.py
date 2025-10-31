#!/usr/bin/env python3
"""
Interactive Chat Interface for Google Docs

An interactive CLI chatbot with two-tier architecture:
1. Lightweight index for overview queries (all files, minimal content)
2. Full content cache for deep queries (selective loading)
"""

import sys
import os
import readline  # Enables Emacs-style line editing and history
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from gdoc_reader import GdocReader
from gdoc_fetcher import fetch_document_content
from gdoc_llm import send_prompt, configure_gemini


class DocumentIndex:
    """Lightweight index of all documents for fast overview queries."""

    def __init__(self, search_directory: str = ".", credentials_path: str = "credentials.json"):
        """Initialize the document index."""
        self.search_directory = Path(search_directory)
        self.index: Dict[str, Dict] = {}  # filename -> {doc_id, preview, summary, size}
        self.credentials_path = credentials_path

    def find_gdoc_files(self) -> List[Path]:
        """Find all .gdoc files in the search directory."""
        return sorted(self.search_directory.glob("*.gdoc"))

    def build_index(self) -> int:
        """
        Build lightweight index of all documents.

        Returns:
            Number of successfully indexed documents
        """
        gdoc_files = self.find_gdoc_files()

        if not gdoc_files:
            print(f"No .gdoc files found in {self.search_directory}")
            return 0

        print(f"Building index of {len(gdoc_files)} document(s)...")
        success_count = 0

        for gdoc_path in gdoc_files:
            if self._index_document(gdoc_path):
                success_count += 1

        # Generate AI summaries for the index
        if success_count > 0:
            print(f"\nGenerating AI summaries for {success_count} documents...")
            self._generate_summaries()

        return success_count

    def _index_document(self, gdoc_path: Path) -> bool:
        """
        Index a single document (fetch preview only).

        Args:
            gdoc_path: Path to the .gdoc file

        Returns:
            True if successfully indexed
        """
        try:
            filename = gdoc_path.name

            # Skip if already indexed
            if filename in self.index:
                return True

            print(f"  Indexing {filename[:60]}...", end=" ", flush=True)

            # Parse the .gdoc file
            reader = GdocReader(str(gdoc_path))
            reader.parse_gdoc_file()

            # Fetch full content (we need it for preview)
            content = fetch_document_content(
                reader.doc_id,
                credentials_path=self.credentials_path,
                output_format='text'
            )

            # Create preview (first 1000 chars)
            preview = content[:1000] + ("..." if len(content) > 1000 else "")

            # Store in index
            self.index[filename] = {
                'doc_id': reader.doc_id,
                'preview': preview,
                'full_size': len(content),
                'path': str(gdoc_path),
                'summary': None,  # Will be generated later
                'full_content': content  # Keep for later summary generation
            }

            print(f"✓ ({len(content)} chars)")
            return True

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def _generate_summaries(self) -> None:
        """Generate AI summaries for all indexed documents."""
        configure_gemini()

        for i, (filename, doc_data) in enumerate(self.index.items(), 1):
            if doc_data['summary'] is not None:
                continue  # Already has summary

            try:
                print(f"  [{i}/{len(self.index)}] Summarizing {filename[:50]}...", end=" ", flush=True)

                # Use full content for summary
                content = doc_data['full_content']

                # Generate 2-3 sentence summary
                prompt = f"""Provide a concise 2-3 sentence summary of this document's main topic and purpose:

{content[:5000]}

Summary:"""

                summary = send_prompt(
                    prompt=prompt,
                    temperature=0.3,
                    model_name="gemini-2.5-flash"
                )

                doc_data['summary'] = summary.strip()
                print("✓")

            except Exception as e:
                print(f"✗ ({e})")
                doc_data['summary'] = "[Summary generation failed]"

        # Clean up full_content to save memory
        for doc_data in self.index.values():
            if 'full_content' in doc_data:
                del doc_data['full_content']

    def get_index_context(self) -> str:
        """
        Get formatted index for LLM context.

        Returns:
            Formatted string with document index
        """
        if not self.index:
            return "No documents indexed."

        lines = ["=== DOCUMENT INDEX ===\n"]
        for i, (filename, doc_data) in enumerate(self.index.items(), 1):
            lines.append(f"{i}. {filename}")
            lines.append(f"   Size: {doc_data['full_size']} characters")
            if doc_data['summary']:
                lines.append(f"   Summary: {doc_data['summary']}")
            lines.append(f"   Preview: {doc_data['preview'][:200]}...")
            lines.append("")

        return "\n".join(lines)

    def search_by_keywords(self, keywords: str) -> List[Tuple[int, str]]:
        """
        Search index by keywords in filename or summary.

        Returns:
            List of (index, filename) tuples
        """
        keywords_lower = keywords.lower()
        results = []

        for i, (filename, doc_data) in enumerate(self.index.items(), 1):
            searchable = f"{filename} {doc_data.get('summary', '')}".lower()
            if keywords_lower in searchable:
                results.append((i, filename))

        return results

    def get_filename_by_index(self, index: int) -> Optional[str]:
        """Get filename by its index number (1-based)."""
        if 1 <= index <= len(self.index):
            return list(self.index.keys())[index - 1]
        return None

    def list_all(self) -> None:
        """Print list of all indexed documents."""
        if not self.index:
            print("No documents indexed.")
            return

        print(f"\nIndexed documents ({len(self.index)}):")
        for i, (filename, doc_data) in enumerate(self.index.items(), 1):
            size_kb = doc_data['full_size'] / 1024
            print(f"  {i}. {filename} ({size_kb:.1f} KB)")
            if doc_data['summary']:
                print(f"      {doc_data['summary'][:100]}...")


class DocumentCache:
    """Full content cache for deep queries (selective loading)."""

    def __init__(self, search_directory: str = ".", credentials_path: str = "credentials.json"):
        """Initialize the full content cache."""
        self.search_directory = Path(search_directory)
        self.loaded_docs: Dict[str, Dict] = {}  # filename -> {doc_id, content, size}
        self.credentials_path = credentials_path

    def load_document(self, gdoc_path: Path) -> bool:
        """
        Load full content of a document.

        Args:
            gdoc_path: Path to the .gdoc file

        Returns:
            True if successfully loaded
        """
        try:
            filename = gdoc_path.name

            # Skip if already loaded
            if filename in self.loaded_docs:
                return True

            print(f"  Loading full content: {filename[:60]}...", end=" ", flush=True)

            # Parse the .gdoc file
            reader = GdocReader(str(gdoc_path))
            reader.parse_gdoc_file()

            # Fetch full content
            content = fetch_document_content(
                reader.doc_id,
                credentials_path=self.credentials_path,
                output_format='text'
            )

            # Cache it
            self.loaded_docs[filename] = {
                'doc_id': reader.doc_id,
                'content': content,
                'path': str(gdoc_path),
                'size': len(content)
            }

            print(f"✓ ({len(content)} chars)")
            return True

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_full_context(self) -> str:
        """
        Get full content of all loaded documents.

        Returns:
            Formatted string with full document contents
        """
        if not self.loaded_docs:
            return "[No documents fully loaded]"

        context_parts = []
        for filename, doc_data in self.loaded_docs.items():
            context_parts.append(f"=== {filename} ===\n{doc_data['content']}\n")

        return "\n".join(context_parts)

    def list_loaded(self) -> None:
        """Print list of fully loaded documents."""
        if not self.loaded_docs:
            print("No documents fully loaded.")
            return

        print(f"\nFully loaded documents ({len(self.loaded_docs)}):")
        for filename, doc_data in self.loaded_docs.items():
            size_kb = doc_data['size'] / 1024
            print(f"  • {filename} ({size_kb:.1f} KB)")

    def clear(self) -> None:
        """Clear all loaded documents."""
        self.loaded_docs.clear()

    def get_summary(self) -> str:
        """Get summary for display in prompt."""
        return f"{len(self.loaded_docs)} loaded" if self.loaded_docs else "none loaded"


class InteractiveChatbot:
    """Interactive chatbot with two-tier architecture."""

    def __init__(self, search_directory: str = ".", credentials_path: str = "credentials.json"):
        """Initialize the chatbot."""
        self.search_directory = search_directory
        self.credentials_path = credentials_path
        self.index = DocumentIndex(search_directory, credentials_path)
        self.cache = DocumentCache(search_directory, credentials_path)
        self.conversation_history: List[Dict[str, str]] = []
        self.running = True

        # Configure readline for better input experience
        self._setup_readline()

        # Configure Gemini
        try:
            configure_gemini()
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    def _setup_readline(self) -> None:
        """Setup readline for Emacs-style editing and command history."""
        # Set up history file
        history_file = Path.home() / ".gdoc_chat_history"
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass  # First run, no history yet

        # Set maximum history size
        readline.set_history_length(1000)

        # Save history on exit
        import atexit
        atexit.register(readline.write_history_file, history_file)

        # Enable tab completion for commands
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")

        # Emacs mode is default, but set it explicitly
        readline.parse_and_bind("set editing-mode emacs")

        # Add Ctrl-P/Ctrl-N for history navigation (in addition to arrow keys)
        readline.parse_and_bind("Control-p: previous-history")
        readline.parse_and_bind("Control-n: next-history")

    def _completer(self, text: str, state: int) -> Optional[str]:
        """Tab completion for commands."""
        commands = [
            '/index', '/search', '/load', '/active', '/unload',
            '/history', '/help', '/exit', '/quit'
        ]

        options = [cmd for cmd in commands if cmd.startswith(text)]

        if state < len(options):
            return options[state]
        return None

    def print_help(self) -> None:
        """Print help message."""
        print("""
Available commands:
  /index             - Show the document index
  /search <keywords> - Search for documents by keywords
  /load <numbers>    - Load full content of documents (e.g., /load 1,3,5)
  /load all          - Load all documents (warning: may be large!)
  /active            - Show which documents are fully loaded
  /unload            - Unload all full documents (keep index)
  /history           - Show conversation history
  /help              - Show this help message
  /exit or /quit     - Exit the chatbot

Query modes:
  - Overview queries use the lightweight index (all docs)
  - Detailed queries use fully loaded documents
  - The bot will prompt you to load documents when needed
""")

    def handle_command(self, command: str) -> None:
        """Handle special commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd in ["/exit", "/quit"]:
            self.running = False
            print("Goodbye!")

        elif cmd == "/help":
            self.print_help()

        elif cmd == "/index":
            self.index.list_all()

        elif cmd == "/active":
            self.cache.list_loaded()

        elif cmd == "/unload":
            self.cache.clear()
            print("Unloaded all full documents. Index remains.")

        elif cmd == "/history":
            if not self.conversation_history:
                print("No conversation history.")
            else:
                print("\nConversation history:")
                for i, msg in enumerate(self.conversation_history, 1):
                    role = msg['role'].capitalize()
                    content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                    print(f"  {i}. [{role}] {content}")

        elif cmd == "/search":
            if len(parts) < 2:
                print("Usage: /search <keywords>")
                return

            keywords = parts[1]
            results = self.index.search_by_keywords(keywords)

            if not results:
                print(f"No documents found matching '{keywords}'")
            else:
                print(f"\nFound {len(results)} document(s) matching '{keywords}':")
                for idx, filename in results:
                    print(f"  {idx}. {filename}")
                print("\nUse /load <numbers> to load full content")

        elif cmd == "/load":
            if len(parts) < 2:
                print("Usage: /load <numbers>  OR  /load all")
                return

            target = parts[1]

            if target == "all":
                # Confirm first
                total = len(self.index.index)
                print(f"Warning: This will load {total} documents. Continue? (y/n): ", end="", flush=True)
                response = input().strip().lower()
                if response != 'y':
                    print("Cancelled.")
                    return

                # Load all
                for i, filename in enumerate(self.index.index.keys(), 1):
                    gdoc_path = Path(self.index.index[filename]['path'])
                    self.cache.load_document(gdoc_path)

                print(f"\nLoaded {len(self.cache.loaded_docs)} document(s).")
            else:
                # Parse numbers (e.g., "1,3,5" or "1-3")
                indices = self._parse_number_list(target)
                if not indices:
                    print("Invalid format. Use: /load 1,3,5  or  /load 1-3")
                    return

                loaded_count = 0
                for idx in indices:
                    filename = self.index.get_filename_by_index(idx)
                    if filename:
                        gdoc_path = Path(self.index.index[filename]['path'])
                        if self.cache.load_document(gdoc_path):
                            loaded_count += 1
                    else:
                        print(f"  Invalid index: {idx}")

                print(f"\nLoaded {loaded_count} document(s).")

        else:
            print(f"Unknown command: {cmd}")
            print("Type /help for available commands.")

    def _parse_number_list(self, text: str) -> List[int]:
        """Parse number list like '1,3,5' or '1-3' into list of integers."""
        indices = []
        try:
            for part in text.split(','):
                part = part.strip()
                if '-' in part:
                    # Range like "1-3"
                    start, end = part.split('-')
                    indices.extend(range(int(start), int(end) + 1))
                else:
                    # Single number
                    indices.append(int(part))
            return indices
        except:
            return []

    def ask_question(self, question: str) -> None:
        """Ask a question using appropriate context."""
        if not self.index.index:
            print("No documents indexed. Something went wrong during initialization.")
            return

        # Determine if this is an overview query or deep query
        overview_keywords = ['which', 'what', 'how many', 'list', 'organize', 'categorize', 'topics', 'all']
        is_overview = any(keyword in question.lower() for keyword in overview_keywords)

        # Build context
        if self.cache.loaded_docs:
            # Has loaded documents - use them
            context_type = "FULLY LOADED DOCUMENTS"
            context = self.cache.get_full_context()
        elif is_overview:
            # Overview query - use index
            context_type = "DOCUMENT INDEX"
            context = self.index.get_index_context()
        else:
            # Deep query but nothing loaded - suggest loading
            print("\nThis seems like a detailed question, but no documents are fully loaded.")
            print("Tip: Use /search to find relevant documents, then /load to load them.")
            print("Or I can try to answer using the document index (less detailed).")
            print("\nProceed with index? (y/n): ", end="", flush=True)

            response = input().strip().lower()
            if response != 'y':
                print("Cancelled. Use /search and /load to load specific documents.")
                return

            context_type = "DOCUMENT INDEX"
            context = self.index.get_index_context()

        # Build prompt
        if self.conversation_history:
            history_text = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in self.conversation_history[-4:]
            ])
            prompt = f"""You are a helpful assistant answering questions about documents.

Previous conversation:
{history_text}

{context_type}:
{context}

User question: {question}

Answer:"""
        else:
            prompt = f"""You are a helpful assistant answering questions about documents.

{context_type}:
{context}

User question: {question}

Answer:"""

        try:
            print("Thinking...", end=" ", flush=True)
            response = send_prompt(
                prompt=prompt,
                temperature=0.7,
                model_name="gemini-2.5-flash"
            )
            print("\r" + " " * 20 + "\r", end="")

            print(f"\n{response}\n")

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "model", "content": response})

        except Exception as e:
            print(f"\nError: {e}\n")

    def run(self) -> None:
        """Run the interactive chat loop."""
        print("=" * 70)
        print("Interactive Google Docs Chatbot - Two-Tier Architecture")
        print("=" * 70)
        print(f"Directory: {Path(self.search_directory).absolute()}")
        print("\nBuilding document index...")

        # Build index
        count = self.index.build_index()
        if count == 0:
            print("\nNo documents found. Exiting.")
            return

        print(f"\n{'='*70}")
        print(f"Ready! {count} document(s) indexed.")
        print("Use /help for commands. Ask overview questions anytime!")
        print("For detailed queries, use /search and /load first.")
        print(f"{'='*70}\n")

        while self.running:
            try:
                # Show prompt with status
                status = self.cache.get_summary()
                user_input = input(f"[{status}] You: ").strip()

                if not user_input:
                    continue

                # Handle commands vs questions
                if user_input.startswith("/"):
                    self.handle_command(user_input)
                else:
                    self.ask_question(user_input)

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type /exit to quit.\n")
                continue
            except EOFError:
                print("\nGoodbye!")
                break


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Interactive chatbot for querying Google Docs (two-tier architecture)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Two-Tier Architecture:
  1. Lightweight index (all docs) - for overview queries
  2. Full content cache (selective) - for detailed queries

Examples:
  %(prog)s                    # Search current directory
  %(prog)s /path/to/docs      # Search specific directory

Setup:
  1. Set GEMINI_API_KEY environment variable
  2. Ensure credentials.json exists for Google Docs API
        """
    )

    parser.add_argument('directory', nargs='?', default='.',
                       help='Directory to search for .gdoc files (default: current)')

    args = parser.parse_args()

    # Validate directory
    if not Path(args.directory).exists():
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)

    # Create and run chatbot
    chatbot = InteractiveChatbot(args.directory)
    chatbot.run()


if __name__ == "__main__":
    main()
