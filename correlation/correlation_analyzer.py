#!/usr/bin/env python3
"""
Correlation Analyzer for Sustainability Disclosure Requirements
Analyzes Table 1 requirements against Table 2 data using LLM correlation.
"""

import sys
import os
import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# Add parent directory to path to import client modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.llm_client import create_client, chat_completion, get_config
from client.config import get_all_config


@dataclass
class Metric:
    """Represents a metric from Table 1."""
    topic: str
    metric: str
    category: str
    unit_standard: str
    code: str


@dataclass
class CorrelationResult:
    """Represents the correlation result for a metric."""
    topic: str
    metric: str
    code: str
    value: str
    unit_actual: str
    unit_standard: str
    unit_match: bool


class CorrelationAnalyzer:
    """Main class for analyzing correlations between requirements and data."""
    
    def __init__(self):
        """Initialize the analyzer with LLM client."""
        self.config = get_all_config()
        self.client = create_client(
            endpoint_url=self.config['endpoint_url'],
            model_name=self.config['model_name'],
            api_key=self.config['api_key']
        )
        self.metrics: List[Metric] = []
        self.rapport_data: str = ""
        
    def parse_requirements_table(self, file_path: str) -> List[Metric]:
        """
        Parse the requirements table from the markdown file.
        
        Args:
            file_path (str): Path to the requirements markdown file
            
        Returns:
            List[Metric]: List of parsed metrics
        """
        print("📋 Parsing requirements table...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract table content using regex
        table_match = re.search(r'\|.*?\|.*?\|.*?\|.*?\|.*?\|', content, re.DOTALL)
        if not table_match:
            raise ValueError("Could not find table in requirements file")
        
        table_content = table_match.group(0)
        lines = [line.strip() for line in table_content.split('\n') if line.strip() and '|' in line]
        
        # Skip header lines (lines with only separators or headers)
        data_lines = []
        for line in lines:
            if not re.match(r'^\|[\s\-\|]*\|$', line) and 'TOPIC' not in line.upper():
                data_lines.append(line)
        
        metrics = []
        for line in data_lines:
            if not line or line.count('|') < 4:
                continue
                
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 5:
                topic = parts[1] if len(parts) > 1 else ""
                metric = parts[2] if len(parts) > 2 else ""
                category = parts[3] if len(parts) > 3 else ""
                unit_standard = parts[4] if len(parts) > 4 else ""
                code = parts[5] if len(parts) > 5 else ""
                
                # Only process quantitative metrics
                if category.lower() == "quantitative" and unit_standard.lower() != "n/a":
                    metrics.append(Metric(
                        topic=topic,
                        metric=metric,
                        category=category,
                        unit_standard=unit_standard,
                        code=code
                    ))
        
        print(f"✅ Parsed {len(metrics)} quantitative metrics from requirements table")
        return metrics
    
    def load_rapport_data(self, file_path: str) -> str:
        """
        Load the rapport data from the markdown file.
        
        Args:
            file_path (str): Path to the rapport markdown file
            
        Returns:
            str: Content of the rapport file
        """
        print("📄 Loading rapport data...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Loaded rapport data ({len(content)} characters)")
        return content
    
    def correlate_metric_with_llm(self, metric: Metric) -> CorrelationResult:
        """
        Use LLM to correlate a metric with data from the rapport.
        
        Args:
            metric (Metric): The metric to correlate
            
        Returns:
            CorrelationResult: The correlation result
        """
        prompt = f"""
You are analyzing a sustainability report to find data that corresponds to a specific metric requirement.

REQUIREMENT TO FIND:
- Topic: {metric.topic}
- Metric: {metric.metric}
- Standard Unit: {metric.unit_standard}
- Code: {metric.code}

REPORT DATA TO SEARCH IN:
{self.rapport_data}

TASK:
1. Search for any data in the report that corresponds to this metric requirement
2. Extract the actual value and unit if found
3. Compare the actual unit with the standard unit
4. Return your findings in JSON format

RESPONSE FORMAT (JSON only):
{{
    "found": true/false,
    "value": "actual value found or empty string",
    "unit_actual": "actual unit found or empty string",
    "unit_match": true/false,
    "explanation": "brief explanation of what was found or why nothing was found"
}}

IMPORTANT:
- Only return valid JSON
- If no matching data is found, set "found" to false and leave value/unit_actual empty
- Be precise about units (e.g., "tCO₂", "EURm", "GWh", "%", etc.)
- Look for similar concepts even if wording differs slightly
"""

        try:
            messages = [
                {"role": "system", "content": "You are an expert at analyzing sustainability reports and correlating metrics with data. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ]
            
            response = chat_completion(
                self.client, 
                self.config['model_name'], 
                messages, 
                temperature=0.1,
                max_tokens=1000
            )
            
            if response['success']:
                # Extract JSON from response
                content = response['content'].strip()
                
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    result = {
                        "found": False,
                        "value": "",
                        "unit_actual": "",
                        "unit_match": False,
                        "explanation": "Could not parse LLM response"
                    }
            else:
                result = {
                    "found": False,
                    "value": "",
                    "unit_actual": "",
                    "unit_match": False,
                    "explanation": f"LLM error: {response['error']}"
                }
                
        except Exception as e:
            result = {
                "found": False,
                "value": "",
                "unit_actual": "",
                "unit_match": False,
                "explanation": f"Error: {str(e)}"
            }
        
        return CorrelationResult(
            topic=metric.topic,
            metric=metric.metric,
            code=metric.code,
            value=result.get("value", ""),
            unit_actual=result.get("unit_actual", ""),
            unit_standard=metric.unit_standard,
            unit_match=result.get("unit_match", False)
        )
    
    def analyze_correlations(self, requirements_file: str, rapport_file: str) -> List[CorrelationResult]:
        """
        Analyze correlations between requirements and rapport data.
        
        Args:
            requirements_file (str): Path to requirements markdown file
            rapport_file (str): Path to rapport markdown file
            
        Returns:
            List[CorrelationResult]: List of correlation results
        """
        print("🔍 Starting correlation analysis...")
        
        # Parse requirements
        self.metrics = self.parse_requirements_table(requirements_file)
        
        # Load rapport data
        self.rapport_data = self.load_rapport_data(rapport_file)
        
        # Correlate each metric
        results = []
        for i, metric in enumerate(self.metrics, 1):
            print(f"📊 Analyzing metric {i}/{len(self.metrics)}: {metric.code}")
            result = self.correlate_metric_with_llm(metric)
            results.append(result)
            print(f"   {'✅' if result.unit_match else '❌'} Unit match: {result.unit_match}")
        
        print(f"✅ Completed analysis of {len(results)} metrics")
        return results
    
    def generate_markdown_tables(self, results: List[CorrelationResult]) -> Tuple[str, str]:
        """
        Generate markdown tables for matching and non-matching units.
        
        Args:
            results (List[CorrelationResult]): List of correlation results
            
        Returns:
            Tuple[str, str]: (matching_table, non_matching_table)
        """
        print("📋 Generating markdown tables...")
        
        # Split results into matching and non-matching
        matching_results = [r for r in results if r.unit_match]
        non_matching_results = [r for r in results if not r.unit_match]
        
        def create_table(results: List[CorrelationResult], title: str) -> str:
            """Create a markdown table from results."""
            if not results:
                return f"## {title}\n\nNo metrics found.\n"
            
            table = f"## {title}\n\n"
            table += "| Topic | Metric | Code | Value | Unit (Actual) | Unit (Standard) | Unit Match |\n"
            table += "|-------|--------|------|-------|---------------|-----------------|------------|\n"
            
            for result in results:
                value = result.value if result.value else "NC"
                unit_actual = result.unit_actual if result.unit_actual else "NC"
                unit_match = "TRUE" if result.unit_match else "FALSE"
                
                # Truncate long text for table display
                topic = result.topic[:50] + "..." if len(result.topic) > 50 else result.topic
                metric = result.metric[:50] + "..." if len(result.metric) > 50 else result.metric
                
                table += f"| {topic} | {metric} | {result.code} | {value} | {unit_actual} | {result.unit_standard} | {unit_match} |\n"
            
            return table
        
        matching_table = create_table(matching_results, "Metrics with Matching Units")
        non_matching_table = create_table(non_matching_results, "Metrics with Non-Matching Units")
        
        print(f"✅ Generated tables: {len(matching_results)} matching, {len(non_matching_results)} non-matching")
        return matching_table, non_matching_table
    
    def save_results(self, matching_table: str, non_matching_table: str, output_file: str = "correlation_results.md"):
        """
        Save the results to a markdown file.
        
        Args:
            matching_table (str): Markdown table for matching units
            non_matching_table (str): Markdown table for non-matching units
            output_file (str): Output file path
        """
        print(f"💾 Saving results to {output_file}...")
        
        content = f"""# Sustainability Disclosure Correlation Analysis

This analysis correlates the requirements from Table 1 with data from Table 2 (rapport).

## Summary

- **Total metrics analyzed**: {len(self.metrics)}
- **Metrics with matching units**: {len([r for r in self.metrics if r.unit_match])}
- **Metrics with non-matching units**: {len([r for r in self.metrics if not r.unit_match])}

{matching_table}

{non_matching_table}

---
*Generated by Correlation Analyzer*
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Results saved to {output_file}")


def main():
    """Main function to run the correlation analysis."""
    print("🚀 Starting Sustainability Disclosure Correlation Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = CorrelationAnalyzer()
    
    # File paths
    requirements_file = "../data-parsed/exigence_markdown.md"
    rapport_file = "../data-parsed/rapport.md"
    output_file = "correlation_results.md"
    
    try:
        # Run analysis
        results = analyzer.analyze_correlations(requirements_file, rapport_file)
        
        # Generate tables
        matching_table, non_matching_table = analyzer.generate_markdown_tables(results)
        
        # Save results
        analyzer.save_results(matching_table, non_matching_table, output_file)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total metrics analyzed: {len(results)}")
        print(f"Metrics with matching units: {len([r for r in results if r.unit_match])}")
        print(f"Metrics with non-matching units: {len([r for r in results if not r.unit_match])}")
        print(f"Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
