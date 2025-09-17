#!/usr/bin/env python3
"""
Simple Image to JSON Converter
A simplified version that processes files in a folder and saves each as JSON
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add client directory to path for LLM client import
sys.path.append(str(Path(__file__).parent.parent.parent / "client"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from llm_client import create_client, get_config, analyze_image
except ImportError as e:
    logger.error(f"Missing required dependencies: {e}")
    logger.error("Please install: pip install openai")
    exit(1)


def process_folder_to_json(folder_path: str, output_folder: str = "output") -> List[str]:
    """
    Simple function to process all image files in a folder and save each as JSON
    
    Args:
        folder_path: Path to folder containing image files
        output_folder: Path to output folder for JSON files
        
    Returns:
        List of saved JSON file paths
    """
    logger.info(f"Starting simple folder processing: {folder_path}")
    
    # Setup paths
    input_path = Path(folder_path)
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    # Check if input folder exists
    if not input_path.exists():
        logger.error(f"Input folder does not exist: {folder_path}")
        return []
    
    # Initialize LLM client
    logger.info("Initializing LLM client...")
    try:
        llm_config = get_config()
        llm_client = create_client(
            endpoint_url=llm_config['endpoint_url'],
            model_name=llm_config['model_name'],
            api_key=llm_config['api_key']
        )
        logger.info(f"LLM client initialized: {llm_config['model_name']}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        return []
    
    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = []
    
    for ext in image_extensions:
        files_found = list(input_path.rglob(f"*{ext}"))
        image_files.extend(files_found)
    
    if not image_files:
        logger.warning("No image files found in folder")
        return []
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    # Process each image file
    saved_files = []
    for i, image_path in enumerate(sorted(image_files), 1):
        logger.info(f"Processing {i}/{len(image_files)}: {image_path.name}")
        
        try:
            # Analyze image with LLM
            prompt = "Convert this image to JSON format. Extract all text, tables, and structured data."
            
            analysis = analyze_image(
                llm_client,
                llm_config['model_name'],
                str(image_path),
                prompt,
                temperature=0.1,
                max_tokens=3000
            )
            
            # Try to parse JSON from response
            try:
                json_start = analysis.find('{')
                json_end = analysis.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = analysis[json_start:json_end]
                    parsed_json = json.loads(json_str)
                else:
                    parsed_json = {"raw_analysis": analysis}
            except json.JSONDecodeError:
                parsed_json = {"raw_analysis": analysis}
            
            # Create result structure
            result = {
                "file_path": str(image_path),
                "file_name": image_path.name,
                "processing_timestamp": str(Path(image_path).stat().st_mtime),
                "data": parsed_json
            }
            
            # Save as JSON file
            output_filename = f"{image_path.stem}.json"
            output_file_path = output_path / output_filename
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            saved_files.append(str(output_file_path))
            logger.info(f"Saved: {output_filename}")
            
        except Exception as e:
            logger.error(f"Error processing {image_path.name}: {e}")
            # Save error result
            error_result = {
                "file_path": str(image_path),
                "file_name": image_path.name,
                "processing_timestamp": str(Path(image_path).stat().st_mtime),
                "error": str(e)
            }
            
            output_filename = f"{image_path.stem}_error.json"
            output_file_path = output_path / output_filename
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)
            
            saved_files.append(str(output_file_path))
    
    logger.info(f"Processing complete! Saved {len(saved_files)} files to {output_folder}")
    return saved_files


def main():
    """
    Main function to run the simple converter
    """
    print("Simple Image to JSON Converter")
    print("=" * 40)
    
    # Process the data-images folder
    folder_path = "../../data-images"
    output_folder = "output"
    
    print(f"Processing folder: {folder_path}")
    print(f"Output folder: {output_folder}")
    print()
    
    saved_files = process_folder_to_json(folder_path, output_folder)
    
    if saved_files:
        print(f"\nSuccessfully processed {len(saved_files)} files:")
        for file_path in saved_files:
            print(f"  - {file_path}")
    else:
        print("\nNo files were processed.")


if __name__ == "__main__":
    main()
