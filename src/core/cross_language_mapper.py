# -*- coding: utf-8 -*-
"""
Cross-language mapping utilities

Handles the complex logic for mapping English date tokens to target language
equivalents, including fuzzy numeric matching, permutation testing, and
ambiguity resolution during cross-language conversion.
"""

from itertools import permutations, product
import regex
from .constants import ENGLISH_DATE_DICT, MONTH_INDEXING, DAY_INDEXING, TOKEN_PATTERN, SKELETON_CODES


def map_english_to_target_skeleton(english_tokens, english_skeleton, target_tokens, target_date_dict, ambiguities, original_target_expression=None):
    """
    Main function to map English skeleton to target language skeleton.
    Now handles literal text by wrapping it in single quotes and preserves original spacing.
    
    Args:
        english_tokens (list): English tokens
        english_skeleton (str): English skeleton string
        target_tokens (list): Target language tokens
        target_date_dict (dict): Target language date dictionary
        ambiguities (list): Ambiguity resolution data
        original_target_expression (str, optional): Original target expression for accurate spacing analysis
        
    Returns:
        list: List of possible target language skeleton strings
    """
    print(f"Target tokenized: {target_tokens}")
    print(f"English skeleton: {english_skeleton}")
    
    # Tokenize English skeleton for mapping
    english_skeleton_tokenized = regex.findall(TOKEN_PATTERN, english_skeleton)
    print(f"English skeleton tokenized: {english_skeleton_tokenized}")
    
    english_tokenized = regex.findall(TOKEN_PATTERN, " ".join(english_tokens))
    print(f"English tokenized: {english_tokenized}")
    
    # Analyze original target expression to preserve spacing
    if original_target_expression is None:
        # Fallback to reconstructed expression (old behavior)
        original_target_expression = " ".join(target_tokens)
    
    spacing_info = []
    
    # Track spacing between tokens in the original expression
    current_pos = 0
    for i, token in enumerate(target_tokens):
        token_start = original_target_expression.find(token, current_pos)
        
        if i > 0:
            # Check if there's a space before this token
            prev_token_end = spacing_info[i-1]['end']
            has_space_before = token_start > prev_token_end
            spacing_info.append({
                'token': token,
                'start': token_start,
                'end': token_start + len(token),
                'has_space_before': has_space_before
            })
        else:
            spacing_info.append({
                'token': token,
                'start': token_start,
                'end': token_start + len(token),
                'has_space_before': False
            })
        
        current_pos = token_start + len(token)
    
    print(f"Spacing info: {spacing_info}")
    
    # Categorize target tokens and build target date lexicon
    target_date_lexicon = []
    for category_list in target_date_dict.values():
        target_date_lexicon.extend(category_list)
    
    categorized_target_tokens = []
    for i, token in enumerate(target_tokens):
        spacing = spacing_info[i] if i < len(spacing_info) else {'has_space_before': True}
        
        # Handle attached tokens (compound words)
        if token.startswith("ATTACHED:"):
            actual_token = token[9:]  # Remove "ATTACHED:" prefix
            spacing['has_space_before'] = False  # Attached tokens have no space
            token = actual_token
        
        if token.isnumeric():
            categorized_target_tokens.append(('numeric', token, spacing))
        elif token in [",", "/", "-", "–", "."]:
            categorized_target_tokens.append(('punctuation', token, spacing))
        elif token in target_date_lexicon:
            categorized_target_tokens.append(('date_element', token, spacing))
        else:
            # This is literal text - will be wrapped in quotes
            categorized_target_tokens.append(('literal', token, spacing))
            print(f"Note: '{token}' will be treated as literal text")
    
    print(f"Categorized target tokens: {[(cat, token) for cat, token, spacing in categorized_target_tokens]}")
    
    # Create mapping from English date elements to all their target language variants
    english_to_target_variants = {}
    target_element_to_skeleton = {}
    english_element_mappings = {}  # Initialize the dictionary
    
    # For each English token, find all possible target language variants
    for i, eng_token in enumerate(english_tokenized):
        if i < len(english_skeleton_tokenized):
            skeleton_code = english_skeleton_tokenized[i]
            
            if eng_token.isnumeric():
                # Handle numeric tokens (already working correctly)
                english_element_mappings[eng_token] = [skeleton_code]
                
                # Add numeric variations
                if skeleton_code in ["M", "d"]:
                    if len(eng_token) == 1:
                        zero_padded = "0" + eng_token
                        new_skeleton = "MM" if skeleton_code == "M" else "dd"
                        english_element_mappings[zero_padded] = [new_skeleton]
                    elif len(eng_token) == 2 and int(eng_token) >= 10:
                        padded_skeleton = "MM" if skeleton_code == "M" else "dd"
                        if eng_token not in english_element_mappings:
                            english_element_mappings[eng_token] = []
                        english_element_mappings[eng_token].append(padded_skeleton)
                
                elif skeleton_code in ["MM", "dd"]:
                    if len(eng_token) == 2 and int(eng_token) >= 10:
                        minimal_skeleton = "M" if skeleton_code == "MM" else "d"
                        if eng_token not in english_element_mappings:
                            english_element_mappings[eng_token] = []
                        english_element_mappings[eng_token].append(minimal_skeleton)
                
                elif skeleton_code == "y" and len(eng_token) == 4:
                    abbreviated_year = eng_token[-2:]
                    english_element_mappings[abbreviated_year] = ["yy"]
                
                elif skeleton_code == "yy" and len(eng_token) == 2:
                    # Look for 4-digit year in target to infer full year
                    target_4digit_years = [token for cat, token, spacing in categorized_target_tokens 
                                         if cat == 'numeric' and len(token) == 4]
                    if target_4digit_years:
                        full_year = target_4digit_years[0]
                        if full_year.endswith(eng_token):
                            english_element_mappings[full_year] = ["y"]
            
            elif any(eng_token.lower() == item.lower() for item in sum(ENGLISH_DATE_DICT.values(), [])):
                # Handle date elements - find ALL variants in target language
                
                # Find which category this English element belongs to
                eng_category = None
                eng_index = None
                for key in ENGLISH_DATE_DICT:
                    for idx, item in enumerate(ENGLISH_DATE_DICT[key]):
                        if item.lower() == eng_token.lower():
                            eng_category = key
                            eng_index = idx
                            break
                    if eng_category:
                        break
                
                if eng_category and eng_index is not None and eng_category in target_date_dict:
                    # Get the target translation for this index
                    if eng_index < len(target_date_dict[eng_category]):
                        target_translation = target_date_dict[eng_category][eng_index]
                        
                        # Now find ALL possible format variants of this translation
                        base_category = eng_category.split('_')[0]  # e.g., 'mon' from 'mon_wid_for'
                        
                        # Define skeleton codes for each format length
                        # Use M codes for formatting context (months within dates)
                        # Use L codes for standalone context (months by themselves)
                        format_skeleton_map = {
                            'mon': {'nar': 'M', 'abb': 'MMM', 'wid': 'MMMM', 'sho': 'MMM'},
                            'day': {'nar': 'c', 'abb': 'ccc', 'wid': 'cccc', 'sho': 'ccc'}
                        }
                        
                        if base_category in format_skeleton_map:
                            # Find all variants of this element in target language
                            for target_key in target_date_dict:
                                if target_key.startswith(base_category):
                                    if eng_index < len(target_date_dict[target_key]):
                                        variant_text = target_date_dict[target_key][eng_index]
                                        
                                        # Determine format length from key
                                        if '_nar_' in target_key:
                                            format_code = format_skeleton_map[base_category]['nar']
                                        elif '_abb_' in target_key:
                                            format_code = format_skeleton_map[base_category]['abb']
                                        elif '_wid_' in target_key:
                                            format_code = format_skeleton_map[base_category]['wid']
                                        elif '_sho_' in target_key:
                                            format_code = format_skeleton_map[base_category]['sho']
                                        else:
                                            continue
                                        
                                        # Store mapping from target variant to its skeleton code
                                        target_element_to_skeleton[variant_text] = format_code
                                        
                                        # Also store in english_element_mappings for compatibility
                                        english_element_mappings[variant_text] = [format_code]
    
    print(f"Target element to skeleton mappings: {target_element_to_skeleton}")
    print(f"English element mappings: {english_element_mappings}")
    
    # Now build target skeleton by processing each target token with spacing preserved
    possible_skeletons = [[]]  # Start with one empty skeleton
    
    # Build a more flexible mapping approach for cases with mismatched token counts
    # due to literal text in target language
    
    # First, identify which target tokens can be mapped to English elements
    mappable_targets = []
    literal_targets = []
    
    for cat, token, spacing in categorized_target_tokens:
        if cat == 'punctuation':
            continue  # Handle punctuation separately
        elif cat == 'literal':
            literal_targets.append((token, spacing))
        elif cat in ['numeric', 'date_element'] and token in english_element_mappings:
            mappable_targets.append((token, english_element_mappings[token], spacing))
        else:
            # Unmappable date element or number - treat as literal
            literal_targets.append((token, spacing))
    
    print(f"Mappable targets: {[(token, codes) for token, codes, spacing in mappable_targets]}")
    print(f"Literal targets: {[token for token, spacing in literal_targets]}")
    
    # If we have mappable targets, generate skeletons
    if mappable_targets:
        # Generate all combinations of skeleton codes for mappable elements
        from itertools import product
        
        all_mapping_options = []
        for token, skeleton_codes, spacing in mappable_targets:
            all_mapping_options.append([(code, spacing) for code in skeleton_codes])
        
        # Generate all combinations
        if all_mapping_options:
            for mapping_combination in product(*all_mapping_options):
                skeleton_parts = []
                
                # Build skeleton by processing tokens in original order
                mappable_index = 0
                literal_index = 0
                
                for cat, token, spacing in categorized_target_tokens:
                    if cat == 'punctuation':
                        # Add punctuation with spacing
                        if spacing['has_space_before'] and skeleton_parts:
                            skeleton_parts.extend([' ', token])
                        else:
                            skeleton_parts.append(token)
                    
                    elif cat == 'literal':
                        # Add literal text wrapped in quotes with spacing
                        quoted_literal = f"'{token}'"
                        if spacing['has_space_before'] and skeleton_parts:
                            skeleton_parts.extend([' ', quoted_literal])
                        else:
                            skeleton_parts.append(quoted_literal)
                    
                    elif cat in ['numeric', 'date_element']:
                        if token in english_element_mappings and mappable_index < len(mapping_combination):
                            # Use the skeleton code from the current mapping combination
                            skeleton_code, code_spacing = mapping_combination[mappable_index]
                            mappable_index += 1
                            
                            if spacing['has_space_before'] and skeleton_parts:
                                skeleton_parts.extend([' ', skeleton_code])
                            else:
                                skeleton_parts.append(skeleton_code)
                        else:
                            # Fallback to literal
                            quoted_literal = f"'{token}'"
                            if spacing['has_space_before'] and skeleton_parts:
                                skeleton_parts.extend([' ', quoted_literal])
                            else:
                                skeleton_parts.append(quoted_literal)
                
                if skeleton_parts:
                    possible_skeletons.append(skeleton_parts)
    
    else:
        # No mappable targets - create skeleton with all literals
        skeleton_parts = []
        for cat, token, spacing in categorized_target_tokens:
            if cat == 'punctuation':
                if spacing['has_space_before'] and skeleton_parts:
                    skeleton_parts.extend([' ', token])
                else:
                    skeleton_parts.append(token)
            else:
                quoted_literal = f"'{token}'"
                if spacing['has_space_before'] and skeleton_parts:
                    skeleton_parts.extend([' ', quoted_literal])
                else:
                    skeleton_parts.append(quoted_literal)
        
        if skeleton_parts:
            possible_skeletons.append(skeleton_parts)
    
    # Remove the empty initial skeleton
    possible_skeletons = [skeleton for skeleton in possible_skeletons if skeleton]
    
    print(f"Possible target skeletons (parts): {possible_skeletons}")
    
    # Convert skeleton parts to strings (just join them, spacing is already handled)
    target_skeleton_strings = []
    for skeleton_parts in possible_skeletons:
        if skeleton_parts:
            result = ''.join(str(part) for part in skeleton_parts)
            if result and result not in target_skeleton_strings:
                target_skeleton_strings.append(result)
    
    print(f"Final target skeleton strings: {target_skeleton_strings}")
    return target_skeleton_strings


# Keep the old functions for backward compatibility but they won't be used
def build_english_token_mappings(english_tokens, english_skeleton_tokens, target_year_candidates, ambiguities):
    """Legacy function - not used in new implementation"""
    pass

def find_valid_target_mappings(target_nonpunct_tokens, eng_token_mapping_options, target_date_dict, ambiguities):
    """Legacy function - not used in new implementation"""
    pass

def reconstruct_target_skeletons(valid_skeleton_sequences, target_tokens):
    """Legacy function - not used in new implementation"""
    pass 