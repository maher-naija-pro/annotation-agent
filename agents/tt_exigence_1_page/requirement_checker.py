
#!/usr/bin/env python3
"""
Simple script to read JSON file and display each row from the table data.
This script reads the page_006.json file and iterates through each row in the table.
"""

import json
import os
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add the project root to the path to import the LLM client
# Get the absolute path to the project root (two levels up from this file)
script_dir = Path(__file__).resolve().parent
project_root = str(script_dir.parent.parent)
sys.path.insert(0, project_root)

from client.llm_client import create_client, simple_query, get_config


def read_rapport_data(rapport_path: str) -> str:
    """
    Read the rapport.md file content.
    
    Args:
        rapport_path (str): Path to the rapport.md file
        
    Returns:
        str: Content of the rapport file
    """
    try:
        with open(rapport_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: Rapport file not found at {rapport_path}")
        return ""
    except Exception as e:
        print(f"Error reading rapport file: {e}")
        return ""


def create_conformity_prompt(rapport_content: str, requirement_text: str) -> str:
    """
    Create a prompt for the LLM to check conformity between requirements and rapport data.
    
    Args:
        rapport_content (str): Content from the rapport.md file
        requirement_text (str): The requirement text to check against
        
    Returns:
        str: Formatted prompt for the LLM
    """
    prompt = f"""
You are an expert in regulatory compliance and ESG (Environmental, Social, Governance) reporting.

REQUIREMENT TO CHECK:
{requirement_text}

RAPPORT DATA TO ANALYZE:
{rapport_content}

Your task is to extract and structure regulatory compliance data from the rapport content according to the given requirement. 

You must output your results in the following CSV format with these exact columns:

CID,Industry,Topic,Metric,Code,Page,Heading or Fragment,Value,Unit,SASB Unit of Measurement,Complete

COLUMN DEFINITIONS:

1. Topic: The main topic category from the requirement
2. Metric: The specific metric being measured from the requirement
3. Code: The regulatory code reference from the requirement
4. Heading or Fragment: The specific text fragment that contains the relevant information
5. Value: The numerical value if applicable. Use "N/A" if no numerical value is present.
6. Unit: The unit of measurement. Use "N/A" if no unit applies.
7. SASB Unit of Measurement: The standardized SASB unit. Use "N/A" if not applicable.
8. Complete: Boolean value indicating if the data extraction is complete ("TRUE" or "FALSE")

EXTRACTION GUIDELINES:
- Extract data that matches the requirement topic and metric
- Preserve original text formatting including line breaks within cells
- Use proper CSV escaping for commas and quotes
- Extract numerical values exactly as they appear
- Include units in the Value field when they appear with the number
- Mark as "TRUE" when  unit and SASB Unit of Measurement are equal
- Mark as "FALSE" when data is partial or missing key elements

OUTPUT FORMAT:
Start your response with the CSV extracted data rows. If no relevant data is found, output no data.

Example output:
Topic,Metric,Code,Heading or Fragment,Value,Unit,SASB Unit of Measurement,Complete
Financed Emissions,Absolute gross financed emissions,FN-IN-410c.1,8,"Les émissions induites totales s'élèvent à 3,472 millions de tonnes de CO2","3,472 millions",tonnes de CO2,tonnes de CO2,TRUE

Focus on:
- Whether the required data is present in the rapport
- If the data format and units match expectations
- If the values are within acceptable ranges
- Any missing or incomplete information
- Proper CSV formatting and escaping
- dont explain the result, just return the result
"""
    return prompt



def check_conformity(requirement_text: str, rapport_path: str = None) -> str:
    """
    Check conformity of a requirement against the rapport data using LLM.
    
    Args:
        requirement_text (str): The requirement text to check
        rapport_path (str, optional): Path to rapport.md file. Defaults to data-parsed/manuel/rapport.md
        
    Returns:
        str: LLM response with conformity analysis
    """
    # Set default rapport path if not provided
    if rapport_path is None:
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent
        rapport_path = str(project_root / "data-parsed" / "manuel" / "rapport.md")
    
    # Read rapport data
    print(f"Reading rapport data from: {rapport_path}")
    rapport_content = read_rapport_data(rapport_path)
    
    if not rapport_content:
        return "Error: Could not read rapport data"
    
    # Get LLM configuration
    config = get_config()
    
    # Create LLM client
    print(f"Connecting to LLM at: {config['endpoint_url']}")
    print(f"Using model: {config['model_name']}")
    
    client = create_client(
        endpoint_url=config['endpoint_url'],
        model_name=config['model_name'],
        api_key=config['api_key']
    )
    
    # Create conformity check prompt
    prompt = create_conformity_prompt(rapport_content, requirement_text)
    
    # Query the LLM
    print("Sending conformity check request to LLM...")
    response = simple_query(
        client=client,
        model_name=config['model_name'],
        prompt=prompt,
        temperature=0.1,  # Lower temperature for more consistent analysis
        max_tokens=2000
    )
    
    return response



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

def iterate_on_requirements_check(data: Dict[str, Any]) -> List[str]:
    """
    Iterate through each row and display it in a formatted way.
    
    Args:
        data (Dict[str, Any]): JSON data containing table rows
        
    Returns:
        List[str]: List of conformity check results for each row
    """
    if not data or 'data' not in data or 'table' not in data['data']:
        print("No table data found.")
        return []
    
    table = data['data']['table']
    rows = table.get('rows', [])
    columns = table.get('columns', [])
    
    if not rows:
        print("No rows found in the table.")
        return []
    
    print("\n" + "=" * 80)
    
    # List to store all results
    all_results = []
    
    for i, row in enumerate(rows, 1):
        print(f"\n--- ROW {i} ---")
        # Check conformity
        print(row)
        result = check_conformity(row)
        print(result)
        # Store the result
        all_results.append(result)
    
    return all_results


  
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

    # Display all rows and get results
    results = iterate_on_requirements_check(data)
    

    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")

    print(f"Total results: {len(results)}")
    print(results)
    print("=" * 80)
    


if __name__ == "__main__":
    main()
