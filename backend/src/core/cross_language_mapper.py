
# -*- coding: utf-8 -*-
"""
Cross-language mapping utilities

Handles the complex logic for mapping English date tokens to target language
equivalents, including fuzzy numeric matching, permutation testing, and
ambiguity resolution during cross-language conversion.
"""

from itertools import permutations, product
import regex
from collections import Counter
from .constants import ENGLISH_DATE_DICT, MONTH_INDEXING, DAY_INDEXING, TOKEN_PATTERN, SKELETON_CODES


def has_consistent_formatting(left_skeleton: str, right_skeleton: str) -> bool:
    """
    Check if two skeleton parts have consistent formatting (same number of M's, d's, y's, etc.).
    
    Args:
        left_skeleton (str): Left side of range skeleton (e.g., "MMM d, y")
        right_skeleton (str): Right side of range skeleton (e.g., "EEE, MMM dd, y")
        
    Returns:
        bool: True if formatting is consistent, False otherwise
    """
    # Extract skeleton elements from both sides
    def extract_elements(skeleton):
        # Split on common separators and extract skeleton codes
        parts = regex.split(r'[,\.\-–—\s]+', skeleton)
        elements = []
        for part in parts:
            part = part.strip()
            if part:
                # Extract skeleton codes (M, MM, MMM, MMMM, d, dd, y, yy, E, EEE, etc.)
                codes = regex.findall(r'[M]{1,4}|[d]{1,2}|[y]{1,2}|[E]{1,6}|[L]{1,5}|[c]{1,6}', part)
                elements.extend(codes)
        return elements
    
    left_elements = extract_elements(left_skeleton)
    right_elements = extract_elements(right_skeleton)
    
    # Group elements by type
    def group_by_type(elements):
        groups = {}
        for elem in elements:
            if elem.startswith('M'):
                groups['M'] = groups.get('M', []) + [elem]
            elif elem.startswith('d'):
                groups['d'] = groups.get('d', []) + [elem]
            elif elem.startswith('y'):
                groups['y'] = groups.get('y', []) + [elem]
            elif elem.startswith('E'):
                groups['E'] = groups.get('E', []) + [elem]
            elif elem.startswith('L'):
                groups['L'] = groups.get('L', []) + [elem]
            elif elem.startswith('c'):
                groups['c'] = groups.get('c', []) + [elem]
        return groups
    
    left_groups = group_by_type(left_elements)
    right_groups = group_by_type(right_elements)
    
    # Check consistency for each element type
    for elem_type in ['M', 'd', 'y', 'E', 'L', 'c']:
        left_elems = left_groups.get(elem_type, [])
        right_elems = right_groups.get(elem_type, [])
        
        # If both sides have this element type, check consistency
        if left_elems and right_elems:
            # Get the most common length for each side
            left_lengths = [len(elem) for elem in left_elems]
            right_lengths = [len(elem) for elem in right_elems]
            
            # Use the most frequent length for each side
            left_most_common = Counter(left_lengths).most_common(1)[0][0] if left_lengths else 0
            right_most_common = Counter(right_lengths).most_common(1)[0][0] if right_lengths else 0
            
            # If lengths don't match, this combination is inconsistent
            if left_most_common != right_most_common:
                return False
    
    return True


