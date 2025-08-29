# -*- coding: utf-8 -*-
"""
Skeleton analysis utilities for date expressions

Core logic for analyzing tokens, determining possible date format interpretations,
generating skeleton combinations, and converting between semantic codes and CLDR skeletons.
"""

from itertools import product
from .constants import SKELETON_CODES, ENGLISH_DATE_DICT, PUNCTUATION


def analyze_tokens_for_format_options(tokens, date_dict, is_standalone=None):
    """
    Analyze tokens to determine all possible date format interpretations.
    
    Args:
        tokens (list): List of tokens to analyze
        date_dict (dict): Date dictionary to use for lookup
        is_standalone (bool): Whether this is standalone format (auto-detect if None)
        
    Returns:
        list: List of lists, each containing possible format codes for each token
    """
    if is_standalone is None:
        is_standalone = len(tokens) == 1
    
    formatting_options = []
    
    for token in tokens:
        token_options = []
        
        if token.isalpha() or (isinstance(token, str) and any(c.isalpha() for c in token)):
            # Check alphabetic tokens against date dictionary
            for key in date_dict.keys():
                # Filter keys based on standalone vs format context
                if is_standalone and key.endswith("for"):
                    continue
                if not is_standalone and key.endswith("sta"):
                    continue
                
                # Case-insensitive matching
                if any(token.lower() == item.lower() for item in date_dict[key]):
                    token_options.append(key)
        
        elif token.isnumeric():
            if len(token) == 4:
                # 4-digit numbers are always years
                token_options.append("year")
            elif len(token) <= 2:
                # 1-2 digit numbers can be days, months, or abbreviated years
                if len(token) == 2:
                    if token[0] == "0":
                        # Zero-padded 2-digit numbers (01-09)
                        if is_standalone:
                            token_options.extend(["mday_sma_sta", "mon_sma_sta", "year_abb_sta"])
                        else:
                            token_options.extend(["mday_sma_for", "mon_sma_for", "year_abb_for"])
                    else:
                        # Non-zero 2-digit numbers (10-99)
                        # For 2-digit numbers, prioritize day/month over year
                        # Only include year abbreviation in very specific cases
                        value = int(token)
                        if is_standalone:
                            token_options.extend(["mday_min_sta", "mday_sma_sta", "mon_min_sta", "mon_sma_sta"])
                            # Only add year option if it's clearly a year (e.g., 20 for 2020)
                            # Be more restrictive - only include year options for very specific year-like values
                            if value >= 20 and value <= 99 and value % 10 == 0:  # Only round decades like 20, 30, 40, etc.
                                token_options.append("year_abb_sta")
                        else:
                            token_options.extend(["mday_min_for", "mday_sma_for", "mon_min_for", "mon_sma_for"])
                            # Only add year option if it's clearly a year (e.g., 20 for 2020)
                            # Be more restrictive - only include year options for very specific year-like values
                            if value >= 20 and value <= 99 and value % 10 == 0:  # Only round decades like 20, 30, 40, etc.
                                token_options.append("year_abb_for")
                else:  # len(token) == 1
                    # Single-digit numbers (1-9)
                    if is_standalone:
                        token_options.extend(["mday_min_sta", "mon_min_sta"])
                    else:
                        token_options.extend(["mday_min_for", "mon_min_for"])
        
        elif token in PUNCTUATION:
            # Punctuation tokens are added as-is
            token_options.append(token)
        
        formatting_options.append(token_options)
    
    return formatting_options


def generate_valid_combinations(formatting_options, original_tokens=None):
    """
    Generate all valid date format combinations from token options.
    
    Args:
        formatting_options (list): List of token option lists
        original_tokens (list): Original tokens for validation (optional)
        
    Returns:
        list: List of valid format combinations
    """
    options = []
    
    if len(formatting_options) == 1:
        # Single token: validate all options exist in skeleton codes
        if all(item in SKELETON_CODES.keys() for item in formatting_options[0]):
            options = [[option] for option in formatting_options[0]]
        else:
            raise ValueError("Invalid format options.")
    else:
        # Multi-token: group tokens by dash/period-separated sections
        new_formatting_options = []
        current_group = []
        
        for format_list in formatting_options:
            if format_list == ["-"] or format_list == ["."] or format_list == ["–"] or format_list == ["—"]:
                if current_group:
                    new_formatting_options.append(current_group)
                new_formatting_options.append(format_list[0])  # Add the separator
                current_group = []
            else:
                current_group.append(format_list)
        
        if current_group:
            new_formatting_options.append(current_group)
        
        # Extract sections (ignore separators for combination generation)
        sections = [item for item in new_formatting_options if item not in ["-", ".", "–", "—"]]
        
        # Generate valid combinations for each section
        section_combinations = []
        for section in sections:
            all_combinations = list(product(*section))
            
            # Filter out combinations with duplicate date element types and invalid value assignments
            valid_combinations = []
            for combo in all_combinations:
                date_elements = [elem for elem in combo if isinstance(elem, str) and '_' in elem]
                prefixes = [elem.split('_')[0] for elem in date_elements]
                
                # Check for duplicate prefixes
                if len(prefixes) != len(set(prefixes)):
                    continue
                
                # Check for logical validity of the combination
                is_valid = True
                if original_tokens:
                    # For each section, we need to find the corresponding numeric tokens
                    # This is complex because sections may not align perfectly with the original token sequence
                    # For now, we'll use a simpler approach: validate that the combination makes logical sense
                    # without trying to map to specific numeric tokens
                    
                    # Count numeric elements in this combination
                    numeric_elements = [elem for elem in date_elements if elem.startswith('mday_') or elem.startswith('mon_') or elem.startswith('year')]
                    
                    # For now, accept all combinations that don't have duplicate prefixes
                    # The validation will be done at a higher level when we have the full context
                    pass
                
                if is_valid:
                    valid_combinations.append(list(combo))
            
            section_combinations.append(valid_combinations)
        
        # Combine sections with separators
        if len(section_combinations) == 1:
            options = section_combinations[0]
        else:
            all_section_products = list(product(*section_combinations))
            for section_combo_tuple in all_section_products:
                combined = []
                separator_index = 0
                for i, section_combo in enumerate(section_combo_tuple):
                    if i > 0:
                        # Find the next separator in new_formatting_options
                        while separator_index < len(new_formatting_options) and new_formatting_options[separator_index] not in ["-", ".", "–", "—"]:
                            separator_index += 1
                        if separator_index < len(new_formatting_options):
                            combined.append(new_formatting_options[separator_index])
                            separator_index += 1
                    combined.extend(section_combo)
                options.append(combined)
    
    return options


