#!/usr/bin/env python3
"""
Generic Markdown Table Parser
A robust parser that can handle any markdown table format and display it line by line.
"""

import os
import sys
from typing import List, Dict, Any, Tuple
import re


def read_markdown_file(file_path: str) -> str:
    """
    Read the markdown file and return its content.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        str: Content of the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def parse_markdown_table(content: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Parse any markdown table content and extract structured data.
    This is a completely generic parser that works with any markdown table format.
    
    Args:
        content (str): Raw markdown content
        
    Returns:
        Tuple[List[Dict[str, str]], List[str]]: (data_rows, headers)
    """
    # Split content into lines
    lines = content.strip().split('\n')
    
    # Find all table lines (lines containing |)
    table_lines = []
    for line in lines:
        line = line.strip()
        if '|' in line and line:
            table_lines.append(line)
    
    if not table_lines:
        print("No table found in the content")
        return [], []
    
    # Parse each table line
    all_rows = []
    for line in table_lines:
        # Split by | and clean up
        cells = [cell.strip() for cell in line.split('|')]
        # Remove empty cells at the beginning and end
        while cells and not cells[0]:
            cells.pop(0)
        while cells and not cells[-1]:
            cells.pop()
        if cells:
            all_rows.append(cells)
    
    if not all_rows:
        print("No valid table rows found")
        return [], []
    
    # For single-line tables, we need to identify headers differently
    if len(all_rows) == 1:
        # This is a single-line table
        row = all_rows[0]
        
        # Find the header cells (usually after the title)
        # Look for common header patterns
        headers = []
        data_start = 0
        
        # Find where the actual headers start (skip title)
        for i, cell in enumerate(row):
            if cell.upper() == 'TOPIC' or (cell.upper() in ['TOPIC', 'METRIC', 'CATEGORY', 'UNIT', 'CODE'] and len(cell) < 20):
                headers = row[i:i+5]  # Take next 5 cells as headers
                data_start = i + 5
                break
        
        if not headers:
            # Fallback: use first 5 cells after title
            title_end = 0
            for i, cell in enumerate(row):
                if 'Table' in cell or '###' in cell:
                    title_end = i + 1
                    break
            
            if title_end + 5 <= len(row):
                headers = row[title_end:title_end+5]
                data_start = title_end + 5
            else:
                print("Could not identify table headers")
                return [], []
        
        # Process data in groups of 5
        data_rows = []
        remaining_cells = row[data_start:]
        
        for i in range(0, len(remaining_cells), 5):
            if i + 4 < len(remaining_cells):
                row_data = {}
                for j, header in enumerate(headers):
                    if i + j < len(remaining_cells):
                        row_data[header] = remaining_cells[i + j]
                    else:
                        row_data[header] = ""
                
                # Only add if we have meaningful data
                if any(value.strip() and not value.replace('-', '').replace(' ', '') == '' for value in row_data.values()):
                    data_rows.append(row_data)
        
        return data_rows, headers
    
    # Multi-line table processing (original logic)
    headers = []
    data_start_index = 0
    
    for i, row in enumerate(all_rows):
        # Check if this is a separator row (only dashes, spaces, and empty cells)
        is_separator = all(
            cell.replace('-', '').replace(' ', '') == '' or cell == '' 
            for cell in row
        )
        
        if not is_separator:
            headers = row
            data_start_index = i + 1
            break
    
    if not headers:
        print("Could not identify table headers")
        return [], []
    
    # Extract data rows
    data_rows = []
    for i in range(data_start_index, len(all_rows)):
        row = all_rows[i]
        
        # Skip separator rows
        is_separator = all(
            cell.replace('-', '').replace(' ', '') == '' or cell == '' 
            for cell in row
        )
        
        if is_separator:
            continue
        
        # Create dictionary for this row
        row_dict = {}
        for j, header in enumerate(headers):
            if j < len(row):
                row_dict[header] = row[j]
            else:
                row_dict[header] = ""
        
        data_rows.append(row_dict)
    
    return data_rows, headers


def display_table_line_by_line(data_rows: List[Dict[str, str]], headers: List[str]) -> None:
    """
    Display the table data line by line in a formatted way.
    This is a generic display function that works with any table structure.
    
    Args:
        data_rows (List[Dict[str, str]]): List of table rows
        headers (List[str]): Table headers
    """
    print("=" * 120)
    print("GENERIC MARKDOWN TABLE PARSER - LINE BY LINE DISPLAY")
    print("=" * 120)
    print()
    
    # Display headers
    print("TABLE HEADERS:")
    for i, header in enumerate(headers, 1):
        print(f"  {i}. {header}")
    print()
    
    # Display each row
    print("TABLE ROWS (Line by Line):")
    print("-" * 120)
    
    for row_num, row in enumerate(data_rows, 1):
        print(f"\nROW {row_num}:")
        print("-" * 60)
        
        # Display all fields for this row
        for header in headers:
            value = row.get(header, "").strip()
            if value:  # Only display non-empty values
                print(f"  {header}: {value}")
        
        print()
    
    print("\n" + "=" * 120)
    print(f"Total rows processed: {len(data_rows)}")
    print("=" * 120)


def main():
    """
    Main function to execute the table parsing and display.
    Supports command line arguments for file path.
    """
    # Check for command line arguments
    if len(sys.argv) > 1:
        markdown_file_path = sys.argv[1]
    else:
        # Default to the exigence_markdown.md file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        markdown_file_path = os.path.join(project_root, "data-parsed", "exigence_markdown.md")
    
    print(f"Reading file: {markdown_file_path}")
    print()
    
    # Read the markdown file
    content = read_markdown_file(markdown_file_path)
    
    # Parse the table
    data_rows, headers = parse_markdown_table(content)
    
    if not data_rows:
        print("No table data found or parsing failed.")
        return
    
    # Display the table line by line
    display_table_line_by_line(data_rows, headers)


if __name__ == "__main__":
    main()
