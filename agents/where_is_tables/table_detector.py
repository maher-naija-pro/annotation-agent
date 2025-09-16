#!/usr/bin/env python3
"""
Simple PDF Table Detection Script

Reads PDF files from data/ directory and uses LLM to find pages with tables.
Returns a list of page numbers where tables are found.

Usage: python table_detector.py
"""

import os
import sys
import logging
from pathlib import Path
import fitz  # PyMuPDF

# Add the parent directory to the path to import client modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from client.llm_client import create_client, simple_query, get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def detect_tables_in_pdf(pdf_path: Path, llm_client, model_name: str) -> list:
    """Detect tables in a PDF file and return list of page numbers with tables"""
    logger.info(f"Analyzing {pdf_path.name} for tables...")
    
    try:
        # Open PDF to get page count
        pdf_document = fitz.open(pdf_path)
        page_count = pdf_document.page_count
        pdf_document.close()
        
        logger.info(f"Processing {page_count} pages in {pdf_path.name}")
        
        pages_with_tables = []
        
        for page_num in range(page_count):
            logger.info(f"Processing page {page_num + 1}/{page_count}")
            
            # Extract text from page
            pdf_document = fitz.open(pdf_path)
            page = pdf_document[page_num]
            text = page.get_text()
            pdf_document.close()
            
            if not text.strip():
                logger.warning(f"Page {page_num + 1} has no text content")
                continue
            
            # Ask LLM if page has tables
            prompt = f"""Analyze this text from page {page_num + 1} of PDF "{pdf_path.name}" and determine if it contains tables.

Look for tabular data, rows/columns, structured data, financial data, or statistics.

Text: {text[:2000]}

Respond with only "YES" if tables are present, or "NO" if no tables found."""
            
            try:
                if llm_client is None:
                    # Mock LLM - simulate table detection based on text patterns
                    has_table_indicators = any(indicator in text.lower() for indicator in [
                        'table', 'tabular', 'rows', 'columns', 'data', 'statistics', 
                        'financial', 'metrics', 'kpi', 'summary', 'report'
                    ])
                    response_clean = "YES" if has_table_indicators else "NO"
                    print(f"   🔍 Mock analysis: {'Table indicators found' if has_table_indicators else 'No table indicators'}")
                else:
                    response = simple_query(llm_client, model_name, prompt, temperature=0.1, max_tokens=10)
                    response_clean = response.strip().upper()
                
                if "YES" in response_clean:
                    pages_with_tables.append(page_num + 1)
                    logger.info(f"Table found on page {page_num + 1}")
                
            except Exception as e:
                logger.error(f"Error analyzing page {page_num + 1}: {e}")
        
        logger.info(f"Found tables on {len(pages_with_tables)} pages: {pages_with_tables}")
        return pages_with_tables
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path.name}: {e}")
        return []


def main():
    """Main function - simple table detection"""
    print("🔍 PDF Table Detection")
    print("=" * 30)
    
    # Setup data directory
    data_dir = Path("../../data")
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Get PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {data_dir}")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files")
    
    # Setup LLM client - use default configuration
    try:
        # Get configuration with default endpoint IP 148.253.83.132
        config = get_config()
        llm_client = create_client(
            endpoint_url=config['endpoint_url'],
            model_name=config['model_name'],
            api_key=config['api_key']
        )
        model_name = config['model_name']
        print(f"🤖 LLM Client ready: {model_name} (Endpoint: {config['endpoint_url']})")
    except Exception as e:
        print(f"⚠️  LLM not available: {e}")
        print("🔄 Using mock LLM for demonstration...")
        # Mock LLM for demonstration
        llm_client = None
        model_name = "mock-llm"
    
    # Process each PDF
    print("\n📊 Analyzing PDFs...")
    for pdf_file in pdf_files:
        print(f"\n📄 {pdf_file.name}")
        pages_with_tables = detect_tables_in_pdf(pdf_file, llm_client, model_name)
        
        if pages_with_tables:
            print(f"   ✅ Tables found on pages: {', '.join(map(str, pages_with_tables))}")
        else:
            print(f"   ❌ No tables found")


if __name__ == "__main__":
    main()
