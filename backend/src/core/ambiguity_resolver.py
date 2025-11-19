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
        tuple: (resolved_ambiguities, ambiguity_options)
            - resolved_ambiguities: List of resolved ambiguity info tuples (position, skeleton_code, resolved_value)
            - ambiguity_options: Dict mapping token position to list of option strings
    """
    ambiguities = []
    ambiguity_options = {}
    
    for i_token, token in enumerate(tokens):
        if i_token >= len(skeleton_tokens):
            continue
        
        questions = set()
        from .constants import SKELETON_CODES
        skeleton_code = skeleton_tokens[i_token]
        
        # For standalone single-token inputs, check ALL possible standalone skeleton codes
        # (not just the chosen one) to catch cross-category ambiguities (month vs day)
        is_standalone_single_token = len(tokens) == 1
        
        matching_keys = []
        if is_standalone_single_token:
            # Check all standalone keys that contain this token, regardless of skeleton code
            # This catches cases like "F" (February vs Friday) or "M" (March/May vs Monday)
            for key in ENGLISH_DATE_DICT.keys():
                # Only check standalone keys for single-token inputs
                if key.endswith("_sta"):
                    if any(item.lower() == token.lower() for item in ENGLISH_DATE_DICT[key]):
                        matching_keys.append(key)
        else:
            # For multi-token inputs, only check keys matching the chosen skeleton code
            # This ensures we only check the appropriate context (format vs standalone)
            for key in ENGLISH_DATE_DICT.keys():
                if SKELETON_CODES.get(key) == skeleton_code:
                    # Check if this token appears in this key
                    if any(item.lower() == token.lower() for item in ENGLISH_DATE_DICT[key]):
                        matching_keys.append(key)
        
        # Check for ambiguities: either multiple matches in same key, or matches in different keys
        if len(matching_keys) > 1:
            # Token matches multiple different keys (e.g., "F" matches both month and day)
            # Each key may have a different skeleton code, so we need to track that
            for key in matching_keys:
                option_skeleton_code = SKELETON_CODES.get(key)
                # Generate disambiguation options using wide format
                for j in range(len(ENGLISH_DATE_DICT[key])):
                    if ENGLISH_DATE_DICT[key][j].lower() == token.lower():
                        nkey = key.split("_")[0] + "_wid_" + key.split("_")[2]
                        if nkey in ENGLISH_DATE_DICT:
                            # Store: (option_name, index, key, skeleton_code)
                            question = (ENGLISH_DATE_DICT[nkey][j], j, key, option_skeleton_code)
                            questions.add(question)
        elif len(matching_keys) == 1:
            # Token matches one key, check if it appears multiple times in that key
            key = matching_keys[0]
            option_skeleton_code = SKELETON_CODES.get(key)
            lowercase_count = sum(1 for item in ENGLISH_DATE_DICT[key] if item.lower() == token.lower())
            if lowercase_count > 1:
                # Generate disambiguation options using wide format
                for j in range(len(ENGLISH_DATE_DICT[key])):
                    if ENGLISH_DATE_DICT[key][j].lower() == token.lower():
                        nkey = key.split("_")[0] + "_wid_" + key.split("_")[2]
                        if nkey in ENGLISH_DATE_DICT:
                            # Store: (option_name, index, key, skeleton_code)
                            question = (ENGLISH_DATE_DICT[nkey][j], j, key, option_skeleton_code)
                            questions.add(question)
        
        # Store ambiguity options for user selection
        # Format: {position: [{"name": "...", "skeleton_code": "..."}, ...]}
        if questions:
            questions_list = sorted(list(questions), key=lambda x: (x[3], x[2], x[1]))  # Sort by skeleton_code, key, then index
            # Group by option name and skeleton code to handle cases where same name has different skeleton codes
            option_map = {}  # Maps option_name -> skeleton_code
            unique_options = []
            for q in questions_list:
                option_name = q[0]
                option_skeleton = q[3]
                # If same name appears with different skeleton codes, include both
                if option_name not in option_map:
                    option_map[option_name] = option_skeleton
                    unique_options.append({"name": option_name, "skeleton_code": option_skeleton})
                elif option_map[option_name] != option_skeleton:
                    # Same name but different skeleton code - this shouldn't happen for month/day, but handle it
                    unique_options.append({"name": option_name, "skeleton_code": option_skeleton})
            
            ambiguity_options[i_token] = unique_options
            # Auto-select the first option as default, but user can override
            choice_index = 0
            selected_option = unique_options[choice_index]
            ambig_info = (i_token, selected_option["skeleton_code"], selected_option["name"])
            ambiguities.append(ambig_info)
    
    return ambiguities, ambiguity_options


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
    except KeyError:
        header = []

    translation_column = None
    for candidate in ("Winning", "Translation"):
        if candidate in english_df.columns:
            translation_column = candidate
            break

    if translation_column:
        winning = english_df[translation_column].values.tolist()
    else:
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