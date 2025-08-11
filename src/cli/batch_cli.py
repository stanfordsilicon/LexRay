# -*- coding: utf-8 -*-
"""
Command-line interface for batch processing and statistics

Provides commands for processing CSV files and generating analysis reports.
"""

import argparse
import sys
from pathlib import Path

from ..batch.batch_processor import run_batch_processing
from ..batch.statistics import analyze_batch_results
from ..batch.validation import validate_batch_results


def get_cldr_data_path_noninteractive() -> str:
    """
    Get the default CLDR data path without user interaction.
    
    Returns:
        str: Path to CLDR data directory
    """
    # Default path relative to project root
    project_root = Path(__file__).parent.parent.parent
    cldr_data_path = project_root / "cldr_data"
    
    if not cldr_data_path.exists():
        print(f"Warning: CLDR data directory not found at {cldr_data_path}")
        print("Please ensure the cldr_data directory exists with your Excel files.")
        sys.exit(1)
    
    return str(cldr_data_path)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CLDR Date Skeleton Converter - Batch Processing and Analysis"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process CSV file with date pairs')
    process_parser.add_argument('input_file', help='Path to input CSV file')
    process_parser.add_argument('--cldr-data', help='Path to CLDR data directory')
    process_parser.add_argument('--stats', action='store_true', help='Generate statistics after processing')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze batch processing results')
    analyze_parser.add_argument('results_file', help='Path to batch processing results CSV')
    analyze_parser.add_argument('--output', help='Output file path')
    analyze_parser.add_argument('--format', choices=['json', 'csv', 'txt'], default='json', 
                               help='Export format (default: json)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate results against verified skeletons')
    validate_parser.add_argument('results_file', help='Path to batch processing results CSV')
    validate_parser.add_argument('verified_file', help='Path to verified skeletons CSV in meta_data')
    validate_parser.add_argument('--output', help='Output file path')
    validate_parser.add_argument('--format', choices=['json', 'csv', 'txt'], default='json', 
                                help='Export format (default: json)')
    
    # Validate-all command
    validate_all_parser = subparsers.add_parser('validate-all', help='Validate results and generate all format reports')
    validate_all_parser.add_argument('results_file', help='Path to batch processing results CSV')
    validate_all_parser.add_argument('verified_file', help='Path to verified skeletons CSV in meta_data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'process':
            print(f"Processing CSV file: {args.input_file}")
            
            cldr_data_path = args.cldr_data or get_cldr_data_path_noninteractive()
            print(f"CLDR data path: {cldr_data_path}")
            
            # Process the CSV file
            output_file = run_batch_processing(args.input_file, cldr_data_path)
            
            print(f"\n✅ Batch processing completed successfully!")
            print(f"Results saved to: {output_file}")
            
            # Generate statistics if requested
            if args.stats:
                print(f"\n📊 Generating statistics...")
                analyze_batch_results(output_file)
                print(f"Statistics saved to: {output_file.replace('.csv', '_analysis.json')}")
        
        elif args.command == 'analyze':
            print(f"Analyzing results file: {args.results_file}")
            analyze_batch_results(args.results_file, args.output, args.format)
        
        elif args.command == 'validate':
            print(f"Validating results against verified skeletons...")
            print(f"Results file: {args.results_file}")
            print(f"Verified file: {args.verified_file}")
            validate_batch_results(args.results_file, args.verified_file, args.output, args.format)
        
        elif args.command == 'validate-all':
            print(f"Validating results and generating all format reports...")
            print(f"Results file: {args.results_file}")
            print(f"Verified file: {args.verified_file}")
            
            from ..batch.validation import SkeletonValidator
            validator = SkeletonValidator(args.results_file, args.verified_file)
            output_files = validator.generate_all_formats()
            
            print(f"\n✅ Validation reports generated in all formats:")
            for output_file in output_files:
                print(f"  📄 {output_file}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 