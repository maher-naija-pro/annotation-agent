#!/usr/bin/env python3
"""
Final Correlation Analyzer for Sustainability Disclosure Requirements
Analyzes Table 1 requirements against Table 2 data using both pattern matching and LLM.
"""

import sys
import os
import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# Add parent directory to path to import client modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from client.llm_client import create_client, chat_completion, get_config
    from client.config import get_all_config
    LLM_AVAILABLE = True
except ImportError:
    print("⚠️  LLM client not available, using pattern matching only")
    LLM_AVAILABLE = False


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
    method: str  # "pattern" or "llm"


class CorrelationAnalyzer:
    """Main class for analyzing correlations between requirements and data."""
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize the analyzer.
        
        Args:
            use_llm (bool): Whether to use LLM for correlation (if available)
        """
        self.use_llm = use_llm and LLM_AVAILABLE
        self.metrics: List[Metric] = []
        self.rapport_data: str = ""
        
        if self.use_llm:
            try:
                self.config = get_all_config()
                self.client = create_client(
                    endpoint_url=self.config['endpoint_url'],
                    model_name=self.config['model_name'],
                    api_key=self.config['api_key']
                )
                print("✅ LLM client initialized")
            except Exception as e:
                print(f"⚠️  LLM client initialization failed: {e}")
                print("   Falling back to pattern matching only")
                self.use_llm = False
        
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
        
        # The table is all on one line, so we need to split it properly
        # Find the table content after the header
        table_start = content.find('| TOPIC |')
        if table_start == -1:
            raise ValueError("Could not find table header in requirements file")
        
        table_content = content[table_start:]
        
        # Split by | to get all fields
        all_fields = [field.strip() for field in table_content.split('|')]
        
        # Remove empty fields and header fields
        data_fields = []
        for field in all_fields:
            if field in ['', 'TOPIC', 'METRIC', 'CATEGORY', 'UNIT OF MEASURE', 'CODE', '-------', '----------------------', '-----------------------------', '----------------']:
                continue
            if field.startswith('---'):
                continue
            data_fields.append(field)
        
        # Process fields by looking for patterns
        metrics = []
        i = 0
        while i < len(data_fields) - 4:
            # Look for a code pattern (FN-IN-xxx.x)
            if re.match(r'FN-IN-\d+[a-z]\.\d+', data_fields[i]):
                # This is a code, so the previous 4 fields should be topic, metric, category, unit
                if i >= 4:
                    topic = data_fields[i - 4]
                    metric = data_fields[i - 3]
                    category = data_fields[i - 2]
                    unit_standard = data_fields[i - 1]
                    code = data_fields[i]
                    
                    # Only process quantitative metrics
                    if category.lower() == "quantitative" and unit_standard.lower() != "n/a":
                        metrics.append(Metric(
                            topic=topic,
                            metric=metric,
                            category=category,
                            unit_standard=unit_standard,
                            code=code
                        ))
            i += 1
        
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
    
    def correlate_metric_with_patterns(self, metric: Metric) -> CorrelationResult:
        """
        Use pattern matching to correlate a metric with data from the rapport.
        
        Args:
            metric (Metric): The metric to correlate
            
        Returns:
            CorrelationResult: The correlation result
        """
        # Define patterns for different types of metrics
        patterns = {
            'emissions': [
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:millions?\s*de\s*tonnes?|tCO₂|tonnes?|t)',
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:tCO₂/M€|tCO₂/EURm)',
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:tCO₂/EURm)'
            ],
            'energy': [
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:GWh/EURm|GWh)',
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:%)'
            ],
            'percentage': [
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:%)'
            ],
            'currency': [
                r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:millions?\s*€|M€|EURm)'
            ]
        }
        
        # Determine which patterns to use based on metric content
        search_patterns = []
        if any(word in metric.metric.lower() for word in ['emission', 'carbon', 'co2', 'ghg']):
            search_patterns.extend(patterns['emissions'])
        if any(word in metric.metric.lower() for word in ['energy', 'electricity', 'power']):
            search_patterns.extend(patterns['energy'])
        if any(word in metric.metric.lower() for word in ['percentage', 'ratio', 'rate']):
            search_patterns.extend(patterns['percentage'])
        if any(word in metric.metric.lower() for word in ['monetary', 'premium', 'loss', 'exposure']):
            search_patterns.extend(patterns['currency'])
        
        # If no specific patterns, try all
        if not search_patterns:
            search_patterns = [p for pattern_list in patterns.values() for p in pattern_list]
        
        found_value = ""
        found_unit = ""
        unit_match = False
        
        # Search for patterns in the rapport data
        for pattern in search_patterns:
            matches = re.findall(pattern, self.rapport_data, re.IGNORECASE)
            if matches:
                # Take the first match
                found_value = matches[0]
                
                # Extract unit from the match context
                full_match = re.search(pattern, self.rapport_data, re.IGNORECASE)
                if full_match:
                    match_text = full_match.group(0)
                    # Extract unit part
                    unit_part = match_text.replace(found_value, '').strip()
                    found_unit = unit_part
                    
                    # Check if unit matches standard unit
                    standard_unit = metric.unit_standard.lower()
                    actual_unit = found_unit.lower()
                    
                    # Normalize units for comparison
                    unit_mappings = {
                        'metric tonnes (t) co₂-e': ['tco₂', 'tonnes', 't', 'millions de tonnes'],
                        'presentation currency': ['€', 'm€', 'eurm', 'millions €'],
                        'percentage %': ['%'],
                        'rate': ['%', 'ratio']
                    }
                    
                    # Check for unit match
                    for standard, variants in unit_mappings.items():
                        if standard_unit in standard:
                            if any(variant in actual_unit for variant in variants):
                                unit_match = True
                                break
                
                break
        
        # Special case: if we found emissions data but the metric is not about emissions, don't match it
        if found_value and 'emission' in found_unit.lower() and 'emission' not in metric.metric.lower():
            found_value = ""
            found_unit = ""
            unit_match = False
        
        return CorrelationResult(
            topic=metric.topic,
            metric=metric.metric,
            code=metric.code,
            value=found_value,
            unit_actual=found_unit,
            unit_standard=metric.unit_standard,
            unit_match=unit_match,
            method="pattern"
        )
    
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
            unit_match=result.get("unit_match", False),
            method="llm"
        )
    
    def correlate_metric(self, metric: Metric) -> CorrelationResult:
        """
        Correlate a metric using the best available method.
        
        Args:
            metric (Metric): The metric to correlate
            
        Returns:
            CorrelationResult: The correlation result
        """
        if self.use_llm:
            return self.correlate_metric_with_llm(metric)
        else:
            return self.correlate_metric_with_patterns(metric)
    
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
            result = self.correlate_metric(metric)
            results.append(result)
            print(f"   {'✅' if result.unit_match else '❌'} Unit match: {result.unit_match} ({result.method})")
            if result.value:
                print(f"   Found: {result.value} {result.unit_actual}")
        
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
            table += "| Topic | Metric | Code | Value | Unit (Actual) | Unit (Standard) | Unit Match | Method |\n"
            table += "|-------|--------|------|-------|---------------|-----------------|------------|--------|\n"
            
            for result in results:
                value = result.value if result.value else "NC"
                unit_actual = result.unit_actual if result.unit_actual else "NC"
                unit_match = "TRUE" if result.unit_match else "FALSE"
                
                # Truncate long text for table display
                topic = result.topic[:50] + "..." if len(result.topic) > 50 else result.topic
                metric = result.metric[:50] + "..." if len(result.metric) > 50 else result.metric
                
                table += f"| {topic} | {metric} | {result.code} | {value} | {unit_actual} | {result.unit_standard} | {unit_match} | {result.method} |\n"
            
            return table
        
        matching_table = create_table(matching_results, "Metrics with Matching Units")
        non_matching_table = create_table(non_matching_results, "Metrics with Non-Matching Units")
        
        print(f"✅ Generated tables: {len(matching_results)} matching, {len(non_matching_results)} non-matching")
        return matching_table, non_matching_table
    
    def save_results(self, results: List[CorrelationResult], matching_table: str, non_matching_table: str, output_file: str = "correlation_results.md"):
        """
        Save the results to a markdown file.
        
        Args:
            results (List[CorrelationResult]): List of correlation results
            matching_table (str): Markdown table for matching units
            non_matching_table (str): Markdown table for non-matching units
            output_file (str): Output file path
        """
        print(f"💾 Saving results to {output_file}...")
        
        # Count matching and non-matching results
        matching_count = len([r for r in results if r.unit_match])
        non_matching_count = len([r for r in results if not r.unit_match])
        
        # Count by method
        pattern_count = len([r for r in results if r.method == "pattern"])
        llm_count = len([r for r in results if r.method == "llm"])
        
        content = f"""# Sustainability Disclosure Correlation Analysis

