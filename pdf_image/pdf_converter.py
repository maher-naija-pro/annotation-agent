"""
Simple PDF to JPEG converter library
Converts all PDF files in a directory to JPEG images (one per page)
"""

import os
import sys
import io
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFToJPEGConverter:
    """
    Simple PDF to JPEG converter that processes all PDFs in a directory
    and exports each page as a separate JPEG image
    """
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize the converter with input and output directories
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory where JPEG images will be saved
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate input directory
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    def get_pdf_files(self) -> List[Path]:
        """
        Get all PDF files from the input directory
        
        Returns:
            List of Path objects for PDF files
        """
        pdf_files = list(self.input_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {self.input_dir}")
        return pdf_files
    
    def convert_pdf_to_jpeg(self, pdf_path: Path) -> int:
        """
        Convert a single PDF file to JPEG images
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages converted
        """
        try:
            # Open PDF document
            pdf_document = fitz.open(pdf_path)
            page_count = pdf_document.page_count
            logger.info(f"Converting {pdf_path.name} ({page_count} pages)")
            
            # Create subdirectory for this PDF
            pdf_name = pdf_path.stem
            pdf_output_dir = self.output_dir / pdf_name
            pdf_output_dir.mkdir(exist_ok=True)
            
            converted_pages = 0
            
            # Convert each page to JPEG
            for page_num in range(page_count):
                try:
                    # Get page
                    page = pdf_document[page_num]
                    
                    # Convert page to image (pixmap)
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Save as JPEG
                    output_filename = f"page_{page_num + 1:03d}.jpg"
                    output_path = pdf_output_dir / output_filename
                    img.save(output_path, "JPEG", quality=95)
                    
                    converted_pages += 1
                    logger.debug(f"Converted page {page_num + 1} to {output_path}")
                    
                except Exception as e:
                    logger.error(f"Error converting page {page_num + 1} of {pdf_path.name}: {e}")
                    continue
            
            pdf_document.close()
            logger.info(f"Successfully converted {converted_pages} pages from {pdf_path.name}")
            return converted_pages
            
        except Exception as e:
            logger.error(f"Error converting PDF {pdf_path.name}: {e}")
            return 0
    
    def convert_all_pdfs(self) -> dict:
        """
        Convert all PDF files in the input directory to JPEG images
        
        Returns:
            Dictionary with conversion results
        """
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.input_dir}")
            return {"total_files": 0, "total_pages": 0, "errors": []}
        
        results = {
            "total_files": len(pdf_files),
            "total_pages": 0,
            "converted_files": 0,
            "errors": []
        }
        
        for pdf_file in pdf_files:
            try:
                pages_converted = self.convert_pdf_to_jpeg(pdf_file)
                if pages_converted > 0:
                    results["converted_files"] += 1
                    results["total_pages"] += pages_converted
                else:
                    results["errors"].append(f"Failed to convert {pdf_file.name}")
            except Exception as e:
                error_msg = f"Error processing {pdf_file.name}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results


def convert_pdfs(input_dir: str, output_dir: str) -> dict:
    """
    Simple function to convert all PDFs in a directory to JPEG images
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory where JPEG images will be saved
        
    Returns:
        Dictionary with conversion results
    """
    converter = PDFToJPEGConverter(input_dir, output_dir)
    return converter.convert_all_pdfs()


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) != 3:
        print("Usage: python pdf_converter.py <input_dir> <output_dir>")
        print("Example: python pdf_converter.py ./pdfs ./images")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    
    print(f"Converting PDFs from {input_directory} to {output_directory}")
    results = convert_pdfs(input_directory, output_directory)
    
    print(f"\nConversion Results:")
    print(f"Total PDF files: {results['total_files']}")
    print(f"Successfully converted: {results['converted_files']}")
    print(f"Total pages converted: {results['total_pages']}")
    
    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
