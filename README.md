# gdoc-tools

CLI tools for accessing and querying Google Docs from `.gdoc` shortcut files created by Google Drive for Desktop.

## Features

- **gdoc** - Read Google Docs content in various formats (Markdown, text, HTML, JSON)
- **gdoc-chat** - Interactive chatbot with two-tier architecture for querying multiple documents
- **gdoc-example** - Example scripts demonstrating LLM integration

## Installation

### Quick Install (Editable Mode - Recommended for Development)

```bash
cd /path/to/gdoc
pip install -e .
```

This installs the package in editable mode, so any changes to the code are immediately reflected.

### Regular Install

```bash
cd /path/to/gdoc
pip install .
```

After installation, the commands `gdoc`, `gdoc-chat`, and `gdoc-example` will be available system-wide.

## Setup

### 1. Google Docs API (for fetching documents)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Docs API
3. Create OAuth 2.0 Desktop credentials
4. Download the credentials file and save it as `credentials.json`

**Recommended location:** `~/.config/gdoc/credentials.json`

```bash
mkdir -p ~/.config/gdoc
mv ~/Downloads/credentials.json ~/.config/gdoc/
```

Alternatively, you can place it in the current directory. The tool searches in this order:
1. `~/.config/gdoc/credentials.json` (recommended)
2. `./credentials.json` (current directory)

On first run, the tool opens a browser for OAuth flow and saves the token to `~/.config/gdoc/token.pickle` for future use.

### 2. Google Gemini API (for chatbot and LLM features)

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create an API key
3. Set environment variable:

```bash
export GEMINI_API_KEY='your-api-key-here'
```

Add to your `~/.bashrc` or `~/.zshrc` to make it permanent.

## Usage

### Basic Document Reading (`gdoc`)

```bash
# Show document info
gdoc document.gdoc --info

# Get document URL
gdoc document.gdoc --url

# Fetch and display as markdown
gdoc document.gdoc --fetch --format markdown

# Save to file
gdoc document.gdoc --fetch --output output.md

# Get AI summary
gdoc document.gdoc --fetch --summarize

# Export without auth (public docs only)
gdoc document.gdoc --fetch --export --format text
```

### Interactive Chatbot (`gdoc-chat`)

```bash
# Start chatbot in current directory
gdoc-chat

# Or specify a directory
gdoc-chat ~/Documents/theology
```

#### Chatbot Features

**Two-Tier Architecture:**
1. **Lightweight Index** - Auto-built on startup, indexes all documents with AI summaries
2. **Full Content Cache** - Selectively load documents for detailed queries

**Commands:**
- `/index` - Show all indexed documents
- `/search <keywords>` - Search for documents
- `/load 1,3,5` - Load specific documents by number
- `/load 1-3` - Load range of documents
- `/load all` - Load all documents (with confirmation)
- `/active` - Show loaded documents
- `/unload` - Clear loaded documents
- `/history` - Show conversation history
- `/help` - Show help
- `/exit` or `/quit` - Exit chatbot

**Keybindings:**
- Emacs-style editing: `Ctrl-A`, `Ctrl-E`, `Ctrl-K`, `Ctrl-W`, etc.
- History navigation: `Ctrl-P` (previous), `Ctrl-N` (next), or arrow keys
- Reverse search: `Ctrl-R`
- Tab completion for commands

### Example Scripts (`gdoc-example`)

```bash
# Basic prompt
gdoc-example basic

# Summarize a document
gdoc-example summary document.gdoc

# Extract key points
gdoc-example keypoints document.gdoc

# Custom analysis
gdoc-example custom document.gdoc

# Q&A about document
gdoc-example qa document.gdoc
```

## Command-Line Options

```
positional arguments:
  gdoc_file             Path to .gdoc file

optional arguments:
  -h, --help            Show help message
  --info                Show metadata from .gdoc file
  --url                 Print the Google Docs URL
  --fetch               Fetch document content (requires auth)
  --format {markdown,text,html,json}
                        Output format (default: markdown)
  --output FILE, -o FILE
                        Save to file instead of stdout
  --summarize           Summarize content instead of full output
  --credentials FILE    Path to Google API credentials file
  --export              Use export URL (no auth) instead of API
```

## File Structure

- `gdoc_reader.py` - Main CLI interface and argument parsing
- `gdoc_fetcher.py` - Google Docs API client and content fetching
- `gdoc_processor.py` - Content processing and summarization
- `requirements.txt` - Python dependencies

## How .gdoc Files Work

`.gdoc` files are JSON shortcuts created by Google Drive for Desktop. They contain:

```json
{
  "doc_id": "document-id-here",
  "email": "user@example.com",
  "resource_key": ""
}
```

The tool parses this file and uses the `doc_id` to fetch the actual document content.

## Authentication Flow

On first run with `--fetch`, the tool will:
1. Open a browser window for Google OAuth authentication
2. Ask you to authorize access to your Google Docs
3. Save the token to `token.pickle` for future use

The token will be automatically refreshed when it expires.

## Extending the Tool

The modular architecture makes it easy to add new features:

- **New output formats**: Add handlers in `gdoc_fetcher.py`
- **Advanced summarization**: Integrate AI models in `gdoc_processor.py`
- **Batch processing**: Add multi-file support in `gdoc_reader.py`
- **Custom filters**: Add content filtering in `gdoc_processor.py`

## Troubleshooting

**"Credentials file not found"**
- Download `credentials.json` from Google Cloud Console

**"HttpError 403: The caller does not have permission"**
- The document may be private and your account doesn't have access
- Try using `--export` for public documents

**"File not found"**
- Ensure the path to your `.gdoc` file is correct
- Use quotes around filenames with spaces

## Examples

Convert a Google Doc to Markdown and save:
```bash
python gdoc_reader.py "My Document.gdoc" --fetch --output document.md
```

Get a quick summary:
```bash
python gdoc_reader.py essay.gdoc --fetch --summarize
```

Open the document in browser:
```bash
open $(python gdoc_reader.py document.gdoc --url)
```

## License

MIT License - feel free to modify and extend as needed.
