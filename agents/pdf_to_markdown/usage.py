#!/usr/bin/env python3
"""
Usage example for PDF to Markdown Parser (Tables Only)

This script demonstrates how to use the pdf_to_markdown_parser.py
which processes ONLY pages containing tables from PDF files.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pdf_to_markdown_parser import process_pdf_to_markdown, create_client, get_config

def main():
    """Example usage of the PDF to Markdown parser (tables only)"""
    print("📄 PDF to Markdown Parser - Usage Example (Tables Only)")
    print("=" * 60)
    
    # Setup
    data_dir = Path("../../data")
    output_dir = Path("../../data-parsed")
    
    # Get configuration
    config = get_config()
    llm_client = create_client(
        endpoint_url=config['endpoint_url'],
        model_name=config['model_name'],
        api_key=config['api_key']
    )
    
    # Find PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data directory")
        return
    
    # Process the first PDF as an example
    pdf_file = pdf_files[0]
    print(f"Processing: {pdf_file.name}")
    
    # Process the PDF (only pages with tables)
    saved_files = process_pdf_to_markdown(
        pdf_path=pdf_file,
        llm_client=llm_client,
        model_name=config['model_name'],
        output_dir=output_dir
    )
    
    print(f"\n✅ Processing complete!")
    print(f"Saved {len(saved_files)} markdown files (pages with tables only):")
    for file_path in saved_files:
        print(f"  📝 {file_path}")
    
    if not saved_files:
        print("ℹ️  No pages with tables found in this PDF.")

if __name__ == "__main__":
    main()
