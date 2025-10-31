#!/usr/bin/env python3
"""
Setup script for gdoc tools
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements = Path("requirements.txt").read_text().strip().split("\n")

# Read README if it exists
readme = ""
if Path("README.md").exists():
    readme = Path("README.md").read_text()

setup(
    name="gdoc-tools",
    version="0.1.0",
    description="CLI tools for accessing and querying Google Docs from .gdoc files",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Your Name",
    url="https://github.com/duluk/gdoc-tools",
    packages=find_packages(),
    py_modules=[
        'gdoc_reader',
        'gdoc_fetcher',
        'gdoc_processor',
        'gdoc_llm',
        'chat_interactive',
        'example_llm',
    ],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'gdoc=gdoc_reader:main',
            'gdoc-chat=chat_interactive:main',
            'gdoc-example=example_llm:main',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
