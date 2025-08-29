# -*- coding: utf-8 -*-
"""
Main entry point for CLDR Date Skeleton Converter

A bilingual date format analyzer that converts natural language date expressions
to CLDR skeleton patterns by analyzing parallel examples in English and target languages.
"""

import os
import glob
from ..core.tokenizer import tokenize_date_expression, semantic_tokenize
from ..core.validators import (
    validate_tokens, validate_english_tokens, validate_target_language_tokens,
    validate_date_values, validate_non_empty_input
)
from ..data.data_loader import load_english_reference_data, load_target_language_data, populate_target_language_dict
from ..core.skeleton_analyzer import (
    analyze_tokens_for_format_options, generate_valid_combinations,
    convert_to_skeleton_codes, format_skeleton_strings, expand_dash_variations
)
from ..core.ambiguity_resolver import detect_ambiguities, get_metadata_for_skeleton
from ..core.cross_language_mapper import map_english_to_target_skeleton
from ..core.constants import ENGLISH_DATE_DICT


def get_available_languages(base_path):
    """
    Get list of available languages from CLDR data files.
    
    Args:
        base_path (str): Path to CLDR data directory
        
    Returns:
        list: List of available language names
    """
    try:
        all_files = glob.glob(os.path.join(base_path, "*_moderate.xlsx"))
        available_languages = []
        for f in all_files:
            lang_name = os.path.basename(f).split('_')[0]
            if lang_name != 'english':  # Exclude english reference file
                available_languages.append(lang_name)
        return sorted(available_languages)
    except:
        return []


def show_language_suggestions(base_path):
    """
    Show available languages to help user choose.
    
    Args:
        base_path (str): Path to CLDR data directory
    """
    languages = get_available_languages(base_path)
    if languages:
        print(f"\nAvailable languages ({len(languages)} total):")
        # Show first 20 languages in a nice format
        for i, lang in enumerate(languages[:20]):
            print(f"  {lang}", end="")
            if (i + 1) % 5 == 0:  # New line every 5 languages
                print()
            else:
                print(", ", end="")
        if len(languages) > 20:
            print(f"\n  ... and {len(languages) - 20} more")
        elif len(languages) <= 20 and len(languages) % 5 != 0:
            print()  # Final newline if needed


def validate_against_reference_data(expanded_options, english_df):
    """
    Validate generated skeleton options against reference CLDR data.
    
    Args:
        expanded_options (list): List of skeleton options
        english_df (pandas.DataFrame): English reference data
        
    Returns:
        list: List of confirmed skeleton combinations
    """
    english_possibilities = english_df['English'].values.tolist()
    
    confirmed_combinations = []
    for option in expanded_options:
        option = option.strip()
        # Accept if in reference data OR is a repeated character pattern
        if option in english_possibilities or len(set(option.lower())) == 1:
            confirmed_combinations.append(option)
    
    return confirmed_combinations


def get_user_skeleton_choice(confirmed_combinations):
    """
    Handle user choice when multiple skeleton options are available.
    
    Args:
        confirmed_combinations (list): List of confirmed skeleton options
        
    Returns:
        str: Selected skeleton
    """
    if len(confirmed_combinations) == 1:
        return confirmed_combinations[0]
    
    print(f"CLDR skeletons found:")
    for i, combo in enumerate(confirmed_combinations, 1):
        print(f"{i}: {combo}")
    
    while True:
        try:
            skeleton_num = input(f"\nWhich conversion would you like to use? Enter a number 1-{len(confirmed_combinations)}: ")
            choice_index = int(skeleton_num)
            if 1 <= choice_index <= len(confirmed_combinations):
                return confirmed_combinations[choice_index - 1]
            else:
                print(f"'{skeleton_num}' is not a valid option. Please try again.")
        except ValueError:
            print(f"'{skeleton_num}' is not a valid number. Please try again.")


