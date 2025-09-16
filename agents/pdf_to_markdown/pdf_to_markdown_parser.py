#!/usr/bin/env python3
"""
PDF to Markdown Parser (Tables Only)

Uses table_detector.py to find pages with tables in PDFs, then uses LLM (qwen2.5vl:32b)
to parse ONLY those pages with tables into markdown format and saves each page as a separate file.

This parser will:
1. Detect which pages contain tables
2. Process ONLY the pages that have tables
3. Skip pages without tables entirely

Usage: python pdf_to_markdown_parser.py
"""

import os
import sys
import logging
from pathlib import Path
import fitz  # PyMuPDF
from datetime import datetime

# Add the parent directory to the path to import client modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from client.llm_client import create_client, simple_query, get_config
from agents.where_is_tables.table_detector import detect_tables_in_pdf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_page_as_image(pdf_path: Path, page_num: int) -> bytes:
    """
    Extract a specific page from PDF as image bytes for LLM processing.
    
    Args:
        pdf_path (Path): Path to the PDF file
        page_num (int): Page number (1-indexed)
        
    Returns:
        bytes: Image data in PNG format
    """
    try:
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[page_num - 1]  # Convert to 0-indexed
        
        # Render page as image with high DPI for better quality
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        pdf_document.close()
        return img_data
        
    except Exception as e:
        logger.error(f"Error extracting page {page_num} as image: {e}")
        return None


