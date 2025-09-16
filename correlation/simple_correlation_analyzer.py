#!/usr/bin/env python3
"""
Simple Correlation Analyzer for Sustainability Disclosure Requirements
Analyzes Table 1 requirements against Table 2 data without LLM dependency.
This version uses pattern matching instead of LLM for demonstration.
"""

import sys
import os
import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


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


class SimpleCorrelationAnalyzer:
    """Simple analyzer using pattern matching instead of LLM."""
    
    def __init__(self):
        """Initialize the analyzer."""
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
        
        # The table is all on one line, so we need to split it properly
        # Find the table content after the header
        table_start = content.find('| TOPIC |')
        if table_start == -1:
            raise ValueError("Could not find table header in requirements file")
        
        table_content = content[table_start:]
        
        # Split by | and process each row
        # First, let's find all the data rows by looking for patterns
        metrics = []
        
        # Split the content by | to get all fields
        all_fields = [field.strip() for field in table_content.split('|')]
        
        # Remove empty fields and header fields
        data_fields = []
        skip_next = False
        for i, field in enumerate(all_fields):
            if skip_next:
                skip_next = False
                continue
            if field in ['', 'TOPIC', 'METRIC', 'CATEGORY', 'UNIT OF MEASURE', 'CODE', '-------', '----------------------', '-----------------------------', '----------------']:
                continue
            if field.startswith('---'):
                continue
            data_fields.append(field)
        
        # Debug output removed for cleaner execution
        
        # Process fields by looking for patterns
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
                        print(f"   Added metric: {code} - {metric[:50]}...")
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
            unit_match=unit_match
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
            result = self.correlate_metric_with_patterns(metric)
            results.append(result)
            print(f"   {'✅' if result.unit_match else '❌'} Unit match: {result.unit_match}")
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
        
        content = f"""# Sustainability Disclosure Correlation Analysis

This analysis correlates the requirements from Table 1 with data from Table 2 (rapport).

## Summary

- **Total metrics analyzed**: {len(results)}
- **Metrics with matching units**: {matching_count}
- **Metrics with non-matching units**: {non_matching_count}

{matching_table}

{non_matching_table}

---
*Generated by Simple Correlation Analyzer*
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Results saved to {output_file}")


def main():
    """Main function to run the correlation analysis."""
    print("🚀 Starting Simple Sustainability Disclosure Correlation Analysis")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = SimpleCorrelationAnalyzer()
    
    # File paths
    requirements_file = "../data-parsed/exigence_markdown.md"
    rapport_file = "../data-parsed/rapport.md"
    output_file = "simple_correlation_results.md"
    
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
            print(f"{result.code}: {status} - {value_info}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