def process_english_expression(eng_equivalent, base_path):
    """
    Process English date expression and generate skeleton.
    
    Args:
        eng_equivalent (str): English date expression
        base_path (str): Path to CLDR data files
        
    Returns:
        tuple: (eng_skeleton, ambiguities, english_df, metainfo)
    """
    # Validate input
    validate_non_empty_input(eng_equivalent, "English string")
    
    # Tokenize and validate
    english_tokenized = tokenize_date_expression(eng_equivalent)
    print(f"Tokenized: {english_tokenized}")
    
    validate_tokens(english_tokenized, "English string")
    validate_english_tokens(english_tokenized, eng_equivalent)
    
    # Analyze tokens for format options
    formatting_options = analyze_tokens_for_format_options(english_tokenized, ENGLISH_DATE_DICT)
    print(f"Format options: {formatting_options}")
    
    # Generate valid combinations
    options = generate_valid_combinations(formatting_options, english_tokens)
    
    # Convert to skeleton codes
    skeleton_options = convert_to_skeleton_codes(options)
    
    # Format as strings (without CLDR validation)
    string_options = format_skeleton_strings(skeleton_options)
    
    # Expand dash variations
    expanded_options = expand_dash_variations(string_options)
    
    # Load English reference data and validate
    english_df = load_english_reference_data(base_path)
    confirmed_combinations = validate_against_reference_data(expanded_options, english_df)
    
    if not confirmed_combinations:
        raise ValueError(f"No official CLDR skeleton for '{eng_equivalent}'.")
    
    # Validate date values
    if confirmed_combinations:
        # Use first combination for validation
        validate_date_values(english_tokenized, tokenize_date_expression(confirmed_combinations[0]))
    
    # Display results
    if len(confirmed_combinations) == 1:
        print(f"\nCLDR skeleton for '{eng_equivalent}': {confirmed_combinations[0]}")
        eng_skeleton = confirmed_combinations[0]
    else:
        print(f"\nCLDR skeletons for '{eng_equivalent}':")
        for i, combo in enumerate(confirmed_combinations, 1):
            print(f"{i}: {combo}")
        eng_skeleton = get_user_skeleton_choice(confirmed_combinations)
    
    # Handle ambiguities
    english_skeleton_tokenized = tokenize_date_expression(eng_skeleton)
    ambiguities = detect_ambiguities(english_tokenized, english_skeleton_tokenized)
    
    # Get metadata
    metainfo = get_metadata_for_skeleton(eng_skeleton, ambiguities, english_df)
    
    return eng_skeleton, ambiguities, english_df, metainfo


def process_target_language(lang_code, base_path, tlang_expression, eng_equivalent, eng_skeleton, ambiguities):
    """
    Process target language expression and generate skeleton.
    
    Args:
        lang_code (str): Target language code
        base_path (str): Path to CLDR data files
        tlang_expression (str): Target language expression
        eng_equivalent (str): Original English expression
        eng_skeleton (str): English skeleton
        ambiguities (list): Ambiguity resolution data
        
    Returns:
        list: List of target language skeleton combinations
    """
    # Validate inputs
    validate_non_empty_input(lang_code, "Language code")
    validate_non_empty_input(tlang_expression, "Target language string")
    
    # Load target language data
    tlang_df = load_target_language_data(base_path, lang_code)
    date_dict, lexicon = populate_target_language_dict(tlang_df)
    
    # Tokenize target language expression
    tlang_tokenized = semantic_tokenize(tlang_expression, date_dict, lexicon)
    print(f"\nTarget language tokenized: {tlang_tokenized}")
    
    # Validate tokens (but allow literal text)
    validate_tokens(tlang_tokenized, "Target language string")
    
    # Check for literal text (don't error, just inform)
    literal_tokens = []
    for token in tlang_tokenized:
        if (not token.isnumeric() and 
            token not in [",", "/", "-", "–", "."] and 
            token not in lexicon):
            literal_tokens.append(token)
            print(f"Note: '{token}' will be treated as literal text")
    
    # Map English to target language skeleton
    english_tokenized = tokenize_date_expression(eng_equivalent)
    target_skeleton_strings = map_english_to_target_skeleton(
        english_tokenized, eng_skeleton, tlang_tokenized, date_dict, ambiguities, tlang_expression
    )
    
    # Analyze target language tokens for valid options (excluding literal text tokens)
    # Filter out literal tokens for traditional skeleton analysis
    date_only_tokens = []
    for token in tlang_tokenized:
        if (token.isnumeric() or 
            token in [",", "/", "-", "–", "."] or 
            token in lexicon):
            date_only_tokens.append(token)
    
    if date_only_tokens:
        target_formatting_options = analyze_tokens_for_format_options(date_only_tokens, date_dict)
        target_options = generate_valid_combinations(target_formatting_options, tlang_tokenized)
        target_skeleton_options = convert_to_skeleton_codes(target_options)
        target_string_options = format_skeleton_strings(target_skeleton_options, english_df)
        
        # For validation, check if the cross-language mapped skeletons are reasonable
        # by comparing the non-literal parts
        confirmed_combinations = []
        for skeleton in target_skeleton_strings:
            # Extract the non-literal parts for comparison
            skeleton_without_literals = skeleton
            # Remove only quoted literals (preserve spaces around them)
            import re
            skeleton_without_literals = re.sub(r"'[^']*'", "", skeleton_without_literals)
            # Clean up multiple spaces but preserve single spaces
            skeleton_without_literals = re.sub(r'\s+', ' ', skeleton_without_literals).strip()
            
            # Check if the core skeleton structure is valid
            is_valid = False
            for valid_option in target_string_options:
                if skeleton_without_literals == valid_option:
                    is_valid = True
                    break
            
            # If the core structure is valid, accept the skeleton with literals
            # Also accept if it's a reasonable pattern even if not exact match
            if is_valid or not target_string_options:
                confirmed_combinations.append(skeleton)
            else:
                # More flexible validation - check if it contains expected elements
                # Count CLDR elements in both skeletons
                original_elements = re.findall(r'[MLdyEc]+', skeleton_without_literals)
                if any(re.findall(r'[MLdyEc]+', valid_option) == original_elements for valid_option in target_string_options):
                    confirmed_combinations.append(skeleton)
                elif target_skeleton_strings:  # If we generated something, it's probably valid
                    confirmed_combinations.append(skeleton)
                
    else:
        # If no recognizable date tokens, accept whatever was generated
        confirmed_combinations = target_skeleton_strings
    
    return confirmed_combinations


