# -*- coding: utf-8 -*-
"""
Data loading utilities for CLDR language data

Handles loading and processing of CLDR data from Excel files,
populating target language dictionaries and lexicons.
"""

import os
import pandas as pd


def load_english_reference_data(base_path):
    """
    Load English reference data from Excel file.
    
    Args:
        base_path (str): Base path to CLDR data files
        
    Returns:
        pandas.DataFrame: English reference data
        
    Raises:
        FileNotFoundError: If English reference file not found
    """
    filename = "english_moderate.xlsx"
    file_path = os.path.join(base_path, filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"English reference file not found at: {file_path}")
    
    print(f"Loading English reference data from: {file_path}")
    df = pd.read_excel(file_path, engine='openpyxl')
    
    # Clean thin space characters from the data
    english_possibilities = df['English'].values.tolist()
    english_possibilities = [
        str(item).replace('\u2009', ' ') if isinstance(item, str) else item
        for item in english_possibilities
    ]
    df['English'] = english_possibilities
    
    return df


def load_target_language_data(base_path, lang_code):
    """
    Load target language CLDR data from Excel file.
    Automatically finds the correct file based on language name.
    
    Args:
        base_path (str): Path to CLDR data directory
        lang_code (str): Language name (e.g., 'spanish', 'french', 'german')
        
    Returns:
        pandas.DataFrame: Target language data
    """
    import glob
    
    lang_code = lang_code.strip().lower()
    
    # First, try the exact match format: {lang_code}_moderate.xlsx
    filename = f"{lang_code}_moderate.xlsx"
    file_path = os.path.join(base_path, filename)
    
    if os.path.exists(file_path):
        print(f"Loading {lang_code.capitalize()} data from: {file_path}")
        return pd.read_excel(file_path, engine='openpyxl')
    
    # If exact match fails, search for files that start with the language name
    search_pattern = os.path.join(base_path, f"{lang_code}*_moderate.xlsx")
    matching_files = glob.glob(search_pattern)
    
    if matching_files:
        file_path = matching_files[0]  # Use the first match
        actual_lang = os.path.basename(file_path).split('_')[0]
        print(f"Found matching file for '{lang_code}': {actual_lang}")
        print(f"Loading {actual_lang.capitalize()} data from: {file_path}")
        return pd.read_excel(file_path, engine='openpyxl')
    
    # If still no match, list available languages to help the user
    all_files = glob.glob(os.path.join(base_path, "*_moderate.xlsx"))
    available_languages = []
    for f in all_files:
        lang_name = os.path.basename(f).split('_')[0]
        if lang_name != 'english':  # Exclude english reference file
            available_languages.append(lang_name)
    
    available_languages.sort()
    
    error_msg = f"Could not find CLDR data for language '{lang_code}'.\n"
    error_msg += f"Available languages in {base_path}:\n"
    error_msg += ", ".join(available_languages[:10])  # Show first 10
    if len(available_languages) > 10:
        error_msg += f" ... and {len(available_languages) - 10} more"
    
    raise FileNotFoundError(error_msg)


def populate_target_language_dict(tlang_df):
    """
    Populate target language date dictionary from translation data.
    
    Args:
        tlang_df (pandas.DataFrame): Target language data
        
    Returns:
        tuple: (date_dict, lexicon) - populated dictionary and lexicon
    """
    date_dict = {
        "mon_nar_for": [], "mon_wid_for": [], "mon_abb_for": [], 
        "mon_nar_sta": [], "mon_wid_sta": [], "mon_abb_sta": [],
        "day_sho_for": [], "day_nar_for": [], "day_wid_for": [], "day_abb_for": [], 
        "day_sho_sta": [], "day_nar_sta": [], "day_wid_sta": [], "day_abb_sta": []
    }
    
    lexicon = []
    
    # Define element types and their length options
    elem_types = ["Months", "Days"]
    mon_lengths = ["narrow", "wide", "abbreviated"]
    wday_lengths = ["short", "narrow", "wide", "abbreviated"]
    elem_contexts = ["Formatting", "Standalone"]
    
    # Populate date dictionary and lexicon from target language data
    for elem_type in elem_types:
        # Select appropriate length options for current element type
        lengths = mon_lengths if elem_type == "Months" else wday_lengths
        
        for elem_context in elem_contexts:
            for length in lengths:
                # Find matching translations in the dataset
                date_structure = f"{elem_type} - {length} - {elem_context}"
                matching_rows = tlang_df[tlang_df['Header'] == date_structure]
                column_name = "Translation" if "Translation" in matching_rows.columns else "Winning"
                translations = matching_rows[column_name].dropna().tolist()  # Remove NaN values
                
                # Limit to expected number of items (12 months, 7 days)
                max_items = 12 if elem_type == "Months" else 7
                translations = translations[:max_items]
                
                # Add to lexicon and dictionary
                lexicon.extend(translations)
                
                # Also add lowercase versions for case-insensitive matching
                lexicon.extend([val.lower() for val in translations if isinstance(val, str)])
                
                # Generate dictionary key (e.g., "mon_nar_for", "day_wid_sta")
                date_dict_key = f"{elem_type.lower()[:3]}_{length[:3]}_{elem_context.lower()[:3]}"
                date_dict[date_dict_key] = translations
                
                print(f"{date_structure}: {translations}")
    
    return date_dict, lexicon 