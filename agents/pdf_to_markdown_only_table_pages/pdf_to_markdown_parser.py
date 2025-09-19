#!/usr/bin/env python3
"""
PDF to Markdown Parser (Tables Only) - Image-based Processing

Uses table_detector.py to find pages with tables in PDFs, then uses LLM (qwen2.5vl:32b)
with image analysis to parse ONLY those pages with tables into markdown format and saves each page as a separate file.

This parser will:
1. Detect which pages contain tables
2. Convert pages with tables to images
3. Use multimodal LLM to analyze images and extract content
4. Process ONLY the pages that have tables
5. Skip pages without tables entirely
6. Clean up temporary image files

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

from client.llm_client import create_client, simple_query, get_config, analyze_image, create_image_message, multimodal_chat_completion
from agents.where_is_tables.table_detector import detect_tables_in_pdf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_page_as_image(pdf_path: Path, page_num: int) -> str:
    """
    Extract a specific page from PDF as image and save to temporary file for LLM processing.
    
    Args:
        pdf_path (Path): Path to the PDF file
        page_num (int): Page number (1-indexed)
        
    Returns:
        str: Path to the saved image file, or None if error
    """
    try:
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[page_num - 1]  # Convert to 0-indexed
        
        # Render page as image
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        
        pdf_document.close()
        
        # Create temporary image file
        temp_dir = Path("temp_images")
        temp_dir.mkdir(exist_ok=True)
        
        # Create filename for the image
        safe_pdf_name = pdf_path.stem.replace(' ', '_')
        img_filename = f"{safe_pdf_name}_page_{page_num:03d}.png"
        img_path = temp_dir / img_filename
        
        # Save image to file
        with open(img_path, 'wb') as img_file:
            img_file.write(img_data)
        
        logger.info(f"Saved page {page_num} as image: {img_path}")
        return str(img_path)
        
    except Exception as e:
        logger.error(f"Error extracting page {page_num} as image: {e}")
        return None


def parse_page_with_llm(llm_client, model_name: str, pdf_path: Path, page_num: int, img_path: str) -> str:
    """
    Parse a PDF page using LLM with image analysis.
    
    Args:
        llm_client: LLM client instance
        model_name (str): Name of the model to use
        pdf_path (Path): Path to the PDF file
        page_num (int): Page number
        img_path (str): Path to the image file of the page
        
    Returns:
        str: Markdown content of the page
    """
    try:
        # Create a detailed prompt for image analysis
        prompt = f"""Analyze this image from page {page_num} of PDF "{pdf_path.name}" and convert the table to well-structured markdown format.

This page contains ONLY a table. Please:
1. Extract all text content from the table accurately
2. Format the table using proper markdown table syntax with | separators
3. Preserve the exact table structure, rows, and columns
4. Maintain proper data alignment and spacing
5. Include all table headers and data cells
6. Handle merged cells appropriately in markdown format
7. Ensure all text is readable and properly formatted

Focus on table accuracy and structure. Return only the markdown table content without any additional commentary or headers."""

        # Use the new image analysis function
        if img_path and os.path.exists(img_path):
            logger.info(f"Using image analysis for page {page_num}")
            response = analyze_image(
                llm_client, 
                model_name, 
                img_path, 
                prompt,
                temperature=0.1, 
                max_tokens=4000
            )
            return response
        else:
            logger.warning(f"Image file not found for page {page_num}, falling back to text extraction")
            raise FileNotFoundError("Image file not available")
        
    except Exception as e:
        logger.error(f"Error parsing page {page_num} with LLM: {e}")


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
        
        # Extract page as image for LLM processing
        img_path = extract_page_as_image(pdf_path, page_num)
        
        # Parse page with LLM using image analysis
        markdown_content = parse_page_with_llm(llm_client, model_name, pdf_path, page_num, img_path)
        
        # Save markdown file
        saved_file = save_markdown_page(markdown_content, pdf_path.name, page_num, output_dir)
        if saved_file:
            saved_files.append(saved_file)
        
        # Clean up temporary image file
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
                logger.debug(f"Cleaned up temporary image: {img_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary image {img_path}: {e}")
    
    logger.info(f"Processed {len(saved_files)} pages with tables from {pdf_path.name}")
    return saved_files


def cleanup_temp_images():
    """Clean up temporary images directory."""
    temp_dir = Path("temp_images")
    if temp_dir.exists():
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info("Cleaned up temporary images directory")
        except Exception as e:
            logger.warning(f"Could not clean up temporary images directory: {e}")


def main():
    """Main function - PDF to Markdown conversion (only pages with tables)"""
    print("📄 PDF to Markdown Parser - Tables Only (Image-based)")
    print("=" * 50)
    
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
    
    # Clean up temporary images
    #cleanup_temp_images()


if __name__ == "__main__":
    main()