def validate_english_date_values(english_tokens, english_skeleton):
    """
    Validate that numeric date values in English expression are within valid ranges.
    
    Args:
        english_tokens (list): Tokenized English expression
        english_skeleton (str): English skeleton pattern
        
    Raises:
        ValueError: If month > 12 or day > 31
    """
    import regex
    
    # Tokenize skeleton and expression
    pattern = r'[\p{L}\p{M}]+\.?|\p{N}+|[/,\.\-–—،፣]'
    skeleton_tokens = regex.findall(pattern, english_skeleton)

    # Helper to extract only date element codes from a skeleton token list
    def extract_element_codes(tokens_list):
        return [t for t in tokens_list if t in ['M','MM','d','dd','y','yy']]

    # Helper to get numeric tokens (as ints) from a token list
    def extract_numeric_values(tokens_list):
        return [int(t) for t in tokens_list if t.isdigit()]

    if '-' in english_skeleton or '–' in english_skeleton:
        # Split skeleton and tokens into sides and validate side-by-side
        sk_parts = english_skeleton.replace('–','-').split('-')
        # Split english_tokens by dash occurrence
        if '-' in english_tokens:
            dash_idx = english_tokens.index('-')
        elif '–' in english_tokens:
            dash_idx = english_tokens.index('–')
        else:
            dash_idx = -1

        if len(sk_parts) == 2 and dash_idx != -1:
            left_tokens = english_tokens[:dash_idx]
            right_tokens = english_tokens[dash_idx+1:]

            left_codes = extract_element_codes(regex.findall(pattern, sk_parts[0]))
            right_codes = extract_element_codes(regex.findall(pattern, sk_parts[1]))

            for side_idx, (vals, codes) in enumerate(((extract_numeric_values(left_tokens), left_codes),
                                                      (extract_numeric_values(right_tokens), right_codes)), start=1):
                # Validate length alignment defensively
                n = min(len(vals), len(codes))
                for i in range(n):
                    v = vals[i]
                    c = codes[i]
                    if c.startswith('M') and v > 12:
                        raise ValueError(f"Invalid month value: {v} (must be 1-12) in side {side_idx}")
                    if c.startswith('d') and v > 31:
                        raise ValueError(f"Invalid day value: {v} (must be 1-31) in side {side_idx}")
        # If we cannot split properly, skip validation (numeric fast path will catch later)
        return
    else:
        # Single date expression - align numbers to element codes in order
        vals = extract_numeric_values(english_tokens)
        codes = extract_element_codes(skeleton_tokens)
        n = min(len(vals), len(codes))
        for i in range(n):
            v = vals[i]
            c = codes[i]
            if c.startswith('M') and v > 12:
                raise ValueError(f"Invalid month value: {v} (must be 1-12)")
            if c.startswith('d') and v > 31:
                raise ValueError(f"Invalid day value: {v} (must be 1-31)")


def generate_month_day_permutations(numeric_tokens, english_skeleton, english_tokens):
    """
    Generate all valid month/day permutations for numeric tokens based on English skeleton mapping.
    
    Args:
        numeric_tokens (list): List of (token, value) tuples from target
        english_skeleton (str): English skeleton pattern
        english_tokens (list): English tokens
        
    Returns:
        list: List of skeleton code permutations
    """
    import regex
    
    # Tokenize English skeleton to get the pattern
    pattern = r'[\p{L}\p{M}]+\.?|\p{N}+|[/,\.\-–—،፣]'
    skeleton_tokens = regex.findall(pattern, english_skeleton)
    
    # Extract numeric skeleton elements (M, d, y, etc.)
    skeleton_elements = [token for token in skeleton_tokens if token in ['M', 'MM', 'd', 'dd', 'y', 'yy']]
    
    # Create mapping from English numeric tokens to their skeleton elements
    english_numeric_to_skeleton = {}
    skeleton_index = 0
    for i, token in enumerate(english_tokens):
        if token.isdigit() and skeleton_index < len(skeleton_elements):
            english_numeric_to_skeleton[token] = skeleton_elements[skeleton_index]
            skeleton_index += 1
    
    # Map each target numeric token to its corresponding English skeleton element
    target_to_skeleton_mapping = []
    for token, value in numeric_tokens:
        # Find which English numeric token this target token corresponds to
        corresponding_english_token = None
        for eng_token in english_numeric_to_skeleton:
            if eng_token == token:  # Exact match
                corresponding_english_token = eng_token
                break
        
        if corresponding_english_token:
            skeleton_element = english_numeric_to_skeleton[corresponding_english_token]
            target_to_skeleton_mapping.append((token, value, skeleton_element))
        else:
            # No direct match found - this might be a reordering case
            # For now, just use the first available skeleton element
            if skeleton_index < len(skeleton_elements):
                skeleton_element = skeleton_elements[skeleton_index]
                target_to_skeleton_mapping.append((token, value, skeleton_element))
                skeleton_index += 1
    
    # Generate skeleton codes based on the mapping and the rules
    def get_skeleton_codes_for_element(token, value, skeleton_element):
        """Get possible skeleton codes based on the English element and target value."""
        codes = []
        
        if skeleton_element.startswith('M'):  # Month element
            if len(token) == 1 and value < 10:
                codes.append('M')  # Single digit, single letter
            elif len(token) == 2 and token.startswith('0') and value < 10:
                codes.append('MM')  # Zero-padded, double letter
            elif len(token) == 2 and value >= 10:
                codes.extend(['M', 'MM'])  # Double digit, could be either
            else:
                codes.append('M')  # Default
        
        elif skeleton_element.startswith('d'):  # Day element
            if len(token) == 1 and value < 10:
                codes.append('d')  # Single digit, single letter
            elif len(token) == 2 and token.startswith('0') and value < 10:
                codes.append('dd')  # Zero-padded, double letter
            elif len(token) == 2 and value >= 10:
                codes.extend(['d', 'dd'])  # Double digit, could be either
            else:
                codes.append('d')  # Default
        
        elif skeleton_element.startswith('y'):  # Year element
            if len(token) == 2:
                codes.append('yy')
            elif len(token) == 4:
                codes.append('y')
            else:
                codes.append('y')  # Default
        
        return codes
    
    # Generate all combinations of skeleton codes
    from itertools import product
    
    all_code_combinations = []
    for token, value, skeleton_element in target_to_skeleton_mapping:
        codes = get_skeleton_codes_for_element(token, value, skeleton_element)
        all_code_combinations.append(codes)
    
    # Generate all valid combinations
    permutations = []
    for combination in product(*all_code_combinations):
        permutations.append(list(combination))
    
    return permutations


