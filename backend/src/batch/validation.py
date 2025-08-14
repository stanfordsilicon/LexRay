# -*- coding: utf-8 -*-
"""
Validation utilities for CLDR Date Skeleton Converter

Compares generated skeletons against verified ground truth skeletons
and provides accuracy metrics and detailed analysis.
"""

import csv
import pandas as pd
from typing import Dict, List, Tuple, Any
from pathlib import Path
import json


class SkeletonValidator:
    """
    Validates generated skeletons against verified ground truth.
    """
    
    def __init__(self, results_file: str, verified_file: str):
        """
        Initialize the validator with results and verified files.
        
        Args:
            results_file (str): Path to batch processing results CSV
            verified_file (str): Path to verified skeletons CSV in meta_data
        """
        self.results_file = results_file
        self.verified_file = verified_file
        self.results_data = None
        self.verified_data = None
        self.load_data()
    
    def load_data(self):
        """Load and parse the results and verified data."""
        try:
            self.results_data = pd.read_csv(self.results_file)
            self.verified_data = pd.read_csv(self.verified_file)
            print(f"Loaded {len(self.results_data)} results and {len(self.verified_data)} verified entries")
        except Exception as e:
            raise ValueError(f"Failed to load data files: {e}")
    
    def compare_skeletons(self, generated: str, verified: str) -> Dict[str, Any]:
        """
        Compare generated skeleton against verified skeleton.
        
        Args:
            generated (str): Generated skeleton string
            verified (str): Verified skeleton string
            
        Returns:
            dict: Comparison results
        """
        if pd.isna(generated) or pd.isna(verified):
            return {
                'exact_match': False,
                'partial_match': False,
                'contains_verified': False,
                'verified_contains_generated': False,
                'similarity_score': 0.0,
                'differences': ['Missing data']
            }
        
        # Normalize both strings: convert commas to semicolons for consistent comparison
        generated_normalized = generated.replace(', ', '; ')
        verified_normalized = verified.replace(', ', '; ')
        
        # Split both into individual options
        generated_options = [opt.strip() for opt in generated_normalized.split(';')]
        verified_options = [opt.strip() for opt in verified_normalized.split(';')]
        
        # Check for exact match: any generated option matches any verified option
        exact_match = any(gen_opt in verified_options for gen_opt in generated_options)
        
        # Check if any generated option contains any verified option
        contains_verified = any(any(ver_opt in gen_opt for ver_opt in verified_options) for gen_opt in generated_options)
        
        # Check if any verified option contains any generated option
        verified_contains_generated = any(any(gen_opt in ver_opt for gen_opt in generated_options) for ver_opt in verified_options)
        
        # Calculate similarity score (simple approach)
        max_similarity = 0.0
        best_match = None
        
        for gen_opt in generated_options:
            for verified_opt in verified_options:
                # Simple similarity: count matching characters
                common_chars = sum(1 for c in gen_opt if c in verified_opt)
                total_chars = max(len(gen_opt), len(verified_opt))
                similarity = common_chars / total_chars if total_chars > 0 else 0.0
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = verified_opt
        
        # Determine differences
        differences = []
        if not exact_match:
            differences.append(f"Generated options: {generated_options}")
            differences.append(f"Expected options: {verified_options}")
            if best_match:
                differences.append(f"Best match: '{best_match}' (similarity: {max_similarity:.2f})")
        
        return {
            'exact_match': exact_match,
            'partial_match': contains_verified or verified_contains_generated,
            'contains_verified': contains_verified,
            'verified_contains_generated': verified_contains_generated,
            'similarity_score': max_similarity,
            'best_match': best_match,
            'differences': differences
        }
    
    def validate_all_skeletons(self) -> Dict[str, Any]:
        """
        Validate all generated skeletons against verified ones.
        
        Returns:
            dict: Comprehensive validation results
        """
        validation_results = []
        english_correct = 0
        target_correct = 0
        total_rows = len(self.results_data)
        
        for idx, row in self.results_data.iterrows():
            xpath = row.get('XPATH', '')
            
            # Find corresponding verified entry by XPATH
            verified_row = self.verified_data[self.verified_data['XPATH'] == xpath]
            
            if len(verified_row) == 0:
                print(f"Warning: No verified entry found for XPATH: {xpath}")
                continue
            
            verified_row = verified_row.iloc[0]
            
            # Compare English skeletons
            english_comparison = self.compare_skeletons(
                row.get('ENGLISH_SKELETON', ''),
                verified_row.get('ENGLISH_SKELETON_VERIFIED', '')
            )
            
            # Compare target skeletons
            target_comparison = self.compare_skeletons(
                row.get('TARGET_SKELETON', ''),
                verified_row.get('TARGET_SKELETON_VERIFIED', '')
            )
            
            if english_comparison['exact_match']:
                english_correct += 1
            
            if target_comparison['exact_match']:
                target_correct += 1
            
            validation_results.append({
                'row_index': idx,
                'xpath': xpath,
                'english_generated': row.get('ENGLISH_SKELETON', ''),
                'english_verified': verified_row.get('ENGLISH_SKELETON_VERIFIED', ''),
                'english_validation': english_comparison,
                'target_generated': row.get('TARGET_SKELETON', ''),
                'target_verified': verified_row.get('TARGET_SKELETON_VERIFIED', ''),
                'target_validation': target_comparison
            })
        
        return {
            'summary': {
                'total_rows': total_rows,
                'english_accuracy': english_correct / total_rows if total_rows > 0 else 0,
                'target_accuracy': target_correct / total_rows if total_rows > 0 else 0,
                'overall_accuracy': (english_correct + target_correct) / (total_rows * 2) if total_rows > 0 else 0,
                'english_correct': english_correct,
                'target_correct': target_correct
            },
            'detailed_results': validation_results
        }
    
    def generate_validation_report(self, output_file: str = None, format: str = 'json'):
        """
        Generate a comprehensive validation report.
        
        Args:
            output_file (str): Output file path (auto-generated if None)
            format (str): Export format ('json', 'csv', 'txt')
        """
        validation_data = self.validate_all_skeletons()
        
        if output_file is None:
            results_path = Path(self.results_file)
            
            # If results are in testing/trial_X/output/, put validation in results folder
            if 'testing/trial_' in str(results_path) or 'testing\\trial_' in str(results_path):
                # Extract trial path and create results directory
                parts = results_path.parts
                trial_index = None
                for i, part in enumerate(parts):
                    if part.startswith('trial_'):
                        trial_index = i
                        break
                
                if trial_index is not None:
                    trial_path = Path(*parts[:trial_index + 1])
                    results_dir = trial_path / 'results'
                    results_dir.mkdir(exist_ok=True)
                    output_file = results_dir / f"validation_report.{format}"
                else:
                    output_file = results_path.parent / f"validation_report.{format}"
            else:
                output_file = results_path.parent / f"validation_report.{format}"
        
        if format.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(validation_data, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'csv':
            # Export summary and detailed results as CSV
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write summary
                writer.writerow(['Metric', 'Value'])
                for key, value in validation_data['summary'].items():
                    writer.writerow([key, value])
                
                writer.writerow([])  # Empty row
                
                # Write detailed results
                if validation_data['detailed_results']:
                    writer.writerow([
                        'Row', 'XPATH', 'English_Generated', 'English_Verified', 
                        'English_Exact_Match', 'English_Similarity', 'Target_Generated', 
                        'Target_Verified', 'Target_Exact_Match', 'Target_Similarity'
                    ])
                    
                    for result in validation_data['detailed_results']:
                        writer.writerow([
                            result['row_index'],
                            result['xpath'],
                            result['english_generated'],
                            result['english_verified'],
                            result['english_validation']['exact_match'],
                            f"{result['english_validation']['similarity_score']:.2f}",
                            result['target_generated'],
                            result['target_verified'],
                            result['target_validation']['exact_match'],
                            f"{result['target_validation']['similarity_score']:.2f}"
                        ])
        
        elif format.lower() == 'txt':
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("CLDR Skeleton Validation Report\n")
                f.write("=" * 40 + "\n\n")
                
                # Summary
                f.write("SUMMARY\n")
                f.write("-" * 10 + "\n")
                for key, value in validation_data['summary'].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                
                # Detailed results
                f.write("DETAILED RESULTS\n")
                f.write("-" * 20 + "\n")
                for result in validation_data['detailed_results']:
                    f.write(f"Row {result['row_index']}:\n")
                    f.write(f"  XPATH: {result['xpath']}\n")
                    f.write(f"  English: Generated='{result['english_generated']}' vs Verified='{result['english_verified']}'\n")
                    f.write(f"  English Match: {result['english_validation']['exact_match']} (Similarity: {result['english_validation']['similarity_score']:.2f})\n")
                    f.write(f"  Target: Generated='{result['target_generated']}' vs Verified='{result['target_verified']}'\n")
                    f.write(f"  Target Match: {result['target_validation']['exact_match']} (Similarity: {result['target_validation']['similarity_score']:.2f})\n")
                    f.write("\n")
        
        print(f"Validation report exported to: {output_file}")
        return output_file
    
    def generate_all_formats(self):
        """
        Generate validation reports in all formats (JSON, CSV, TXT).
        """
        formats = ['json', 'csv', 'txt']
        output_files = []
        
        for format_type in formats:
            output_file = self.generate_validation_report(format=format_type)
            output_files.append(output_file)
        
        return output_files


def validate_batch_results(results_file: str, verified_file: str, output_file: str = None, format: str = 'json'):
    """
    Convenience function to validate batch results against verified skeletons.
    
    Args:
        results_file (str): Path to batch processing results CSV
        verified_file (str): Path to verified skeletons CSV in meta_data
        output_file (str): Output file path (auto-generated if None)
        format (str): Export format ('json', 'csv', 'txt')
    """
    validator = SkeletonValidator(results_file, verified_file)
    return validator.generate_validation_report(output_file, format) 