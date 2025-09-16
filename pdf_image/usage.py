#!/usr/bin/env python3
"""
Example usage of the PDF to JPEG converter library
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import the library
sys.path.append(str(Path(__file__).parent.parent))

from pdf_image import PDFToJPEGConverter, convert_pdfs



def example_advanced_usage():
    """Example of advanced usage with the class"""
    print("\n=== Advanced Usage Example ===")
    
    # Define input and output directories
    input_dir = "data"
    output_dir = "data-images/output_advanced"
    
    try:
        # Create converter instance
        converter = PDFToJPEGConverter(input_dir, output_dir)
        
        # Get list of PDF files
        pdf_files = converter.get_pdf_files()
        print(f"Found {len(pdf_files)} PDF files:")
        for pdf_file in pdf_files:
            print(f"  - {pdf_file.name}")
        
        # Convert each PDF individually (for more control)
        total_pages = 0
        for pdf_file in pdf_files:
            print(f"\nConverting {pdf_file.name}...")
            pages_converted = converter.convert_pdf_to_jpeg(pdf_file)
            total_pages += pages_converted
            print(f"Converted {pages_converted} pages")
        
        print(f"\nTotal pages converted: {total_pages}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")




if __name__ == "__main__":
    print("PDF to JPEG Converter - Example Usage")
    print("=" * 50)
    
    # Run examples

    example_advanced_usage()

    
    print("\n" + "=" * 50)
   