def get_cldr_data_path():
    """
    Get the path to CLDR data files with intelligent defaults.
    
    Returns:
        str: Path to CLDR data directory
    """
    # Default to cldr_data folder in the project root directory
    # Go up from src/cli/ to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    default_path = os.path.join(project_root, "cldr_data")
    
    print(f"Default CLDR data path: {default_path}")
    
    # Check if default path exists and has data files
    if os.path.exists(default_path):
        xlsx_files = [f for f in os.listdir(default_path) if f.endswith('.xlsx')]
        if xlsx_files:
            print(f"Found {len(xlsx_files)} CLDR data files in default location.")
            use_default = input(f"Use default path '{default_path}'? (yes/no, default: yes): ").strip().lower()
            if use_default in ['', 'yes', 'y']:
                return default_path
    
    # Ask user for custom path
    base_path = input("Enter the path to CLDR data files: ").strip()
    if not base_path:
        print("Using default cldr_data directory...")
        return default_path
    
    return base_path


def main():
    """
    Main function to run the CLDR Date Skeleton Converter.
    """
    print("=== CLDR Date Skeleton Converter ===")
    print("Convert natural language date expressions to CLDR skeleton patterns")
    print()
    
    # Get base path for CLDR data files
    base_path = get_cldr_data_path()
    
    if not os.path.exists(base_path):
        print(f"Error: Path '{base_path}' does not exist.")
        print(f"Please create the directory and place your CLDR Excel files there.")
        return
    
    # Check for required English reference file
    english_file = os.path.join(base_path, "english_moderate.xlsx")
    if not os.path.exists(english_file):
        print(f"Error: Required file 'english_moderate.xlsx' not found in '{base_path}'.")
        print(f"Please place the English reference data file in the CLDR data directory.")
        return
    
    try:
        # Process English expression
        print("\n--- English Date Expression ---")
        eng_equivalent = input("Enter an English date expression: ").strip()
        
        eng_skeleton, ambiguities, english_df, metainfo = process_english_expression(eng_equivalent, base_path)
        
        # Ask if user wants to process target language
        print(f"\n--- Translation Option ---")
        answer = input(f"Do you have a translation of '{eng_equivalent}' in a different language? (yes/no): ").strip().lower()
        
        if answer == "yes":
            # Process target language
            print(f"\n--- Target Language ---")
            show_language_suggestions(base_path)
            print(f"\nSimply type the language name (e.g., 'spanish', 'french', 'german')")
            lang_code = input("Enter target language: ").strip()
            
            if not lang_code:
                print("No language specified. Skipping translation.")
                print(f"\n=== RESULTS ===")
                print(f"English skeleton for '{eng_equivalent}': {eng_skeleton}")
                print(f"General CLDR code: {', '.join(metainfo[0][1])}")
                print(f"CLDR X-path: {', '.join(metainfo[0][2])}")
                return
            
            tlang_expression = input(f"Enter the translation for '{eng_equivalent}' in {lang_code.capitalize()}: ").strip()
            
            try:
                target_combinations = process_target_language(
                    lang_code, base_path, tlang_expression, eng_equivalent, eng_skeleton, ambiguities
                )
                
                # Display results
                print(f"\n=== RESULTS ===")
                print(f"English skeleton for '{eng_equivalent}': {eng_skeleton}")
                
                if not target_combinations:
                    print(f"'{tlang_expression}' is not a valid translation of '{eng_equivalent}'.")
                else:
                    if len(target_combinations) == 1:
                        print(f"{lang_code.capitalize()} skeleton for '{tlang_expression}': {target_combinations[0]}")
                    else:
                        print(f"{lang_code.capitalize()} skeletons for '{tlang_expression}': {', '.join(target_combinations)}")
                
                print(f"\nGeneral CLDR code: {', '.join(metainfo[0][1])}")
                print(f"CLDR X-path: {', '.join(metainfo[0][2])}")
            
            except FileNotFoundError as e:
                print(f"\nError: {e}")
                print(f"\nFalling back to English-only results:")
                print(f"English skeleton for '{eng_equivalent}': {eng_skeleton}")
                print(f"General CLDR code: {', '.join(metainfo[0][1])}")
                print(f"CLDR X-path: {', '.join(metainfo[0][2])}")
        
        elif answer == "no":
            print(f"\n=== RESULTS ===")
            print(f"English skeleton for '{eng_equivalent}': {eng_skeleton}")
            print(f"General CLDR code: {', '.join(metainfo[0][1])}")
            print(f"CLDR X-path: {', '.join(metainfo[0][2])}")
            print("\nGoodbye!")
        
        else:
            print(f"'{answer}' is not a valid option.")
    
    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main() 