def map_english_to_target_skeleton(english_tokens, english_skeleton, target_tokens, target_date_dict, ambiguities=None, original_target_expression=None):
    """
    Map English date expression to target language skeleton.
    
    Args:
        english_tokens (list): Tokenized English expression
        english_skeleton (str): English skeleton pattern
        target_tokens (list): Tokenized target language expression
        target_date_dict (dict): Target language date dictionary
        ambiguities (list): Ambiguity resolution data
        original_target_expression (str): Original target expression for error messages
        
    Returns:
        list: List of valid target skeleton strings
    """
    # Validate English date values first
    validate_english_date_values(english_tokens, english_skeleton)
    
    # Initialize variables
    if ambiguities is None:
        ambiguities = []
    
    print(f"Target tokenized: {target_tokens}")
    print(f"English skeleton: {english_skeleton}")
    
    # Tokenize English skeleton for mapping
    english_skeleton_tokenized = regex.findall(TOKEN_PATTERN, english_skeleton)
    print(f"English skeleton tokenized: {english_skeleton_tokenized}")
    
    english_tokenized = regex.findall(TOKEN_PATTERN, " ".join(english_tokens))
    print(f"English tokenized: {english_tokenized}")

    # ------------------------------------------------------------------
    # Special-case fast path: numeric-only dates with separators (M/d[/y], ranges)
    # Implements the user's Made-Up skeleton spec precisely for numeric cases
    # ------------------------------------------------------------------
    def is_numeric_only(tokens):
        return all(t.isdigit() or t in [",", "/", "-", "–", "."] for t in tokens)

    def skeleton_is_numeric_only(tokens):
        allowed = {"M", "MM", "d", "dd", "y", "yy", ",", "/", "-", "–", "."}
        return all(t in allowed for t in tokens)

    english_skeleton_tokens_simple = regex.findall(TOKEN_PATTERN, english_skeleton)

    if is_numeric_only(target_tokens) and is_numeric_only(english_tokenized) and skeleton_is_numeric_only(english_skeleton_tokens_simple):
        print("Using numeric-only mapping fast path")

        def detect_separator(expr_tokens):
            for s in ["/", ".", "-", "–"]:
                if s in expr_tokens:
                    return s
            return "/"

        def split_components(tokens, sep):
            comps = []
            current = []
            for t in tokens:
                if t == sep:
                    if current:
                        comps.append("".join(current))
                        current = []
                else:
                    if t.isdigit():
                        current.append(t)
            if current:
                comps.append("".join(current))
            return comps

        def parse_int_list(str_list):
            try:
                return [int(x) for x in str_list]
            except Exception:
                return None

        # Handle ranges by splitting both sides and cross-product later
        def split_range(tokens):
            if "-" in tokens or "–" in tokens:
                dash = "-" if "-" in tokens else "–"
                idx = tokens.index(dash)
                return tokens[:idx], tokens[idx+1:], dash
            return None, None, None

        # Build mapping from English values to skeleton components preserving duplicates
        def build_english_value_to_components(eng_tokens, eng_skel_tokens):
            values = [int(t) for t in eng_tokens if t.isdigit()]
            comps = [t for t in eng_skel_tokens if t in ["M","MM","d","dd","y","yy"]]
            pairs = []
            vi = 0
            for t in eng_tokens:
                if t.isdigit():
                    if vi < len(comps):
                        pairs.append((int(t), comps[vi]))
                        vi += 1
            return pairs  # list of (value, component) in order

        # Validate English numeric bounds explicitly (month<=12, day<=31)
        eng_pairs_full = build_english_value_to_components(english_tokenized, english_skeleton_tokens_simple)
        for val, comp in eng_pairs_full:
            if comp.startswith('M') and val > 12:
                raise ValueError("Invalid month value in English example (must be 1-12)")
            if comp.startswith('d') and val > 31:
                raise ValueError("Invalid day value in English example (must be 1-31)")

        def formats_for(value_str, comp_type):
            # Apply formatting rules from spec
            if comp_type.startswith("y"):
                return ["y"] if len(value_str) == 4 else (["yy"] if len(value_str) == 2 else [])
            if comp_type.startswith("M"):
                if len(value_str) == 1:
                    return ["M"]
                if len(value_str) == 2 and value_str.startswith("0"):
                    return ["MM"]
                if len(value_str) == 2:
                    return ["M","MM"]
            if comp_type.startswith("d"):
                if len(value_str) == 1:
                    return ["d"]
                if len(value_str) == 2 and value_str.startswith("0"):
                    return ["dd"]
                if len(value_str) == 2:
                    return ["d","dd"]
            return []

        def generate_for_side(eng_side_tokens, eng_skel_side, tgt_side_tokens):
            sep = detect_separator(tgt_side_tokens)
            eng_vals = [t for t in eng_side_tokens if t.isdigit()]
            tgt_vals = [t for t in tgt_side_tokens if t.isdigit()]
            if not eng_vals or not tgt_vals:
                return []
            eng_pairs = build_english_value_to_components(eng_side_tokens, regex.findall(TOKEN_PATTERN, eng_skel_side))
            # Count availability of each value's component types
            from collections import defaultdict
            value_to_components = defaultdict(list)
            for val, comp in eng_pairs:
                value_to_components[val].append(comp)
            
            # Helper to find available component types for a target value string
            def available_components_for_target(v_str: str):
                iv = int(v_str)
                comps = list(value_to_components.get(iv, []))
                # Year truncation allowance: if target is 2-digit and matches last-2 of an English year
                if len(v_str) == 2:
                    for ev, ec in eng_pairs:
                        if str(ev).isdigit() and len(str(ev)) == 4 and (ev % 100) == iv and ec.startswith('y'):
                            # Treat as a year component available
                            comps.append('y')
                            break
                # Year expansion allowance: if target is 4-digit and its last-2 match an English yy
                if len(v_str) == 4:
                    last2 = int(v_str[-2:])
                    for ev, ec in eng_pairs:
                        if ec == 'yy' and ev == last2:
                            comps.append('y')
                            break
                return comps

            # Validate mapping existence per target value
            for v in tgt_vals:
                if not available_components_for_target(v):
                    return []
            # Backtracking to assign components to target occurrences while respecting multiplicity
            results = []
            assigned = []
            used_counts = defaultdict(int)

            def backtrack(idx):
                if idx == len(tgt_vals):
                    results.append(list(assigned))
                    return
                v_str = tgt_vals[idx]
                comps_avail = available_components_for_target(v_str)
                # Try each remaining component instance
                tried = 0
                for comp in comps_avail:
                    key = (v_str, comp)
                    # Compute total allowed count for this comp for this value_str
                    # If comp came from exact matches, count them; if from year-truncation, allow one use
                    total_allowed = 0
                    if comp == 'y' and len(v_str) == 2 and comp not in value_to_components.get(int(v_str), []):
                        total_allowed = 1
                    else:
                        # exact matches count
                        total_allowed = value_to_components[int(v_str)].count(comp) if v_str.isdigit() else 0
                    if used_counts[key] < max(1, total_allowed):
                        # Determine format options for this target value and component type
                        opts = formats_for(v_str, comp)
                        if not opts:
                            continue
                        for o in opts:
                            assigned.append(o)
                            used_counts[key] += 1
                            backtrack(idx+1)
                            used_counts[key] -= 1
                            assigned.pop()
                        tried += 1
                if tried == 0:
                    return

            backtrack(0)
            # Rebuild skeleton strings with separator retained
            skeletons = [sep.join(r) for r in results]
            # Note: Removed overly restrictive filtering that was preventing valid combinations like M/dd/y
            # The previous filter was removing valid skeleton options where numbers > 9 create ambiguity
            # All generated combinations should be valid since the backtracking already ensures correctness
            filtered = skeletons
            # De-dup
            return sorted(list(dict.fromkeys(filtered)))

        # Range handling
        e_left, e_right, dash = split_range(english_tokenized)
        t_left, t_right, dash_t = split_range(target_tokens)

        # Treat as a range ONLY if both sides clearly have a dash
        if dash and dash_t:
            if not (e_left and e_right and t_left and t_right):
                pass  # fall through to generic path
            else:
                eng_skel_parts = english_skeleton.replace("–","-").split("-")
                if len(eng_skel_parts) == 2:
                    left_opts = generate_for_side(e_left, eng_skel_parts[0].strip(), t_left)
                    right_opts = generate_for_side(e_right, eng_skel_parts[1].strip(), t_right)
                    if not left_opts or not right_opts:
                        raise ValueError("Inadequate mapping of numeric elements in range")
                    out = []
                    for a in left_opts:
                        for b in right_opts:
                            # Check for formatting consistency between left and right sides
                            if has_consistent_formatting(a, b):
                                out.append(f"{a} - {b}")
                    print(f"Final target skeleton strings: {out}")
                    return out
        else:
            opts = generate_for_side(english_tokenized, english_skeleton, target_tokens)
            if not opts:
                raise ValueError("Inadequate mapping of numeric elements. The translation does not properly correspond to the English expression.")
            print(f"Final target skeleton strings: {opts}")
            return opts
    
    # Analyze original target expression to preserve spacing
    if original_target_expression is None:
        # Fallback to reconstructed expression (old behavior)
        original_target_expression = " ".join(target_tokens)
    
    spacing_info = []
    
    # Track spacing between tokens in the original expression
    current_pos = 0
    for i, token in enumerate(target_tokens):
        # Handle ATTACHED tokens
        actual_token = token[9:] if token.startswith("ATTACHED:") else token
        
        # Find the actual token in the original expression
        token_start = original_target_expression.find(actual_token, current_pos)
        
        if i > 0:
            # Check if there's a space before this token
            prev_token_end = spacing_info[i-1]['end']
            has_space_before = token_start > prev_token_end
            spacing_info.append({
                'token': token,
                'start': token_start,
                'end': token_start + len(actual_token),
                'has_space_before': has_space_before
            })
        else:
            spacing_info.append({
                'token': token,
                'start': token_start,
                'end': token_start + len(actual_token),
                'has_space_before': False
            })
        
        current_pos = token_start + len(actual_token)
    
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
        elif token in [",", "/", "-", "–", ".", "،", "؛", "؟", "！", "？", "。", "ฯ", "ๆ", "־", "፣", "።", "፤", "፥", "፦", "፧", "፨"]:
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
                        # Use E codes for formatting context (days within dates)
                        # Use c codes for standalone context (days by themselves)
                        format_skeleton_map = {
                            'mon': {'nar': 'M', 'abb': 'MMM', 'wid': 'MMMM', 'sho': 'MMM'},
                            'day': {'nar': 'E', 'abb': 'EEE', 'wid': 'EEEE', 'sho': 'EEE'}
                        }
                        
                        # Define skeleton codes for standalone context
                        standalone_skeleton_map = {
                            'mon': {'nar': 'L', 'abb': 'LLL', 'wid': 'LLLL', 'sho': 'LLL'},
                            'day': {'nar': 'c', 'abb': 'ccc', 'wid': 'cccc', 'sho': 'ccc'}
                        }
                        
                        if base_category in format_skeleton_map:
                            # Find all variants of this element in target language
                            for target_key in target_date_dict:
                                if target_key.startswith(base_category):
                                    if eng_index < len(target_date_dict[target_key]):
                                        variant_text = target_date_dict[target_key][eng_index]
                                        
                                        # Determine format length from key and context
                                        if '_nar_' in target_key:
                                            length_code = 'nar'
                                        elif '_abb_' in target_key:
                                            length_code = 'abb'
                                        elif '_wid_' in target_key:
                                            length_code = 'wid'
                                        elif '_sho_' in target_key:
                                            length_code = 'sho'
                                        else:
                                            continue
                                        
                                        # Determine context based on English skeleton, not target key
                                        # Check if the English skeleton uses standalone context (L/c codes) or formatting context (M/E codes)
                                        english_uses_standalone = any(code.startswith('L') or code.startswith('c') for code in english_skeleton_tokenized)
                                        
                                        if english_uses_standalone:
                                            # English uses standalone context - use L/c codes
                                            format_code = standalone_skeleton_map[base_category][length_code]
                                        else:
                                            # English uses formatting context - use M/E codes
                                            format_code = format_skeleton_map[base_category][length_code]
                                        
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
    
    # Generate all valid skeleton permutations for numeric tokens
    if mappable_targets:
        # Extract numeric tokens and their values
        numeric_tokens = [(token, int(token)) for token, codes, spacing in mappable_targets if token.isdigit()]
        
        if len(numeric_tokens) >= 2:
            # Generate all valid month/day permutations
            valid_permutations = generate_month_day_permutations(numeric_tokens, english_skeleton, english_tokenized)
            
            for permutation in valid_permutations:
                skeleton_parts = []
                mappable_index = 0
                
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
                        if token.isdigit() and mappable_index < len(permutation):
                            # Use the skeleton code from the permutation
                            skeleton_code = permutation[mappable_index]
                            mappable_index += 1
                            
                            if spacing['has_space_before'] and skeleton_parts:
                                skeleton_parts.extend([' ', skeleton_code])
                            else:
                                skeleton_parts.append(skeleton_code)
                        elif token in english_element_mappings:
                            # Use the first available skeleton code
                            skeleton_code = english_element_mappings[token][0]
                            
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
            # Handle case with only one numeric token (like just a year)
            skeleton_parts = []
            mappable_index = 0
            
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
                    # Find the correct mappable target for this token
                    target_found = False
                    for i, (mappable_token, mappable_codes, mappable_spacing) in enumerate(mappable_targets):
                        if mappable_token == token:
                            if token.isdigit():
                                # Use the first available skeleton code for numeric tokens
                                skeleton_code = mappable_codes[0]
                            else:
                                # Use the first available skeleton code for date elements
                                skeleton_code = mappable_codes[0]
                            
                            if spacing['has_space_before'] and skeleton_parts:
                                skeleton_parts.extend([' ', skeleton_code])
                            else:
                                skeleton_parts.append(skeleton_code)
                            target_found = True
                            break
                    
                    if not target_found:
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
    
    # Apply consistency filtering for range expressions
    if ' - ' in english_skeleton or '–' in english_skeleton or '—' in english_skeleton:
        filtered_skeletons = []
        for skeleton in target_skeleton_strings:
            # Check if this is a range skeleton
            if ' - ' in skeleton or '–' in skeleton or '—' in skeleton:
                # Split into left and right parts
                if ' - ' in skeleton:
                    left, right = skeleton.split(' - ', 1)
                elif '–' in skeleton:
                    left, right = skeleton.split('–', 1)
                elif '—' in skeleton:
                    left, right = skeleton.split('—', 1)
                else:
                    filtered_skeletons.append(skeleton)
                    continue
                
                # Check consistency
                if has_consistent_formatting(left.strip(), right.strip()):
                    filtered_skeletons.append(skeleton)
            else:
                # Not a range skeleton, keep it
                filtered_skeletons.append(skeleton)
        
        target_skeleton_strings = filtered_skeletons
    
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
