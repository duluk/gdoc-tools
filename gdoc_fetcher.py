"""
Google Docs Fetcher Module

Handles fetching content from Google Docs using the Google Docs API or export URLs.
"""

import os
import pickle
import requests
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']


def _find_credentials_file(credentials_path: str = 'credentials.json') -> Path:
    """
    Find credentials file by searching in multiple locations.

    Search order:
    1. Exact path if provided (and exists)
    2. ~/.config/gdoc/credentials.json
    3. ./credentials.json (current directory)

    Returns:
        Path to credentials file

    Raises:
        FileNotFoundError: If credentials file not found in any location
    """
    # If a specific path was provided, try it first
    if credentials_path != 'credentials.json':
        cred_path = Path(credentials_path)
        if cred_path.exists():
            return cred_path

    # Try ~/.config/gdoc/credentials.json
    config_path = Path.home() / '.config' / 'gdoc' / 'credentials.json'
    if config_path.exists():
        return config_path

    # Try current directory
    local_path = Path('credentials.json')
    if local_path.exists():
        return local_path

    # Not found anywhere
    raise FileNotFoundError(
        f"Credentials file not found. Searched:\n"
        f"  1. {config_path}\n"
        f"  2. {local_path.absolute()}\n"
        f"\nPlease download credentials.json from Google Cloud Console:\n"
        f"https://console.cloud.google.com/apis/credentials\n"
        f"\nRecommended: Place it in {config_path}"
    )


def get_credentials(credentials_path: str = 'credentials.json') -> Credentials:
    """
    Authenticate and return Google API credentials.

    Uses OAuth2 flow with a credentials.json file downloaded from Google Cloud Console.
    Saves token to ~/.config/gdoc/token.pickle for future use.

    Searches for credentials.json in:
    1. Provided path (if specified)
    2. ~/.config/gdoc/credentials.json (recommended)
    3. ./credentials.json (current directory)
    """
    creds = None

    # Store token in config directory
    config_dir = Path.home() / '.config' / 'gdoc'
    config_dir.mkdir(parents=True, exist_ok=True)
    token_path = config_dir / 'token.pickle'

    # The file token.pickle stores the user's access and refresh tokens
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds_file = _find_credentials_file(credentials_path)
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def fetch_document_via_api(doc_id: str, credentials_path: str) -> dict:
    """
    Fetch document structure via Google Docs API.

    Returns the full document structure as a dictionary.
    """
    creds = get_credentials(credentials_path)

    try:
        service = build('docs', 'v1', credentials=creds)
        document = service.documents().get(documentId=doc_id).execute()
        return document
    except HttpError as error:
        raise Exception(f"An error occurred: {error}")


def fetch_document_via_export(doc_id: str, format: str = 'txt') -> str:
    """
    Fetch document content via export URL (no authentication required for public docs).

    Available formats: txt, html, pdf, docx, odt, rtf, epub
    Note: This only works for publicly accessible documents.
    """
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format={format}"

    response = requests.get(export_url)
    response.raise_for_status()

    if format in ['txt', 'html']:
        return response.text
    else:
        return response.content


def document_to_text(document: dict) -> str:
    """
    Convert Google Docs API document structure to plain text.

    Extracts text content from the document structure.
    """
    content = document.get('body', {}).get('content', [])
    text_parts = []

    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            for elem in paragraph.get('elements', []):
                if 'textRun' in elem:
                    text_parts.append(elem['textRun'].get('content', ''))

        elif 'table' in element:
            table = element['table']
            for row in table.get('tableRows', []):
                for cell in row.get('tableCells', []):
                    for cell_content in cell.get('content', []):
                        if 'paragraph' in cell_content:
                            paragraph = cell_content['paragraph']
                            for elem in paragraph.get('elements', []):
                                if 'textRun' in elem:
                                    text_parts.append(elem['textRun'].get('content', ''))

    return ''.join(text_parts)


