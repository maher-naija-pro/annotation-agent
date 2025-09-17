#!/usr/bin/env python3
"""
Simple usage example for the simplified image to JSON converter
"""

from simple_converter import process_folder_to_json
import json


def main():
    """
    Example usage of the simple converter
    """
    print("Simple Image to JSON Converter - Usage Example")
    print("=" * 50)
    
    # Define paths
    input_folder = "../../data-images"
    output_folder = "output"
    
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print()
    
    # Process the folder
    print("Processing images...")
    saved_files = process_folder_to_json(input_folder, output_folder)
    
    # Show results
    if saved_files:
        print(f"\n✓ Successfully processed {len(saved_files)} files:")
        for file_path in saved_files:
            print(f"  - {file_path}")
        
        # Show example of first processed file
        if saved_files:
            print(f"\nExample of first processed file:")
            print("-" * 30)
            try:
                with open(saved_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"File: {data.get('file_name', 'Unknown')}")
                    print(f"Data keys: {list(data.keys())}")
                    if 'data' in data:
                        print(f"Data type: {type(data['data'])}")
                        if isinstance(data['data'], dict):
                            print(f"Data keys: {list(data['data'].keys())}")
            except Exception as e:
                print(f"Error reading example file: {e}")
    else:
        print("\n✗ No files were processed.")


if __name__ == "__main__":
    main()