This analysis correlates the requirements from Table 1 with data from Table 2 (rapport).

## Summary

- **Total metrics analyzed**: {len(results)}
- **Metrics with matching units**: {matching_count}
- **Metrics with non-matching units**: {non_matching_count}
- **Analysis method**: {"LLM + Pattern Matching" if self.use_llm else "Pattern Matching Only"}
- **Pattern matching results**: {pattern_count}
- **LLM results**: {llm_count}

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
    print("=" * 70)
    
    # Initialize analyzer (try LLM first, fallback to pattern matching)
    analyzer = CorrelationAnalyzer(use_llm=True)
    
    # File paths
    requirements_file = "../data-parsed/exigence_markdown.md"
    rapport_file = "../data-parsed/rapport.md"
    output_file = "correlation_results_final.md"
    
    try:
        # Run analysis
        results = analyzer.analyze_correlations(requirements_file, rapport_file)
        
        # Generate tables
        matching_table, non_matching_table = analyzer.generate_markdown_tables(results)
        
        # Save results
        analyzer.save_results(results, matching_table, non_matching_table, output_file)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"Total metrics analyzed: {len(results)}")
        print(f"Metrics with matching units: {len([r for r in results if r.unit_match])}")
        print(f"Metrics with non-matching units: {len([r for r in results if not r.unit_match])}")
        print(f"Results saved to: {output_file}")
        
        # Print detailed results
        print("\n📋 DETAILED RESULTS:")
        print("-" * 70)
        for result in results:
            status = "✅ MATCH" if result.unit_match else "❌ NO MATCH"
            value_info = f"Value: {result.value} {result.unit_actual}" if result.value else "No value found"
            print(f"{result.code}: {status} - {value_info} ({result.method})")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
