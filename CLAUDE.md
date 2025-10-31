# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool for accessing Google Docs content from `.gdoc` shortcut files created by Google Drive for Desktop. The tool parses these JSON shortcuts, fetches the actual document content via Google Docs API, and converts it to various output formats (Markdown, text, HTML, JSON).

## Architecture

The codebase uses a **four-module architecture** separating concerns:

1. **`gdoc_reader.py`** - CLI interface and orchestration
   - Entry point: `main()` function
   - `GdocReader` class: Parses `.gdoc` files and extracts document IDs
   - Handles argument parsing and coordinates between modules
   - Imports fetcher/processor modules lazily (only when `--fetch` is used)

2. **`gdoc_fetcher.py`** - Google Docs API client and format conversion
   - Two fetch paths: API (requires OAuth) vs. Export URL (public docs only)
   - `get_credentials()`: Handles OAuth2 flow, saves token to `token.pickle`
   - `document_to_markdown()` / `document_to_text()`: Converts Google Docs API response to output formats
   - The API response is a nested dict structure: `body.content[]` contains `paragraph` and `table` elements

3. **`gdoc_processor.py`** - Content post-processing utilities
   - `summarize_content()`: Extractive summary (headings, first paragraph, statistics)
   - Helper functions: `extract_headings()`, `extract_links()`, `get_word_count()`, etc.

4. **`gdoc_llm.py`** - Google Gemini LLM integration (NEW)
   - `configure_gemini()`: Sets up Gemini API with key from environment or parameter
   - `send_prompt()`: Send single prompts to Gemini with configurable temperature and tokens
   - `chat_conversation()`: Multi-turn conversations with message history
   - `analyze_document()`: Pre-built analysis types (summary, key_points, questions, custom)
   - Uses `gemini-2.5-flash` model by default for fast, high-quality responses

### .gdoc File Format

`.gdoc` files are JSON shortcuts with this structure:
```json
{
  "doc_id": "document-id-here",
  "email": "user@example.com",
  "resource_key": ""
}
```

The `doc_id` field is extracted and used to construct API requests or export URLs.

## Common Commands

### Setup
```bash
pip install -r requirements.txt
```

### Testing
```bash
# Run basic tests (no API calls)
python3 test_basic.py

# Test with a .gdoc file (no auth required)
python3 gdoc_reader.py "file.gdoc" --info
python3 gdoc_reader.py "file.gdoc" --url
```

### Development Usage
```bash
# Fetch content (requires credentials.json from Google Cloud Console)
python3 gdoc_reader.py "file.gdoc" --fetch --format markdown
python3 gdoc_reader.py "file.gdoc" --fetch --format text
python3 gdoc_reader.py "file.gdoc" --fetch --format json

# Save output to file
python3 gdoc_reader.py "file.gdoc" --fetch --output output.md

# Get summary instead of full content
python3 gdoc_reader.py "file.gdoc" --fetch --summarize

# For public docs only (no authentication)
python3 gdoc_reader.py "file.gdoc" --fetch --export --format text

# Interactive chatbot for querying documents
python3 chat_interactive.py                    # Search current directory
python3 chat_interactive.py /path/to/docs      # Search specific directory
```

## Authentication Setup

### Google Docs API (for fetching documents)

For `--fetch` without `--export`:
1. Go to Google Cloud Console
2. Enable Google Docs API
3. Create OAuth 2.0 Desktop credentials
4. Download as `credentials.json` in project directory
5. First run opens browser for OAuth flow, saves `token.pickle` for future use
6. Scope used: `https://www.googleapis.com/auth/documents.readonly`

### Google Gemini API (for LLM features)

