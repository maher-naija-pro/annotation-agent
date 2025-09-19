#!/usr/bin/env python3
"""
Simple script to read JSON file and display each row from the table data.
This script reads the page_006.json file and iterates through each row in the table.
"""

import json
import os
from typing import Dict, List, Any

def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        Dict[str, Any]: Parsed JSON data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{file_path}': {e}")
        return {}
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return {}

def display_table_info(data: Dict[str, Any]) -> None:
    """
    Display table information and metadata.
    
    Args:
        data (Dict[str, Any]): JSON data containing table information
    """
    if not data:
        return
    
    print("=" * 80)
    print("JSON FILE INFORMATION")
    print("=" * 80)
    print(f"File Path: {data.get('file_path', 'N/A')}")
    print(f"File Name: {data.get('file_name', 'N/A')}")
    print(f"Processing Timestamp: {data.get('processing_timestamp', 'N/A')}")
    
    # Display title
    if 'data' in data and 'title' in data['data']:
        print(f"\nTitle: {data['data']['title']}")
    
    # Display table information
    if 'data' in data and 'table' in data['data']:
        table = data['data']['table']
        print(f"\nTable Name: {table.get('name', 'N/A')}")
        print(f"Columns: {', '.join(table.get('columns', []))}")
        print(f"Number of Rows: {len(table.get('rows', []))}")

def display_rows(data: Dict[str, Any]) -> None:
    """
    Iterate through each row and display it in a formatted way.
    
    Args:
        data (Dict[str, Any]): JSON data containing table rows
    """
    if not data or 'data' not in data or 'table' not in data['data']:
        print("No table data found.")
        return
    
    table = data['data']['table']
    rows = table.get('rows', [])
    columns = table.get('columns', [])
    
    if not rows:
        print("No rows found in the table.")
        return
    
    print("\n" + "=" * 80)
    print("TABLE ROWS")
    print("=" * 80)
    
    for i, row in enumerate(rows, 1):
        print(f"\n--- ROW {i} ---")
        for column in columns:
            value = row.get(column, 'N/A')
            print(f"{column}: {value}")
        print("-" * 40)

def display_notes(data: Dict[str, Any]) -> None:
    """
    Display notes if they exist.
    
    Args:
        data (Dict[str, Any]): JSON data containing notes
    """
    if not data or 'data' not in data or 'notes' not in data['data']:
        return
    
    notes = data['data']['notes']
    if not notes:
        return
    
    print("\n" + "=" * 80)
    print("NOTES")
    print("=" * 80)
    
    for note in notes:
        print(f"Note {note.get('number', 'N/A')}: {note.get('text', 'N/A')}")

def main():
    """
    Main function to execute the JSON reading and display process.
    """
    # Path to the JSON file (relative to this script)
    json_file_path = "../image_to_json/output/page_006.json"
    
    # Get absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, json_file_path)
    
    print("Reading JSON file...")
    print(f"File path: {full_path}")
    
    # Read JSON file
    data = read_json_file(full_path)
    
    if not data:
        print("Failed to read JSON file. Exiting.")
        return
    
    # Display table information
    display_table_info(data)
    
    # Display all rows
    display_rows(data)
    
    # Display notes
    display_notes(data)
    
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