def document_to_markdown(document: dict) -> str:
    """
    Convert Google Docs API document structure to Markdown.

    Handles basic formatting: headings, bold, italic, lists, links.
    """
    content = document.get('body', {}).get('content', [])
    markdown_parts = []

    title = document.get('title', '')
    if title:
        markdown_parts.append(f"# {title}\n\n")

    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            paragraph_style = paragraph.get('paragraphStyle', {})
            named_style = paragraph_style.get('namedStyleType', 'NORMAL_TEXT')

            # Collect text with formatting
            text_parts = []
            for elem in paragraph.get('elements', []):
                if 'textRun' in elem:
                    text_run = elem['textRun']
                    text = text_run.get('content', '')
                    text_style = text_run.get('textStyle', {})

                    # Apply inline formatting
                    if text_style.get('bold'):
                        text = f"**{text}**"
                    if text_style.get('italic'):
                        text = f"*{text}*"
                    if 'link' in text_style:
                        url = text_style['link'].get('url', '')
                        text = f"[{text.strip()}]({url})"

                    text_parts.append(text)

            line = ''.join(text_parts)

            # Apply paragraph-level formatting
            if named_style == 'HEADING_1':
                line = f"# {line}"
            elif named_style == 'HEADING_2':
                line = f"## {line}"
            elif named_style == 'HEADING_3':
                line = f"### {line}"
            elif named_style == 'HEADING_4':
                line = f"#### {line}"
            elif named_style == 'HEADING_5':
                line = f"##### {line}"
            elif named_style == 'HEADING_6':
                line = f"###### {line}"

            # Handle bullet points
            bullet = paragraph.get('bullet')
            if bullet:
                nesting_level = bullet.get('nestingLevel', 0)
                indent = '  ' * nesting_level
                line = f"{indent}- {line}"

            markdown_parts.append(line)

        elif 'table' in element:
            # Basic table support
            table = element['table']
            for row in table.get('tableRows', []):
                row_parts = []
                for cell in row.get('tableCells', []):
                    cell_text = []
                    for cell_content in cell.get('content', []):
                        if 'paragraph' in cell_content:
                            paragraph = cell_content['paragraph']
                            for elem in paragraph.get('elements', []):
                                if 'textRun' in elem:
                                    cell_text.append(elem['textRun'].get('content', ''))
                    row_parts.append(''.join(cell_text).strip())
                markdown_parts.append('| ' + ' | '.join(row_parts) + ' |\n')
            markdown_parts.append('\n')

    return ''.join(markdown_parts)


def fetch_document_content(
    doc_id: str,
    credentials_path: str = 'credentials.json',
    use_export: bool = False,
    output_format: str = 'markdown'
) -> str:
    """
    Main function to fetch document content in the specified format.

    Args:
        doc_id: Google Docs document ID
        credentials_path: Path to credentials.json file
        use_export: If True, use export URL (no auth); if False, use API (requires auth)
        output_format: Output format (markdown, text, html, json)

    Returns:
        Document content as a string
    """
    if use_export:
        # Use export URL (no authentication)
        if output_format == 'markdown':
            # Export as HTML then convert to markdown (future enhancement)
            content = fetch_document_via_export(doc_id, 'txt')
            return content
        elif output_format == 'text':
            return fetch_document_via_export(doc_id, 'txt')
        elif output_format == 'html':
            return fetch_document_via_export(doc_id, 'html')
        else:
            raise ValueError(f"Export format '{output_format}' not supported with --export")
    else:
        # Use Google Docs API (requires authentication)
        document = fetch_document_via_api(doc_id, credentials_path)

        if output_format == 'json':
            import json
            return json.dumps(document, indent=2)
        elif output_format == 'markdown':
            return document_to_markdown(document)
        elif output_format == 'text':
            return document_to_text(document)
        elif output_format == 'html':
            # HTML export is better via export URL
            raise ValueError("HTML format is better with --export flag")
        else:
            raise ValueError(f"Unknown format: {output_format}")
