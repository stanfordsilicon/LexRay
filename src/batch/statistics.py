# -*- coding: utf-8 -*-
"""
Statistics and reporting utilities for CLDR Date Skeleton Converter

Analyzes batch processing results and generates frequency analysis
and pattern distribution reports.
"""

import csv
import json
import pandas as pd
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any
from pathlib import Path


class SkeletonAnalyzer:
    """
    Analyzes skeleton patterns and generates statistics.
    """
    
    def __init__(self, results_file: str):
        """
        Initialize the analyzer with results file.
        
        Args:
            results_file (str): Path to batch processing results CSV
        """
        self.results_file = results_file
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Load and parse the results data."""
        try:
            self.data = pd.read_csv(self.results_file)
            print(f"Loaded {len(self.data)} rows from {self.results_file}")
        except Exception as e:
            raise ValueError(f"Failed to load results file: {e}")
    
    def analyze_skeleton_frequencies(self) -> Dict[str, Any]:
        """
        Analyze frequency of skeleton patterns.
        
        Returns:
            dict: Frequency analysis results
        """
        if self.data is None or len(self.data) == 0:
            return {}
        
        # Count English skeleton frequencies
        english_skeletons = self.data['ENGLISH_SKELETON'].dropna()
        english_freq = Counter(english_skeletons)
        
        # Count target skeleton frequencies
        target_skeletons = self.data['TARGET_SKELETON'].dropna()
        target_freq = Counter(target_skeletons)
        
        # Analyze skeleton components
        english_components = self._analyze_skeleton_components(english_skeletons)
        target_components = self._analyze_skeleton_components(target_skeletons)
        
        return {
            'english_skeleton_frequencies': dict(english_freq.most_common()),
            'target_skeleton_frequencies': dict(target_freq.most_common()),
            'english_component_analysis': english_components,
            'target_component_analysis': target_components,
            'total_english_patterns': len(english_freq),
            'total_target_patterns': len(target_freq),
            'total_rows': len(self.data)
        }
    
    def _analyze_skeleton_components(self, skeletons: pd.Series) -> Dict[str, Any]:
        """
        Analyze individual components within skeletons.
        
        Args:
            skeletons (pd.Series): Series of skeleton strings
            
        Returns:
            dict: Component analysis results
        """
        # Extract individual components
        all_components = []
        literal_texts = []
        
        for skeleton in skeletons:
            if pd.isna(skeleton):
                continue
            
            # Split by spaces and analyze each component
            components = skeleton.split()
            for component in components:
                all_components.append(component)
                
                # Check for literal text (quoted)
                if component.startswith("'") and component.endswith("'"):
                    literal_texts.append(component)
        
        # Count component frequencies
        component_freq = Counter(all_components)
        literal_freq = Counter(literal_texts)
        
        # Categorize components
        date_elements = [c for c in component_freq.keys() if any(char in c for char in 'MLdyEc')]
        punctuation = [c for c in component_freq.keys() if c in [',', '-', '–', '/', '.']]
        literals = [c for c in component_freq.keys() if c.startswith("'") and c.endswith("'")]
        
        return {
            'component_frequencies': dict(component_freq.most_common()),
            'date_element_frequencies': {k: component_freq[k] for k in date_elements},
            'punctuation_frequencies': {k: component_freq[k] for k in punctuation},
            'literal_text_frequencies': dict(literal_freq.most_common()),
            'total_unique_components': len(component_freq),
            'total_literal_texts': len(literal_freq)
        }
    
    def analyze_format_lengths(self) -> Dict[str, Any]:
        """
        Analyze distribution of format lengths (wide, abbreviated, narrow).
        
        Returns:
            dict: Format length analysis
        """
        if self.data is None or len(self.data) == 0:
            return {}
        
        english_lengths = defaultdict(int)
        target_lengths = defaultdict(int)
        
        # Analyze English skeletons
        for skeleton in self.data['ENGLISH_SKELETON'].dropna():
            lengths = self._extract_format_lengths(skeleton)
            for length_type in lengths:
                english_lengths[length_type] += 1
        
        # Analyze target skeletons
        for skeleton in self.data['TARGET_SKELETON'].dropna():
            lengths = self._extract_format_lengths(skeleton)
            for length_type in lengths:
                target_lengths[length_type] += 1
        
        return {
            'english_format_lengths': dict(english_lengths),
            'target_format_lengths': dict(target_lengths)
        }
    
    def _extract_format_lengths(self, skeleton: str) -> List[str]:
        """
        Extract format length types from a skeleton.
        
        Args:
            skeleton (str): Skeleton string
            
        Returns:
            list: List of format length types found
        """
        lengths = []
        
        # Month format lengths
        if 'MMMM' in skeleton:
            lengths.append('month_wide')
        if 'MMM' in skeleton:
            lengths.append('month_abbreviated')
        if 'M' in skeleton and 'MMM' not in skeleton and 'MMMM' not in skeleton:
            lengths.append('month_narrow')
        
        # Day format lengths
        if 'cccc' in skeleton:
            lengths.append('day_wide')
        if 'ccc' in skeleton:
            lengths.append('day_abbreviated')
        if 'c' in skeleton and 'ccc' not in skeleton and 'cccc' not in skeleton:
            lengths.append('day_narrow')
        
        return lengths
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report.
        
        Returns:
            dict: Complete analysis report
        """
        frequency_analysis = self.analyze_skeleton_frequencies()
        format_analysis = self.analyze_format_lengths()
        
        # Calculate success rates
        total_rows = len(self.data)
        successful_english = len(self.data['ENGLISH_SKELETON'].dropna())
        successful_target = len(self.data['TARGET_SKELETON'].dropna())
        
        return {
            'summary': {
                'total_rows': total_rows,
                'successful_english_processing': successful_english,
                'successful_target_processing': successful_target,
                'english_success_rate': successful_english / total_rows if total_rows > 0 else 0,
                'target_success_rate': successful_target / total_rows if total_rows > 0 else 0
            },
            'frequency_analysis': frequency_analysis,
            'format_analysis': format_analysis
        }
    
    def export_report(self, output_file: str, format: str = 'json'):
        """
        Export analysis report to file.
        
        Args:
            output_file (str): Output file path
            format (str): Export format ('json', 'csv', 'txt')
        """
        report = self.generate_summary_report()
        
        if format.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'csv':
            # Export frequency data as CSV
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write summary
                writer.writerow(['Metric', 'Value'])
                for key, value in report['summary'].items():
                    writer.writerow([key, value])
                
                writer.writerow([])  # Empty row
                
                # Write English skeleton frequencies
                writer.writerow(['English Skeleton', 'Frequency'])
                for skeleton, freq in report['frequency_analysis']['english_skeleton_frequencies'].items():
                    writer.writerow([skeleton, freq])
                
                writer.writerow([])  # Empty row
                
                # Write target skeleton frequencies
                writer.writerow(['Target Skeleton', 'Frequency'])
                for skeleton, freq in report['frequency_analysis']['target_skeleton_frequencies'].items():
                    writer.writerow([skeleton, freq])
        
        elif format.lower() == 'txt':
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("CLDR Date Skeleton Analysis Report\n")
                f.write("=" * 40 + "\n\n")
                
                # Summary
                f.write("SUMMARY\n")
                f.write("-" * 10 + "\n")
                for key, value in report['summary'].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                
                # English frequencies
                f.write("ENGLISH SKELETON FREQUENCIES\n")
                f.write("-" * 30 + "\n")
                for skeleton, freq in report['frequency_analysis']['english_skeleton_frequencies'].items():
                    f.write(f"{skeleton}: {freq}\n")
                f.write("\n")
                
                # Target frequencies
                f.write("TARGET SKELETON FREQUENCIES\n")
                f.write("-" * 30 + "\n")
                for skeleton, freq in report['frequency_analysis']['target_skeleton_frequencies'].items():
                    f.write(f"{skeleton}: {freq}\n")
        
        print(f"Report exported to: {output_file}")


def analyze_batch_results(results_file: str, output_file: str = None, format: str = 'json'):
    """
    Convenience function to analyze batch results.
    
    Args:
        results_file (str): Path to batch processing results CSV
        output_file (str): Output file path (auto-generated if None)
        format (str): Export format ('json', 'csv', 'txt')
    """
    analyzer = SkeletonAnalyzer(results_file)
    
    if output_file is None:
        results_path = Path(results_file)
        
        # If results are in testing/trial_YYYYMMDD_HHMMSS/output/, keep analysis in same directory
        if 'testing/trial_' in str(results_path) or 'testing\\trial_' in str(results_path):
            output_file = results_path.parent / f"{results_path.stem}_analysis.{format}"
        else:
            # Default behavior: output in same directory as results
            output_file = results_path.parent / f"{results_path.stem}_analysis.{format}"
    
    analyzer.export_report(output_file, format)
    return output_file 