# -*- coding: utf-8 -*-
"""
Ambiguity resolution utilities for date expressions

Handles detection and resolution of ambiguous date elements that appear
multiple times in date dictionaries (e.g., "J" could be January, June, or July).
"""

from .constants import ENGLISH_DATE_DICT, MONTH_INDEXING, DAY_INDEXING


def detect_ambiguities(tokens, skeleton_tokens):
    """
    Detect ambiguous tokens that appear multiple times in date dictionaries.
    
    Args:
        tokens (list): Original input tokens
        skeleton_tokens (list): Corresponding skeleton tokens
        
    Returns:
        list: List of ambiguity information tuples
    """
    ambiguities = []
    
    for i_token, token in enumerate(tokens):
        if i_token >= len(skeleton_tokens):
            continue
        
        questions = set()
        # Find matching skeleton code for this position
        for key in ENGLISH_DATE_DICT.keys():
            from .constants import SKELETON_CODES
            if skeleton_tokens[i_token] == SKELETON_CODES.get(key):
                # Check if this token appears multiple times in the date dictionary (case-insensitive)
                if key in ENGLISH_DATE_DICT:
                    lowercase_count = sum(1 for item in ENGLISH_DATE_DICT[key] if item.lower() == token.lower())
                    if lowercase_count > 1:
                        # Generate disambiguation options using wide format
                        for j in range(len(ENGLISH_DATE_DICT[key])):
                            if ENGLISH_DATE_DICT[key][j].lower() == token.lower():
                                nkey = key.split("_")[0] + "_wid_" + key.split("_")[2]
                                if nkey in ENGLISH_DATE_DICT:
                                    question = (ENGLISH_DATE_DICT[nkey][j], j)
                                    questions.add(question)
        
        # Present disambiguation options to user
        if questions:
            print(f"\nFor '{token}', do you mean:")
            questions_list = list(questions)
            for i, question in enumerate(questions_list):
                print(f"{i+1}: {question[0]}")
            
            while True:
                try:
                    ambig_answer = input(f"Enter a number 1-{len(questions_list)}: ")
                    choice_index = int(ambig_answer)
                    if 1 <= choice_index <= len(questions_list):
                        ambig_info = (i_token, skeleton_tokens[i_token], questions_list[choice_index - 1][0])
                        ambiguities.append(ambig_info)
                        break
                    else:
                        print(f"'{ambig_answer}' is not a valid option. Please try again.")
                except ValueError:
                    print(f"'{ambig_answer}' is not a valid number. Please try again.")
    
    return ambiguities


def resolve_ambiguity_in_mapping(token, skeleton_code, ambiguities, date_dict, position):
    """
    Resolve ambiguity using stored disambiguation data during target language mapping.
    
    Args:
        token (str): Token to resolve
        skeleton_code (str): Skeleton code for the token
        ambiguities (list): List of ambiguity resolution data
        date_dict (dict): Target language date dictionary
        position (int): Position of token in sequence
        
    Returns:
        str or None: Resolved translation or None if not found
    """
    # Find disambiguation for this position
    ambiguity_for_position = None
    for amb in ambiguities:
        if amb[0] == position:  # amb[0] is the position
            ambiguity_for_position = amb
            break
    
    if ambiguity_for_position:
        ncode = ambiguity_for_position[2][:3]  # Get first 3 chars
        
        # Find the appropriate key in date_dict
        for key in date_dict.keys():
            from .constants import SKELETON_CODES
            if skeleton_code == SKELETON_CODES.get(key):
                try:
                    if any(char in "ML" for char in skeleton_code):
                        # Month element
                        entry = MONTH_INDEXING.index(ncode.capitalize())
                    elif any(char in "Ec" for char in skeleton_code):
                        # Day element
                        entry = DAY_INDEXING.index(ncode.capitalize())
                    else:
                        continue
                    
                    if entry < len(date_dict[key]):
                        return date_dict[key][entry]
                except (ValueError, IndexError):
                    continue
    
    return None


def get_metadata_for_skeleton(eng_skeleton, ambiguities, english_df):
    """
    Extract CLDR metadata (code and XPath) for the selected English skeleton.
    
    Args:
        eng_skeleton (str): English skeleton pattern
        ambiguities (list): List of ambiguity resolution data
        english_df (pandas.DataFrame): English reference data
        
    Returns:
        list: List of tuples containing (skeleton, codes, xpaths)
    """
    # Extract metadata columns from the DataFrame
    english_possibilities = english_df['English'].values.tolist()
    codes = english_df['Code'].values.tolist()
    xpaths = english_df['XPath'].values.tolist()
    
    # Try to get header and winning columns if they exist
    try:
        header = english_df['Header'].values.tolist()
        winning = english_df['Winning'].values.tolist()
    except KeyError:
        header = []
        winning = []
    
    # Find metadata for the selected English skeleton - collect ALL instances
    all_codes = []
    all_xpaths = []
    
    if eng_skeleton in english_possibilities:
        # Find ALL direct matches in reference data
        for i, possibility in enumerate(english_possibilities):
            if possibility == eng_skeleton:
                all_codes.append(codes[i])
                all_xpaths.append(xpaths[i])
    
    elif len(set(eng_skeleton.lower())) == 1:
        # Handle repeated character patterns with ambiguity resolution
        from .constants import SKELETON_CODES, SKELETON_FULL_NAME
        for key in SKELETON_CODES.keys():
            if eng_skeleton == SKELETON_CODES[key]:
                full_name = SKELETON_FULL_NAME[key]
                if full_name and header and full_name in header:
                    for i, item in enumerate(header):
                        # Check if we have valid ambiguity data
                        ambiguity_match = True
                        if ambiguities and len(ambiguities) > 0:
                            ambiguity_match = codes[i] == ambiguities[0][2][:3].lower()
                        
                        # Match header, code prefix, and winning example
                        if (item == full_name and
                            ambiguity_match and
                            winning and i < len(winning)):
                            all_codes.append(codes[i])
                            all_xpaths.append(xpaths[i])
    
    # Store metadata information for all instances
    if all_codes and all_xpaths:
        return [(eng_skeleton, all_codes, all_xpaths)]
    else:
        return [(eng_skeleton, ["Unknown"], ["Unknown"])] 