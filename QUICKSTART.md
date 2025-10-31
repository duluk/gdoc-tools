# Quick Start Guide

## Installation

```bash
pip3 install -r requirements.txt
```

## Basic Usage (No Authentication Required)

Show document info:
```bash
python3 gdoc_reader.py "document.gdoc" --info
```

Get the document URL:
```bash
python3 gdoc_reader.py "document.gdoc" --url
```

## Fetching Content (Requires Authentication)

### First Time Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Docs API
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download and save as `credentials.json` in this directory

### Fetch and Display Content

Fetch as Markdown:
```bash
python3 gdoc_reader.py "document.gdoc" --fetch
```

Fetch as plain text:
```bash
python3 gdoc_reader.py "document.gdoc" --fetch --format text
```

Save to file:
```bash
python3 gdoc_reader.py "document.gdoc" --fetch --output document.md
```

Get a summary:
```bash
python3 gdoc_reader.py "document.gdoc" --fetch --summarize
```

## Example with Your File

```bash
# Show info
python3 gdoc_reader.py "An Essay Concerning the Word of the Perfect Person: A Hermeneutic of TPR.gdoc" --info

# Get URL
python3 gdoc_reader.py "An Essay Concerning the Word of the Perfect Person: A Hermeneutic of TPR.gdoc" --url

# Fetch content (after setting up credentials.json)
python3 gdoc_reader.py "An Essay Concerning the Word of the Perfect Person: A Hermeneutic of TPR.gdoc" --fetch --output essay.md
```

## Testing

Run basic tests:
```bash
python3 test_basic.py
```

## Troubleshooting

**"Credentials file not found"**
- You need to download `credentials.json` from Google Cloud Console

**"401 Unauthorized" with --export**
- The document is not public
- Use `--fetch` without `--export` and set up authentication

**"File not found"**
- Use quotes around filenames with spaces
- Check the file path is correct

## Architecture

The tool is modular and extensible:

- `gdoc_reader.py` - Main CLI interface
- `gdoc_fetcher.py` - Google Docs API client
- `gdoc_processor.py` - Content processing
- `test_basic.py` - Basic tests

Add new features by extending these modules!
