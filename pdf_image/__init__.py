"""
PDF to JPEG conversion library
Simple library to convert PDF files to JPEG images
"""

from .pdf_converter import PDFToJPEGConverter, convert_pdfs

__version__ = "1.0.0"
__all__ = ["PDFToJPEGConverter", "convert_pdfs"]
