#!/usr/bin/env python3
"""
PDF to Markdown Parser (All Pages) - Image-based Processing
parse ALL pages of PDFs into markdown format 
and saves each page as a separate file.

This parser will:
1. Convert all pages to images
2. Use multimodal LLM to analyze images and extract content
3. Process ALL pages of the PDF
4. Extract text, tables, images, and other content
5. Clean up temporary image files

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
        prompt = f"""Analyze this image from page {page_num} of PDF "{pdf_path.name}" and convert ALL content to well-structured markdown format.

Please extract and format:
1. All text content accurately (headings, paragraphs, lists, etc.)
2. Tables using proper markdown table syntax with | separators
3. Images (describe them in markdown format)
4. Any other visual elements

For tables specifically:
- Preserve the exact table structure, rows, and columns
- Maintain proper data alignment and spacing
- Include all table headers and data cells
- Handle merged cells appropriately in markdown format

For other content:
- Use appropriate markdown headers (# ## ###)
- Format lists with - or 1. as needed
- Preserve paragraph structure
- Maintain text formatting (bold, italic) where appropriate

Return only the markdown content without any additional commentary or headers."""

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
    Process a PDF file: parse ALL pages and save as markdown.
    
    Args:
        pdf_path (Path): Path to the PDF file
        llm_client: LLM client instance
        model_name (str): Name of the model to use
        output_dir (Path): Directory to save markdown files
        
    Returns:
        list: List of saved markdown file paths
    """
    logger.info(f"Processing PDF: {pdf_path.name}")
    
    # Get total number of pages in the PDF
    try:
        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)
        pdf_document.close()
        logger.info(f"PDF has {total_pages} pages")
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return []
    
    # Process ALL pages
    logger.info("Step 1: Parsing ALL pages using LLM...")
    saved_files = []
    
    for page_num in range(1, total_pages + 1):
        logger.info(f"Processing page {page_num}/{total_pages}...")
        
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
    
    logger.info(f"Processed {len(saved_files)} pages from {pdf_path.name}")
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
    """Main function - PDF to Markdown conversion (all pages)"""
    print("📄 PDF to Markdown Parser - All Pages (Image-based)")
    print("=" * 50)
    
    # Setup directories
    data_dir = Path("../../data")
    output_dir = Path("../data-parsed")
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Create output directory if it doesn't exist
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created output directory: {output_dir}")
    else:
        print(f"📁 Output directory exists: {output_dir}")
    
    # Get specific PDF file - Malakoff Humanis ESG report
    target_pdf = "malakoff-humanis-rapport-ESG-climat-article-29-loi-energie-climat-exercice-2022-mh-22365-2306-192.pdf"
    pdf_path = data_dir / target_pdf
    
    if not pdf_path.exists():
        print(f"❌ Target PDF not found: {pdf_path}")
        return
    
    pdf_files = [pdf_path]
    print(f"📁 Processing specific PDF: {target_pdf}")
    
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
    
    # Process each PDF (all pages)
    print("\n🔄 Processing PDFs (all pages)...")
    all_saved_files = []
    
    for pdf_file in pdf_files:
        print(f"\n📄 Processing: {pdf_file.name}")
        try:
            saved_files = process_pdf_to_markdown(pdf_file, llm_client, model_name, output_dir)
            all_saved_files.extend(saved_files)
            
            if saved_files:
                print(f"   ✅ Saved {len(saved_files)} markdown files (all pages)")
                for file_path in saved_files:
                    print(f"      📝 {file_path.name}")
            else:
                print(f"   ℹ️  No pages processed - error occurred")
                
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")
            print(f"   ❌ Error processing {pdf_file.name}: {e}")
    
    # Summary
    print(f"\n📊 Summary")
    print("=" * 20)
    print(f"Total markdown files created (all pages): {len(all_saved_files)}")
    if all_saved_files:
        print("Files saved (all pages processed):")
        for file_path in all_saved_files:
            print(f"  📝 {file_path}")
    else:
        print("No pages processed from any PDF files.")
    
    # Clean up temporary images
    #cleanup_temp_images()


if __name__ == "__main__":
    main()