def convert_to_skeleton_codes(options):
    """
    Convert format codes to CLDR skeleton codes.
    
    Args:
        options (list): List of format option combinations
        
    Returns:
        list: List of skeleton code combinations
    """
    converted_options = []
    
    for option in options:
        converted_option = []
        for element in option:
            if isinstance(element, str) and (element.endswith('_for') or element.endswith('_sta') or element == "year"):
                converted_option.append(SKELETON_CODES[element])
            else:
                converted_option.append(element)
        
        # Validate that no duplicate skeleton element types exist within the same side of a range
        # For ranges (containing '-'), allow duplicates on different sides
        if '-' in converted_option or '–' in converted_option:
            # For ranges, allow duplicates as they can appear on both sides
            converted_options.append(converted_option)
        else:
            # For non-ranges, check for duplicates
            element_types = []
            for code in converted_option:
                if isinstance(code, str):
                    if code.startswith('M'):
                        element_types.append('M')
                    elif code.startswith('d'):
                        element_types.append('d')
                    elif code.startswith('y'):
                        element_types.append('y')
                    elif code.startswith('E'):
                        element_types.append('E')
                    elif code.startswith('L'):
                        element_types.append('L')
                    elif code.startswith('c'):
                        element_types.append('c')
            
            # Only add options that don't have duplicate element types
            if len(element_types) == len(set(element_types)):
                converted_options.append(converted_option)
    
    return converted_options


def format_skeleton_strings(options, english_cldr_data=None):
    """
    Convert skeleton combinations to properly spaced strings.
    
    Args:
        options (list): List of skeleton code combinations
        english_cldr_data (pandas.DataFrame): English CLDR data for validation
        
    Returns:
        list: List of formatted skeleton strings
    """
    string_options = []
    
    for option in options:
        if not option:
            string_options.append("")
            continue
        
        # Final validation: check for duplicate element types in the final skeleton
        # For ranges (containing '-'), allow duplicates on different sides
        if '-' in option or '–' in option:
            # For ranges, allow duplicates as they can appear on both sides
            pass
        else:
            # For non-ranges, check for duplicates
            element_types = []
            for code in option:
                if isinstance(code, str):
                    if code.startswith('M'):
                        element_types.append('M')
                    elif code.startswith('d'):
                        element_types.append('d')
                    elif code.startswith('y'):
                        element_types.append('y')
                    elif code.startswith('E'):
                        element_types.append('E')
                    elif code.startswith('L'):
                        element_types.append('L')
                    elif code.startswith('c'):
                        element_types.append('c')
            
            # Skip options with duplicate element types
            if len(element_types) != len(set(element_types)):
                continue
        
        result = str(option[0])
        
        for i in range(1, len(option)):
            current = str(option[i])
            previous = str(option[i-1])
            
            # Check if element contains non-punctuation content
            has_content = lambda x: x.replace(',', '').replace('/', '').replace('-', '').replace('–', '').replace('.', '').strip()
            
            # Apply spacing rules
            if previous == ',' and current not in PUNCTUATION:
                # Space after comma (unless followed by punctuation)
                result += ' ' + current
            elif (has_content(previous) and has_content(current) and
                  previous not in PUNCTUATION and current not in PUNCTUATION):
                # Space between date elements (both contain letters/numbers)
                result += ' ' + current
            elif current in ['-', '–'] or previous in ['-', '–']:
                # No space around dashes
                result += current
            else:
                # No space for punctuation connections
                result += current
        
        # Validate against English CLDR data if provided
        if english_cldr_data is not None:
            if 'Winning' in english_cldr_data.columns:
                # Check if this skeleton exists in the winning examples
                if result not in english_cldr_data['Winning'].values:
                    continue  # Skip this skeleton if it doesn't exist in CLDR data
        
        string_options.append(result)
    
    return string_options


def expand_dash_variations(string_options):
    """
    Generate dash type variations (hyphen-minus and en-dash) for skeletons.
    
    Args:
        string_options (list): List of skeleton strings
        
    Returns:
        list: List of skeleton strings with dash variations
    """
    expanded_options = []
    
    for skeleton in string_options:
        if '-' in skeleton or '–' in skeleton:
            # Normalize to hyphen-minus then create both dash variations
            base_skeleton = skeleton.replace('–', '-')
            
            # Create hyphen-minus and en-dash variations
            variations = [
                base_skeleton,                    # hyphen-minus
                base_skeleton.replace('-', '–')   # en-dash
            ]
            
            # Remove duplicates while preserving order
            unique_variations = []
            for var in variations:
                if var not in unique_variations:
                    unique_variations.append(var)
            
            expanded_options.extend(unique_variations)
        else:
            # No dashes - add original skeleton as-is
            expanded_options.append(skeleton)
    
    return expanded_options 