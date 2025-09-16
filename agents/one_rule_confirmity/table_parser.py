#!/usr/bin/env python3
"""
Script to read and parse the markdown table from exigence_markdown.md
Displays the table data line by line in a structured format.
"""

import os
import sys
from typing import List, Dict, Any


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


def parse_markdown_table(content: str) -> tuple:
    """
    Parse the markdown table content and extract structured data.
    This is a generic parser that works with any markdown table format.
    Handles both multi-line and single-line table formats.
    
    Args:
        content (str): Raw markdown content
        
    Returns:
        tuple: (data_rows, headers) - List of dictionaries containing table rows and headers
    """
    # Split content into lines
    lines = content.strip().split('\n')
    
    # Find the table content (skip title lines)
    table_content = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line contains table data (has | separators)
        if '|' in line:
            in_table = True
            table_content.append(line)
        elif in_table and not line.startswith('#'):
            # Continue collecting table lines until we hit non-table content
            break
    
    if not table_content:
        print("No table found in the content")
        return [], []
    
    # Handle single-line table format
    if len(table_content) == 1:
        return parse_single_line_table(table_content[0])
    
    # Parse multi-line table
    rows = []
    for line in table_content:
        # Split by | and clean up
        cells = [cell.strip() for cell in line.split('|')]
        # Remove empty cells at the beginning and end
        while cells and not cells[0]:
            cells.pop(0)
        while cells and not cells[-1]:
            cells.pop()
        if cells:  # Only add non-empty rows
            rows.append(cells)
    
    if len(rows) < 2:
        print("Table must have at least header and one data row")
        return [], []
    
    # First row is headers
    headers = rows[0]
    
    # Skip separator row (usually contains dashes)
    data_rows = []
    for i in range(1, len(rows)):
        row = rows[i]
        # Skip separator rows (rows with only dashes and spaces)
        if all(cell.replace('-', '').replace(' ', '') == '' for cell in row):
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


def parse_single_line_table(table_line: str) -> tuple:
    """
    Parse a single-line markdown table format.
    This handles complex single-line tables with varying column structures.
    
    Args:
        table_line (str): Single line containing the table
        
    Returns:
        tuple: (data_rows, headers) - List of dictionaries containing table rows and headers
    """
    # Split by | and clean up
    parts = [part.strip() for part in table_line.split('|') if part.strip()]
    
    if len(parts) < 6:  # Need at least title + 5 columns
        print("Single line table format not recognized")
        return [], []
    
    # Skip the title part (first part usually contains "Table" or similar)
    data_parts = parts[1:] if 'Table' in parts[0] else parts
    
    # Define headers based on the table structure
    headers = ['TOPIC', 'METRIC', 'CATEGORY', 'UNIT OF MEASURE', 'CODE']
    
    # For this specific table format, we need to manually parse the structure
    # The table has a specific pattern where topics are followed by their metrics
    data_rows = []
    
    # Find the start of actual data (skip header row and separator)
    data_start = 0
    for i, part in enumerate(data_parts):
        if 'Transparent Information' in part or 'FN-IN-270a.1' in part:
            data_start = i
            break
    
    if data_start == 0:
        # Fallback: try to find any meaningful data
        for i, part in enumerate(data_parts):
            if len(part) > 10 and not part.replace('-', '').replace(' ', ''):
                data_start = i
                break
    
    # Process the data starting from the identified start point
    remaining_parts = data_parts[data_start:]
    
    # Group data into logical rows based on the table structure
    # This is a heuristic approach for this specific table format
    i = 0
    while i < len(remaining_parts):
        # Look for the start of a new topic (long descriptive text)
        if i < len(remaining_parts) and len(remaining_parts[i]) > 20:
            # This might be a topic
            topic = remaining_parts[i]
            i += 1
            
            # Collect metrics for this topic
            while i < len(remaining_parts):
                if i + 4 < len(remaining_parts):
                    # Check if this looks like a complete row
                    metric = remaining_parts[i]
                    category = remaining_parts[i + 1]
                    unit = remaining_parts[i + 2]
                    code = remaining_parts[i + 3]
                    
                    # Create row data
                    row_data = {
                        'TOPIC': topic if len(metric) < 50 else '',  # Only set topic for first row of each topic group
                        'METRIC': metric,
                        'CATEGORY': category,
                        'UNIT OF MEASURE': unit,
                        'CODE': code
                    }
                    
                    # Only add if we have meaningful data
                    if any(value.strip() and not value.replace('-', '').replace(' ', '') == '' for value in row_data.values()):
                        data_rows.append(row_data)
                    
                    i += 4
                    
                    # Check if next part is a new topic
                    if i < len(remaining_parts) and len(remaining_parts[i]) > 20:
                        break
                else:
                    break
        else:
            i += 1
    
    return data_rows, headers


def display_table_line_by_line(data_rows: List[Dict[str, str]], headers: List[str]) -> None:
    """
    Display the table data line by line in a formatted way.
    
    Args:
        data_rows (List[Dict[str, str]]): List of table rows
        headers (List[str]): Table headers
    """
    print("=" * 120)
    print("MARKDOWN TABLE PARSER - LINE BY LINE DISPLAY")
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
