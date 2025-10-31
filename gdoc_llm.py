#!/usr/bin/env python3
"""
Google Gemini LLM Integration Module

Provides functions to interact with Google Gemini LLM for advanced processing
of Google Docs content.
"""

import os
from typing import Optional, Dict, Any, List
import google.generativeai as genai


def configure_gemini(api_key: Optional[str] = None) -> None:
    """
    Configure the Gemini API client.

    Args:
        api_key: Google API key. If None, reads from GEMINI_API_KEY environment variable.

    Raises:
        ValueError: If no API key is provided or found in environment.
    """
    if api_key is None:
        api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        raise ValueError(
            "No Gemini API key provided. Set GEMINI_API_KEY environment variable "
            "or pass api_key parameter."
        )

    genai.configure(api_key=api_key)


def send_prompt(
    prompt: str,
    model_name: str = "gemini-2.5-flash",
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    max_output_tokens: Optional[int] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Send a prompt to Gemini and return the response.

    Args:
        prompt: The text prompt to send to the model.
        model_name: The Gemini model to use (default: gemini-2.5-flash).
        system_instruction: Optional system instruction to guide model behavior.
        temperature: Controls randomness (0.0-1.0). Lower = more deterministic.
        max_output_tokens: Maximum tokens in response. None = model default.
        api_key: API key (optional if already configured or in environment).

    Returns:
        The model's text response.

    Raises:
        ValueError: If API is not configured.
        Exception: For API errors.
    """
    # Configure if API key provided
    if api_key:
        configure_gemini(api_key)

    # Build generation config
    generation_config = {
        "temperature": temperature,
    }
    if max_output_tokens:
        generation_config["max_output_tokens"] = max_output_tokens

    # Create model
    model_kwargs = {
        "model_name": model_name,
        "generation_config": generation_config,
    }
    if system_instruction:
        model_kwargs["system_instruction"] = system_instruction

    model = genai.GenerativeModel(**model_kwargs)

    # Generate response
    response = model.generate_content(prompt)

    return response.text


def chat_conversation(
    messages: List[Dict[str, str]],
    model_name: str = "gemini-2.5-flash",
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    api_key: Optional[str] = None
) -> str:
    """
    Have a multi-turn conversation with Gemini.

    Args:
        messages: List of message dicts with 'role' (user/model) and 'content' keys.
        model_name: The Gemini model to use.
        system_instruction: Optional system instruction.
        temperature: Controls randomness.
        api_key: API key (optional if already configured).

    Returns:
        The model's response to the last message.

    Example:
        messages = [
            {"role": "user", "content": "Hello!"},
            {"role": "model", "content": "Hi! How can I help?"},
            {"role": "user", "content": "Tell me about Python."}
        ]
        response = chat_conversation(messages)
    """
    if api_key:
        configure_gemini(api_key)

    generation_config = {"temperature": temperature}

    model_kwargs = {
        "model_name": model_name,
        "generation_config": generation_config,
    }
    if system_instruction:
        model_kwargs["system_instruction"] = system_instruction

    model = genai.GenerativeModel(**model_kwargs)

    # Start chat with history (excluding the last user message)
    chat = model.start_chat(history=[])

    # Add all messages to conversation
    for i, msg in enumerate(messages):
        if msg["role"] == "user":
            if i == len(messages) - 1:
                # Last message - get response
                response = chat.send_message(msg["content"])
                return response.text
            else:
                # Historical user message
                chat.send_message(msg["content"])
        # Model responses are automatically tracked in history

    raise ValueError("Last message must be from user")


def analyze_document(
    document_content: str,
    analysis_type: str = "summary",
    custom_prompt: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None
) -> str:
    """
    Analyze a Google Doc using Gemini with predefined analysis types.

    Args:
        document_content: The full text content of the document.
        analysis_type: Type of analysis - 'summary', 'key_points', 'questions', or 'custom'.
        custom_prompt: Custom prompt (required if analysis_type is 'custom').
        model_name: The Gemini model to use.
        api_key: API key (optional if already configured).

    Returns:
        The analysis result as text.
    """
    if api_key:
        configure_gemini(api_key)

    # Build prompt based on analysis type
    if analysis_type == "summary":
        prompt = f"""Provide a concise summary of the following document:

{document_content}

Summary:"""

    elif analysis_type == "key_points":
        prompt = f"""Extract and list the key points from the following document:

{document_content}

Key points:"""

    elif analysis_type == "questions":
        prompt = f"""Generate thoughtful questions about the following document that would help test comprehension:

{document_content}

Questions:"""

    elif analysis_type == "custom":
        if not custom_prompt:
            raise ValueError("custom_prompt required when analysis_type is 'custom'")
        prompt = f"""{custom_prompt}

Document:
{document_content}"""

    else:
        raise ValueError(f"Unknown analysis_type: {analysis_type}")

    return send_prompt(
        prompt=prompt,
        model_name=model_name,
        temperature=0.5,  # Lower temperature for more factual analysis
        api_key=api_key
    )


if __name__ == "__main__":
    # Simple test
    try:
        configure_gemini()
        response = send_prompt("Say hello!")
        print("Response:", response)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo test this module, set GEMINI_API_KEY environment variable:")
        print("export GEMINI_API_KEY='your-api-key-here'")