def parse_page_with_llm(llm_client, model_name: str, pdf_path: Path, page_num: int, img_data: bytes) -> str:
    """
    Use LLM to parse a PDF page (as image) into markdown format.
    
    Args:
        llm_client: LLM client instance
        model_name (str): Name of the model to use
        pdf_path (Path): Path to the PDF file
        page_num (int): Page number being processed
        img_data (bytes): Image data of the page
        
    Returns:
        str: Markdown content of the page
    """
    try:
        # Create a detailed prompt for the LLM
        prompt = f"""Analyze this image from page {page_num} of PDF "{pdf_path.name}" and convert it to well-structured markdown format.

Please:
1. Extract all text content accurately
2. Identify and format tables using markdown table syntax
3. Preserve the structure and hierarchy of the content
4. Use appropriate markdown headers (#, ##, ###) for sections
5. Format lists, bullet points, and numbered items properly
6. Include any important visual elements or formatting cues
7. If there are tables, make sure they are properly formatted with | separators

Focus on accuracy and maintaining the original document structure. Return only the markdown content without any additional commentary."""

        # For now, we'll use text extraction as fallback since the current LLM client
        # doesn't support image input. In a real implementation, you'd need to modify
        # the LLM client to support vision models.
        
        # Extract text as fallback
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[page_num - 1]
        text = page.get_text()
        pdf_document.close()
        
        # Use LLM to structure the text into markdown
        structured_prompt = f"""Convert this extracted text from page {page_num} of PDF "{pdf_path.name}" into well-structured markdown format:

{text}

Please:
1. Structure the content with appropriate markdown headers
2. Format any tables using markdown table syntax
3. Use proper markdown formatting for lists, emphasis, etc.
4. Maintain the logical flow and hierarchy of the original content
5. Return only the markdown content without additional commentary."""

        if llm_client is None:
            # Mock response for demonstration
            logger.warning("LLM client not available, using mock markdown conversion")
            return f"# Page {page_num} from {pdf_path.name}\n\n```\n{text[:500]}...\n```\n\n*Note: This is a mock conversion. LLM client is not available.*"
        
        response = simple_query(
            llm_client, 
            model_name, 
            structured_prompt, 
            temperature=0.1, 
            max_tokens=4000
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error parsing page {page_num} with LLM: {e}")
        # Fallback to basic text extraction
        try:
            pdf_document = fitz.open(pdf_path)
            page = pdf_document[page_num - 1]
            text = page.get_text()
            pdf_document.close()
            return f"# Page {page_num} from {pdf_path.name}\n\n```\n{text}\n```"
        except Exception as fallback_error:
            logger.error(f"Fallback text extraction also failed: {fallback_error}")
            return f"# Page {page_num} from {pdf_path.name}\n\n*Error: Could not extract content from this page.*"


def save_markdown_page(content: str, pdf_name: str, page_num: int, output_dir: Path) -> Path:
    """
    Save markdown content to a file.
    
    Args:
        content (str): Markdown content to save
        pdf_name (str): Name of the source PDF file
        page_num (int): Page number
        output_dir (Path): Directory to save the file
        
    Returns:
        Path: Path to the saved file
    """
    # Create filename: pdf_name_page_XX.md
    safe_pdf_name = pdf_name.replace('.pdf', '').replace(' ', '_')
    filename = f"{safe_pdf_name}_page_{page_num:03d}.md"
    file_path = output_dir / filename
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved markdown: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving markdown file {file_path}: {e}")
        return None


def process_pdf_to_markdown(pdf_path: Path, llm_client, model_name: str, output_dir: Path) -> list:
    """
    Process a PDF file: detect tables, parse ONLY pages with tables, and save as markdown.
    
    Args:
        pdf_path (Path): Path to the PDF file
        llm_client: LLM client instance
        model_name (str): Name of the model to use
        output_dir (Path): Directory to save markdown files
        
    Returns:
        list: List of saved markdown file paths
    """
    logger.info(f"Processing PDF: {pdf_path.name}")
    
    # Step 1: Detect pages with tables
    logger.info("Step 1: Detecting pages with tables...")
    pages_with_tables = detect_tables_in_pdf(pdf_path, llm_client, model_name)
    
    if not pages_with_tables:
        logger.info(f"No tables found in {pdf_path.name} - skipping PDF")
        return []
    
    logger.info(f"Found tables on pages: {pages_with_tables}")
    
    # Step 2: Process ONLY pages with tables
    logger.info("Step 2: Parsing ONLY pages with tables using LLM...")
    saved_files = []
    
    for page_num in pages_with_tables:
        logger.info(f"Processing page {page_num} (has tables)...")
        
        # Extract page as image (for future vision model support)
        img_data = extract_page_as_image(pdf_path, page_num)
        
        # Parse page with LLM
        markdown_content = parse_page_with_llm(llm_client, model_name, pdf_path, page_num, img_data)
        
        # Save markdown file
        saved_file = save_markdown_page(markdown_content, pdf_path.name, page_num, output_dir)
        if saved_file:
            saved_files.append(saved_file)
    
    logger.info(f"Processed {len(saved_files)} pages with tables from {pdf_path.name}")
    return saved_files


def main():
    """Main function - PDF to Markdown conversion (only pages with tables)"""
    print("📄 PDF to Markdown Parser - Tables Only")
    print("=" * 45)
    
    # Setup directories
    data_dir = Path("../../data")
    output_dir = Path("../../data-parsed")
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Get PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {data_dir}")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files")
    
    # Setup LLM client
    try:
        config = get_config()
        llm_client = create_client(
            endpoint_url=config['endpoint_url'],
            model_name=config['model_name'],
            api_key=config['api_key']
        )
        model_name = config['model_name']
        print(f"🤖 LLM Client ready: {model_name}")
        print(f"   Endpoint: {config['endpoint_url']}")
    except Exception as e:
        print(f"⚠️  LLM not available: {e}")
        print("🔄 Using mock LLM for demonstration...")
        llm_client = None
        model_name = "mock-llm"
    
    # Process each PDF (only pages with tables)
    print("\n🔄 Processing PDFs (tables only)...")
    all_saved_files = []
    
    for pdf_file in pdf_files:
        print(f"\n📄 Processing: {pdf_file.name}")
        try:
            saved_files = process_pdf_to_markdown(pdf_file, llm_client, model_name, output_dir)
            all_saved_files.extend(saved_files)
            
            if saved_files:
                print(f"   ✅ Saved {len(saved_files)} markdown files (pages with tables)")
                for file_path in saved_files:
                    print(f"      📝 {file_path.name}")
            else:
                print(f"   ℹ️  No pages with tables found - skipped")
                
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")
            print(f"   ❌ Error processing {pdf_file.name}: {e}")
    
    # Summary
    print(f"\n📊 Summary")
    print("=" * 20)
    print(f"Total markdown files created (pages with tables): {len(all_saved_files)}")
    if all_saved_files:
        print("Files saved (only pages containing tables):")
        for file_path in all_saved_files:
            print(f"  📝 {file_path}")
    else:
        print("No pages with tables found in any PDF files.")


if __name__ == "__main__":
    main()
