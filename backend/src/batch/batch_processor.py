# -*- coding: utf-8 -*-
"""
Batch processing utilities for CLDR Date Skeleton Converter

Handles processing multiple date pairs from CSV files and generates
statistics and reports on the results.
"""

import csv
import os
import re
import pandas as pd
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from ..core.tokenizer import tokenize_date_expression, semantic_tokenize
from ..data.data_loader import load_target_language_data, populate_target_language_dict
from ..core.cross_language_mapper import map_english_to_target_skeleton
from ..core.skeleton_analyzer import (
    analyze_tokens_for_format_options, generate_valid_combinations,
    convert_to_skeleton_codes, format_skeleton_strings
)
from ..core.constants import ENGLISH_DATE_DICT


class BatchProcessor:
    """
    Handles batch processing of date pairs from CSV files.
    """
    
    def __init__(self, cldr_data_path: str):
        """
        Initialize the batch processor.
        
        Args:
            cldr_data_path (str): Path to CLDR data directory
        """
        self.cldr_data_path = cldr_data_path
        self.target_language = None
        self.target_date_dict = None
        self.target_lexicon = None
        
    def detect_language_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract language name from CSV filename.
        
        Expected format: {language}_data.csv
        
        Args:
            filename (str): CSV filename
            
        Returns:
            str: Detected language name or None
        """
        # Remove file extension and get base name
        base_name = Path(filename).stem.lower()
        
        # Check for {language}_data pattern
        if base_name.endswith('_data'):
            language = base_name[:-5]  # Remove '_data' suffix
            return language
        
        # Fallback: try to detect language from filename (old method)
        language_patterns = [
            r'spanish', r'french', r'german', r'italian', r'portuguese',
            r'chinese', r'japanese', r'korean', r'arabic', r'hebrew',
            r'russian', r'polish', r'dutch', r'swedish', r'norwegian',
            r'danish', r'finnish', r'hungarian', r'czech', r'slovak',
            r'romanian', r'bulgarian', r'croatian', r'serbian', r'slovenian',
            r'estonian', r'latvian', r'lithuanian', r'turkish', r'greek',
            r'ukrainian', r'belarusian', r'kazakh', r'uzbek', r'kyrgyz',
            r'tajik', r'turkmen', r'azerbaijani', r'georgian', r'armenian',
            r'persian', r'urdu', r'hindi', r'bengali', r'tamil', r'telugu',
            r'marathi', r'gujarati', r'kannada', r'malayalam', r'punjabi',
            r'nepali', r'sinhala', r'thai', r'vietnamese', r'indonesian',
            r'malay', r'filipino', r'khmer', r'lao', r'myanmar', r'mongolian'
        ]
        
        for pattern in language_patterns:
            if re.search(pattern, base_name):
                return re.search(pattern, base_name).group()
        
        return None
    
    def load_target_language_data(self, language: str) -> bool:
        """
        Load target language data.
        
        Args:
            language (str): Target language name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            df = load_target_language_data(self.cldr_data_path, language)
            self.target_date_dict, self.target_lexicon = populate_target_language_dict(df)
            self.target_language = language
            return True
        except Exception as e:
            print(f"Error loading {language} data: {e}")
            return False
    
    def process_single_row(self, english_text: str, target_text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Process a single date pair.
        
        Args:
            english_text (str): English date expression
            target_text (str): Target language date expression
            
        Returns:
            tuple: (english_skeleton, target_skeleton) or (None, None) if failed
        """
        try:
            # Process English expression
            english_tokens = tokenize_date_expression(english_text)
            english_formatting_options = analyze_tokens_for_format_options(english_tokens, ENGLISH_DATE_DICT)
            english_options = generate_valid_combinations(english_formatting_options)
            english_skeleton_options = convert_to_skeleton_codes(english_options)
            english_skeleton_strings = format_skeleton_strings(english_skeleton_options)
            
            if not english_skeleton_strings:
                return None, None
            
            # Use first English skeleton (most common)
            english_skeleton = english_skeleton_strings[0]
            
            # Process target expression
            target_tokens = semantic_tokenize(target_text, self.target_date_dict, self.target_lexicon)
            
            # Map English to target skeleton
            target_skeleton_strings = map_english_to_target_skeleton(
                english_tokens, english_skeleton, target_tokens, 
                self.target_date_dict, [], target_text
            )
            
            if not target_skeleton_strings:
                return english_skeleton, None
            
            # Return all target skeleton options as comma-separated string
            target_skeleton = ", ".join(target_skeleton_strings)
            
            return english_skeleton, target_skeleton
            
        except Exception as e:
            print(f"Error processing row '{english_text}' -> '{target_text}': {e}")
            return None, None
    
    def process_csv_file(self, input_file: str) -> str:
        """
        Process entire CSV file and generate output.
        
        Args:
            input_file (str): Path to input CSV file
            
        Returns:
            str: Path to output CSV file
        """
        # Detect language from filename
        language = self.detect_language_from_filename(input_file)
        if not language:
            raise ValueError(f"Could not detect language from filename: {input_file}")
        
        print(f"Detected language: {language}")
        
        # Load target language data
        if not self.load_target_language_data(language):
            raise ValueError(f"Failed to load {language} data")
        
        # Generate output filename
        input_path = Path(input_file)
        
        # If input is in testing/trial_YYYYMMDD_HHMMSS/input/, output to testing/trial_YYYYMMDD_HHMMSS/output/
        if 'testing/trial_' in str(input_path) or 'testing\\trial_' in str(input_path):
            # Extract trial path and create output directory
            parts = input_path.parts
            trial_index = None
            for i, part in enumerate(parts):
                if part.startswith('trial_'):
                    trial_index = i
                    break
            
            if trial_index is not None:
                # Reconstruct path up to trial folder, then add output
                trial_path = Path(*parts[:trial_index + 1])
                output_dir = trial_path / 'output'
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / f"{input_path.stem}_results{input_path.suffix}"
            else:
                # Fallback: output in same directory as input
                output_file = input_path.parent / f"{input_path.stem}_results{input_path.suffix}"
        else:
            # Default behavior: output in same directory as input
            output_file = input_path.parent / f"{input_path.stem}_results{input_path.suffix}"
        
        # Process CSV
        processed_rows = 0
        failed_rows = 0
        
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=['ENGLISH_SKELETON', 'TARGET_SKELETON', 'XPATH'])
            
            writer.writeheader()
            
            for row_num, row in enumerate(reader, 1):
                english_text = row.get('ENGLISH', '').strip()
                target_text = row.get('TARGET', '').strip()
                xpath = row.get('XPATH', '').strip()
                
                if not english_text or not target_text:
                    print(f"Warning: Row {row_num} has empty ENGLISH or TARGET field, skipping")
                    failed_rows += 1
                    continue
                
                english_skeleton, target_skeleton = self.process_single_row(english_text, target_text)
                
                if english_skeleton is None:
                    print(f"Warning: Row {row_num} failed to process, skipping")
                    failed_rows += 1
                    continue
                
                writer.writerow({
                    'ENGLISH_SKELETON': english_skeleton,
                    'TARGET_SKELETON': target_skeleton or '',
                    'XPATH': xpath
                })
                
                processed_rows += 1
                
                # Progress indicator
                if processed_rows % 10 == 0:
                    print(f"Processed {processed_rows} rows...")
        
        print(f"\nBatch processing complete!")
        print(f"Successfully processed: {processed_rows} rows")
        print(f"Failed rows: {failed_rows} rows")
        print(f"Output file: {output_file}")
        
        return str(output_file)


def run_batch_processing(input_file: str, cldr_data_path: str) -> str:
    """
    Convenience function to run batch processing.
    
    Args:
        input_file (str): Path to input CSV file
        cldr_data_path (str): Path to CLDR data directory
        
    Returns:
        str: Path to output CSV file
    """
    processor = BatchProcessor(cldr_data_path)
    return processor.process_csv_file(input_file) 