#!/usr/bin/env python3
"""
Simple conformity checker script that uses LLM to check requirements against rapport data.
This script reads the rapport.md file and uses the LLM client to check conformity.
"""

import os
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
Start your response with the CSV header row, then provide the extracted data rows. If no relevant data is found, output only the header row.

Example output:
Topic,Metric,Code,Heading or Fragment,Value,Unit,SASB Unit of Measurement,Complete
Financed Emissions,Absolute gross financed emissions,FN-IN-410c.1,8,"Les émissions induites totales s'élèvent à 3,472 millions de tonnes de CO2","3,472 millions",tonnes de CO2,tonnes de CO2,TRUE

Focus on:
- Whether the required data is present in the rapport
- If the data format and units match expectations
- If the values are within acceptable ranges
- Any missing or incomplete information
- Proper CSV formatting and escaping
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


def main():
    """
    Main function to run the conformity checker.
    """
    print("=== ESG Rapport Conformity Checker ===\n")
    
    # Example requirement text (you can modify this)
    requirement_text = """
    TOPIC: Financed Emissions
    METRIC: Absolute gross financed emissions, disaggregated by (1) Scope 1, (2) Scope 2, and (3) Scope 3
    CATEGORY: Quantitative
    UNIT OF MEASURE: Metric tonnes (t) CO2-e     
    CODE: FN-IN-410c.1
    """
    
    print("REQUIREMENT TO CHECK:")
    print(requirement_text)
    print("\n" + "="*50 + "\n")
    
    # Check conformity
    result = check_conformity(requirement_text)
    
    print("EXTRACTED DATA IN CSV FORMAT:")
    print("="*50)
    print(result)
    print("\n" + "="*50)
    print("Note: The output above should be in CSV format with columns:")
    print("CID,Industry,Topic,Metric,Code,Page,Heading or Fragment,Value,Unit,SASB Unit of Measurement,Complete")


if __name__ == "__main__":
    main()