For using `gdoc_llm.py` module:
1. Go to Google AI Studio (https://aistudio.google.com/apikey)
2. Create an API key
3. Set environment variable: `export GEMINI_API_KEY='your-api-key-here'`
4. Alternatively, pass `api_key` parameter to LLM functions

Example usage:
```bash
# Set API key in environment
export GEMINI_API_KEY='your-key-here'

# Run LLM examples
python3 example_llm.py basic
python3 example_llm.py summary "document.gdoc"
python3 example_llm.py keypoints "document.gdoc"

# Start interactive chatbot
python3 chat_interactive.py
```

### Interactive Chatbot Usage

The `chat_interactive.py` script provides an interactive session with **two-tier architecture**:

**Two-Tier Architecture:**
1. **Lightweight Index** (Tier 1) - Automatically built on startup
   - Indexes ALL documents in the directory
   - Fetches each document once to create:
     - First 1000 characters as preview
     - AI-generated 2-3 sentence summary
   - Used for overview queries: "Which docs discuss X?", "How would you organize these?", "What topics are covered?"

2. **Full Content Cache** (Tier 2) - Selectively loaded on demand
   - Load specific documents when you need detailed analysis
   - Use `/search` to find relevant docs, then `/load` to fully load them
   - Loaded documents are kept in memory for the session

**Benefits:**
- Efficient: Don't blow through context limits with huge document sets
- Fast: Index lets you explore/search all docs without full loading
- Flexible: Load only what you need for detailed queries

**Commands:**
- `/index` - Show all indexed documents with summaries
- `/search <keywords>` - Search for documents by keywords (filename/summary)
- `/load <numbers>` - Load full content (e.g., `/load 1,3,5` or `/load 1-3`)
- `/load all` - Load all documents (prompts for confirmation)
- `/active` - Show which documents are fully loaded
- `/unload` - Unload full documents (keeps index)
- `/history` - Show conversation history
- `/help` - Show help message
- `/exit` or `/quit` - Exit the chatbot

**Example session:**
```
$ python3 chat_interactive.py ~/Documents/theology
Building document index...
  Indexing Divine Intent and Human Hands.gdoc... ✓ (105195 chars)
  Indexing The Perfect Fellowship.gdoc... ✓ (219197 chars)
  [... 36 more files ...]

Generating AI summaries for 38 documents...
  [1/38] Summarizing Divine Intent and Human Hands.gdoc... ✓
  [2/38] Summarizing The Perfect Fellowship.gdoc... ✓
  [... continues ...]

Ready! 38 document(s) indexed.
Use /help for commands. Ask overview questions anytime!

[none loaded] You: How would you categorize these documents?

Based on the document index, I would organize these 38 theological works into:
1. Core Framework (5 docs) - Theistic Personalist Realism foundations
2. Doctrine of God (8 docs) - Trinity, attributes, divine action
3. Soteriology (3 docs) - Atonement theories, salvation
4. Ecclesiology (4 docs) - Church, sacraments, practices
...

[none loaded] You: /search atonement

Found 3 document(s) matching 'atonement':
  5. Triune Kenotic Substitution: The Decisive Battle.gdoc
  8. Old - Triune Kenotic Substitution: A Constructive Model.gdoc
  24. Summary of Triune Kenotic Substitution (TKS).gdoc

Use /load <numbers> to load full content

[none loaded] You: /load 5

  Loading full content: Triune Kenotic Substitution...✓ (221068 chars)

Loaded 1 document(s).

[1 loaded] You: Explain the kenotic aspect in detail

[AI provides detailed analysis using full document content]

[1 loaded] You: /exit
Goodbye!
```

## Extension Points

The modular design enables easy feature additions:

- **New output formats**: Add conversion functions in `gdoc_fetcher.py` (e.g., `document_to_html()`)
- **Advanced summarization**: Use `gdoc_llm.py` with `analyze_document()` for AI-powered summarization
- **Batch processing**: Add multi-file loop in `gdoc_reader.py` main() or create new entry point
- **Custom filters**: Add processing functions in `gdoc_processor.py`
- **LLM-powered features**: Use `gdoc_llm.py` for document Q&A, content generation, translation, sentiment analysis, etc.
- **Custom LLM prompts**: Use `send_prompt()` or `analyze_document()` with custom prompts for specialized tasks

## Key Implementation Details

- **Lazy imports**: `gdoc_fetcher` and `gdoc_processor` are imported only when needed, so `--info` and `--url` work without installing Google API dependencies
- **Error handling**: Invalid files, missing credentials, and API errors raise exceptions caught in `main()` and printed to stderr
- **File paths with spaces**: Use quotes when passing `.gdoc` filenames to CLI
- **Token refresh**: OAuth tokens auto-refresh; delete `token.pickle` to force re-authentication
