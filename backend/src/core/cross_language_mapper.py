
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
    used_english_tokens = set()  # Track which English tokens have been used
    
    for token, value in numeric_tokens:
        # Find which English numeric token this target token corresponds to
        corresponding_english_token = None
        
        # First, try to find an exact match that hasn't been used yet
        for eng_token in english_numeric_to_skeleton:
            if eng_token == token and eng_token not in used_english_tokens:
                corresponding_english_token = eng_token
                break
        
        if corresponding_english_token:
            # Found an exact match
            skeleton_element = english_numeric_to_skeleton[corresponding_english_token]
            target_to_skeleton_mapping.append((token, value, skeleton_element))
            used_english_tokens.add(corresponding_english_token)
        else:
            # No exact match found - this might be a reordering case
            # Try to find the best match based on value ranges and positions
            best_match = None
            best_score = -1
            
            for eng_token in english_numeric_to_skeleton:
                if eng_token in used_english_tokens:
                    continue
                
                eng_value = int(eng_token)
                score = 0
                
                # Score based on value similarity
                if eng_value == value:
                    score += 100  # Exact value match
                elif 1 <= eng_value <= 12 and 1 <= value <= 12:
                    score += 50   # Both are in month range
                elif 1 <= eng_value <= 31 and 1 <= value <= 31:
                    score += 30   # Both are in day range
                elif eng_value >= 1000 and value >= 1000:
                    score += 40   # Both are years
                
                # Score based on length similarity
                if len(eng_token) == len(token):
                    score += 20
                
                if score > best_score:
                    best_score = score
                    best_match = eng_token
            
            if best_match:
                skeleton_element = english_numeric_to_skeleton[best_match]
                target_to_skeleton_mapping.append((token, value, skeleton_element))
                used_english_tokens.add(best_match)
            else:
                # Fallback: use the next available skeleton element
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
        # Validate that no duplicate element types exist in the combination
        # Check for duplicate M, d, or y elements
        element_types = []
        for code in combination:
            if code.startswith('M'):
                element_types.append('M')
            elif code.startswith('d'):
                element_types.append('d')
            elif code.startswith('y'):
                element_types.append('y')
        
        # Only add combinations that don't have duplicate element types
        if len(element_types) == len(set(element_types)):
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
    
    # Tokenize English skeleton for mapping
    english_skeleton_tokenized = regex.findall(TOKEN_PATTERN, english_skeleton)
    
    english_tokenized = regex.findall(TOKEN_PATTERN, " ".join(english_tokens))

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

    # Define generate_for_side function outside the fast path so it can be used by both paths
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
                        # Only add 'y' if 'yy' is not already present
                        if 'y' not in comps and 'yy' not in comps:
                            comps.append('y')
                        break
            # Year expansion allowance: if target is 4-digit and its last-2 match an English yy
            if len(v_str) == 4:
                last2 = int(v_str[-2:])
                for ev, ec in eng_pairs:
                    if ec == 'yy' and ev == last2:
                        # Only add 'y' if it's not already present and if 'yy' is not already present
                        if 'y' not in comps and 'yy' not in comps:
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
        
        # Filter out combinations with duplicate element types
        filtered = []
        for skeleton in skeletons:
            element_types = []
            year_elements = []
            for part in skeleton.split('/'):
                if part.startswith('M'):
                    element_types.append('M')
                elif part.startswith('d'):
                    element_types.append('d')
                elif part.startswith('y'):
                    element_types.append('y')
                    year_elements.append(part)
            
            # Only add skeletons without duplicate element types
            # Also check that we don't have both 'y' and 'yy' in the same skeleton
            if len(element_types) == len(set(element_types)) and len(set(year_elements)) == len(year_elements):
                filtered.append(skeleton)
            else:
                # Log invalid skeleton for debugging
                print(f"Rejecting invalid skeleton with duplicate elements: {skeleton}")
        
        # If no valid skeletons remain, this indicates an error in the mapping
        if not filtered:
            raise ValueError(f"Invalid skeleton generated: all options contain duplicate element types within a single side")
        
        # De-dup
        return sorted(list(dict.fromkeys(filtered)))

    def detect_separator(expr_tokens):
        for s in ["/", ".", "-", "–"]:
            if s in expr_tokens:
                return s
        return "/"

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
                return ["MM"]  # Only return MM for double-digit months to match original format
        if comp_type.startswith("d"):
            if len(value_str) == 1:
                return ["d"]
            if len(value_str) == 2 and value_str.startswith("0"):
                return ["dd"]
            if len(value_str) == 2:
                return ["dd"]  # Only return dd for double-digit days to match original format
        return []

        if is_numeric_only(target_tokens) and is_numeric_only(english_tokenized) and skeleton_is_numeric_only(english_skeleton_tokens_simple):
            # Handle ranges by splitting both sides and cross-product later
            def split_range(tokens):
                if "-" in tokens or "–" in tokens:
                    dash = "-" if "-" in tokens else "–"
                    idx = tokens.index(dash)
                    return tokens[:idx], tokens[idx+1:], dash
                return None, None, None

        # Validate English numeric bounds explicitly (month<=12, day<=31)
        eng_pairs_full = build_english_value_to_components(english_tokenized, english_skeleton_tokens_simple)
        for val, comp in eng_pairs_full:
            if comp.startswith('M') and val > 12:
                raise ValueError("Invalid month value in English example (must be 1-12)")
            if comp.startswith('d') and val > 31:
                raise ValueError("Invalid day value in English example (must be 1-31)")

        # Range handling
        e_left, e_right, dash = split_range(english_tokenized)
        t_left, t_right, dash_t = split_range(target_tokens)
        
        # Treat as a range if both sides clearly have a dash
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
                                combined = f"{a}{dash_t}{b}"
                                # Only check within each side, not across the entire range
                                left_side = a.split('/')
                                right_side = b.split('/')
                                
                                left_element_types = []
                                right_element_types = []
                                
                                for subpart in left_side:
                                    if subpart.startswith('M'):
                                        left_element_types.append('M')
                                    elif subpart.startswith('d'):
                                        left_element_types.append('d')
                                    elif subpart.startswith('y'):
                                        left_element_types.append('y')
                                
                                for subpart in right_side:
                                    if subpart.startswith('M'):
                                        right_element_types.append('M')
                                    elif subpart.startswith('d'):
                                        right_element_types.append('d')
                                    elif subpart.startswith('y'):
                                        right_element_types.append('y')
                                
                                # Only add if no duplicate element types within each side
                                if len(left_element_types) == len(set(left_element_types)) and len(right_element_types) == len(set(right_element_types)):
                                    out.append(combined)
                    return out
        
        # Handle non-range numeric expressions (e.g., with slashes)
        else:
            # For non-range expressions, use the generate_for_side function for the entire expression
            result = generate_for_side(english_tokenized, english_skeleton, target_tokens)
            if result:
                return result
            else:
                # If generate_for_side fails, fall through to generic path
                pass
    
    # If we get here, we need to use the generic path
    # This handles expressions with day-of-week, literals, and numeric components
        # If we get here, we need to use the generic path
        # This handles expressions with day-of-week, literals, and numeric components
    
    # Tokenize the English skeleton to understand the structure
    english_skeleton_tokenized = regex.findall(TOKEN_PATTERN, english_skeleton)
    
    # Create mapping from English date elements to all their target language variants
    english_to_target_variants = {}
    target_element_to_skeleton = {}
    english_element_mappings = {}  # Initialize the dictionary
    
    # For each English token, find all possible target language variants
    
    for i, eng_token in enumerate(english_tokens):
        if i < len(english_skeleton_tokenized):
            skeleton_code = english_skeleton_tokenized[i]
            
            # Handle day-of-week components (E, EE, EEE, EEEE, EEEEE, EEEEEE)
            if skeleton_code.startswith('E'):
                # Look for day-of-week translations in target language
                if eng_token.lower() in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 
                                       'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                                       'mon.', 'tue.', 'wed.', 'thu.', 'fri.', 'sat.', 'sun.',
                                       'm', 't', 'w', 'th', 'f', 's', 'su']:
                    # Find corresponding day-of-week in target language
                    for target_token in target_tokens:
                        if target_token in target_date_dict.get('day_abb_for', []) or \
                           target_token in target_date_dict.get('day_nar_for', []) or \
                           target_token in target_date_dict.get('day_wid_for', []) or \
                           target_token in target_date_dict.get('day_sho_for', []):
                            target_element_to_skeleton[target_token] = skeleton_code
                            english_element_mappings[target_token] = [skeleton_code]
                            break
                continue
            
            # Handle month components (M, MM, MMM, MMMM)
            elif skeleton_code.startswith('M'):
                # Look for month translations in target language
                if eng_token.lower() in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                                       'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']:
                    # Find corresponding month in target language
                    for target_token in target_tokens:
                        if target_token in target_date_dict.get('mon_abb_for', []) or \
                           target_token in target_date_dict.get('mon_nar_for', []) or \
                           target_token in target_date_dict.get('mon_wid_for', []) or \
                           target_token in target_date_dict.get('mon_sho_for', []):
                            target_element_to_skeleton[target_token] = skeleton_code
                            english_element_mappings[target_token] = [skeleton_code]
                            break
                else:
                    # Handle numeric month tokens
                    target_numeric_tokens = [t for t in target_tokens if t.isnumeric()]
                    english_numeric_tokens = [t for t in english_tokens if t.isnumeric()]
                    
                    # Find the position of this numeric token in the English tokens
                    numeric_index = english_numeric_tokens.index(eng_token)
                    if numeric_index < len(target_numeric_tokens):
                        target_token = target_numeric_tokens[numeric_index]
                        target_element_to_skeleton[target_token] = skeleton_code
                        english_element_mappings[target_token] = [skeleton_code]
                continue
            
            # Handle numeric components (d, dd, y, yy)
            elif skeleton_code in ['d', 'dd', 'y', 'yy']:
                # For numeric components, we need to map based on position and value
                # Map to corresponding target language numeric tokens
                target_numeric_tokens = [t for t in target_tokens if t.isnumeric()]
                english_numeric_tokens = [t for t in english_tokens if t.isnumeric()]
                
                # Find the position of this numeric token in the English tokens
                numeric_index = english_numeric_tokens.index(eng_token)
                if numeric_index < len(target_numeric_tokens):
                    target_token = target_numeric_tokens[numeric_index]
                    target_element_to_skeleton[target_token] = skeleton_code
                    english_element_mappings[target_token] = [skeleton_code]
                continue
            
            elif eng_token.isnumeric():
                # Handle numeric tokens with proper mapping for reordering
                # Get the English skeleton structure to understand the order
                english_numeric_positions = []
                for j, skel_code in enumerate(english_skeleton_tokenized):
                    if skel_code in ['d', 'dd', 'M', 'MM', 'y', 'yy']:
                        english_numeric_positions.append((j, skel_code))
                
                # Find the position of this numeric token in the English skeleton
                current_pos = None
                for j, (pos, skel_code) in enumerate(english_numeric_positions):
                    if j < len([t for t in english_tokens[:i+1] if t.isnumeric()]):
                        current_pos = pos
                        break
                
                # Map to corresponding target language numeric tokens
                target_numeric_tokens = [t for t in target_tokens if t.isnumeric()]
                english_numeric_tokens = [t for t in english_tokens if t.isnumeric()]
                
                # Check if the numeric values are the same but in different positions (reordering case)
                if (len(target_numeric_tokens) == len(english_numeric_tokens) and 
                    set(target_numeric_tokens) == set(english_numeric_tokens)):
                    # Values are the same but potentially reordered, map by value
                    for target_token in target_tokens:
                        if target_token.isnumeric() and target_token == eng_token:
                            target_element_to_skeleton[target_token] = skeleton_code
                            english_element_mappings[target_token] = [skeleton_code]
                            break
                elif len(target_numeric_tokens) == len([t for t in english_tokens if t.isnumeric()]):
                    # Same number of numeric tokens, map by position
                    numeric_index = len([t for t in english_tokens[:i] if t.isnumeric()])
                    if numeric_index < len(target_numeric_tokens):
                        target_token = target_numeric_tokens[numeric_index]
                        target_element_to_skeleton[target_token] = skeleton_code
                        english_element_mappings[target_token] = [skeleton_code]
                else:
                    # Different number of numeric tokens, try to map by value
                    for target_token in target_tokens:
                        if target_token.isnumeric() and target_token == eng_token:
                            target_element_to_skeleton[target_token] = skeleton_code
                            english_element_mappings[target_token] = [skeleton_code]
                            break
                
                # Add numeric variations
                if eng_token in english_element_mappings:
                    for target_token in english_element_mappings[eng_token]:
                        if target_token.startswith('d'):
                            if len(eng_token) == 1:
                                english_element_mappings[eng_token].extend(['d'])
                            elif len(eng_token) == 2:
                                if eng_token.startswith('0'):
                                    english_element_mappings[eng_token].extend(['dd'])
                                else:
                                    english_element_mappings[eng_token].extend(['d', 'dd'])
                        elif target_token.startswith('M'):
                            if len(eng_token) == 1:
                                english_element_mappings[eng_token].extend(['M'])
                            elif len(eng_token) == 2:
                                if eng_token.startswith('0'):
                                    english_element_mappings[eng_token].extend(['MM'])
                                else:
                                    english_element_mappings[eng_token].extend(['M', 'MM'])
                        elif target_token.startswith('y'):
                            if len(eng_token) == 4:
                                english_element_mappings[eng_token].extend(['y'])
                            elif len(eng_token) == 2:
                                english_element_mappings[eng_token].extend(['yy'])
            else:
                # Handle literal tokens (commas, spaces, etc.)
                # Map literal tokens directly
                for target_token in target_tokens:
                    if target_token == eng_token:
                        target_element_to_skeleton[target_token] = eng_token
                        english_element_mappings[target_token] = [eng_token]
                        break
    
    # Add numeric variations for mapped numeric tokens
    for target_token, skeleton_code in target_element_to_skeleton.items():
        if target_token.isnumeric():
            # Add variations based on the skeleton code and token length
            if skeleton_code.startswith('d'):
                if len(target_token) == 1:
                    english_element_mappings[target_token].append('d')
                elif len(target_token) == 2:
                    if target_token.startswith('0'):
                        english_element_mappings[target_token].append('dd')
                    else:
                        english_element_mappings[target_token].append('d')
                        english_element_mappings[target_token].append('dd')
            elif skeleton_code.startswith('M'):
                if len(target_token) == 1:
                    english_element_mappings[target_token].append('M')
                elif len(target_token) == 2:
                    if target_token.startswith('0'):
                        english_element_mappings[target_token].append('MM')
                    else:
                        english_element_mappings[target_token].append('M')
                        english_element_mappings[target_token].append('MM')
            elif skeleton_code.startswith('y'):
                if len(target_token) == 4:
                    english_element_mappings[target_token].append('y')
                elif len(target_token) == 2:
                    english_element_mappings[target_token].append('yy')
    
    # First, handle any remaining day-of-week tokens that weren't mapped
    for target_token in target_tokens:
        if (target_token in target_date_dict.get('day_abb_for', []) or 
            target_token in target_date_dict.get('day_nar_for', []) or 
            target_token in target_date_dict.get('day_wid_for', []) or 
            target_token in target_date_dict.get('day_sho_for', [])):
            if target_token not in target_element_to_skeleton:
                # Map to E if not already mapped
                target_element_to_skeleton[target_token] = 'E'
                english_element_mappings[target_token] = ['E']
    
    # Then handle any remaining numeric tokens that weren't mapped
    for target_token in target_tokens:
        if target_token.isnumeric() and target_token not in target_element_to_skeleton:
            # Fallback for numeric tokens that weren't mapped
            # Try to map based on value, position, and context
            value = int(target_token)
            
            # Find the position of this token in the target tokens
            token_index = target_tokens.index(target_token)
            
            # Look at the surrounding context to determine if it's a month or day
            is_likely_month = False
            is_likely_day = False
            
            # Check if this token is followed by a slash and another numeric token
            if token_index + 2 < len(target_tokens) and target_tokens[token_index + 1] == '/' and target_tokens[token_index + 2].isnumeric():
                next_value = int(target_tokens[token_index + 2])
                # If this value <= 12 and next value > 12, this is likely a month
                if value <= 12 and next_value > 12:
                    is_likely_month = True
                # If this value > 12 and next value <= 12, this is likely a day
                elif value > 12 and next_value <= 12:
                    is_likely_day = True
                # If both values <= 12, look at the pattern
                elif value <= 12 and next_value <= 12:
                    # Check if this is part of a date pattern like "4/4" or "13/4"
                    # If the first value is smaller and the second is also small, it's likely day/month
                    # If the first value is larger and the second is small, it's likely day/month (reordered)
                    if value > next_value:
                        is_likely_day = True
                    else:
                        is_likely_month = True
            
            if value <= 12 and is_likely_month:
                # Likely a month
                target_element_to_skeleton[target_token] = 'M'
                english_element_mappings[target_token] = ['M']
            elif value <= 31 and is_likely_day:
                # Likely a day
                target_element_to_skeleton[target_token] = 'd'
                english_element_mappings[target_token] = ['d']
            elif value <= 12:
                # Could be month or day, default to month
                target_element_to_skeleton[target_token] = 'M'
                english_element_mappings[target_token] = ['M']
            elif value <= 31:
                # Could be day
                target_element_to_skeleton[target_token] = 'd'
                english_element_mappings[target_token] = ['d']
            else:
                # Could be year
                target_element_to_skeleton[target_token] = 'y'
                english_element_mappings[target_token] = ['y']
    
    # Generate all possible skeleton combinations
    target_skeleton_strings = []
    
    # Build skeleton by mapping each target token to its skeleton
    skeleton_parts = []
    for target_token in target_tokens:
        # Remove ATTACHED prefix if present
        if target_token.startswith('ATTACHED:'):
            actual_token = target_token[9:]  # Remove "ATTACHED:" prefix
        else:
            actual_token = target_token
            
        if target_token in target_element_to_skeleton:
            skeleton_parts.append(target_element_to_skeleton[target_token])
        else:
            # If no mapping found, use the token as-is (for literals)
            skeleton_parts.append(f"'{actual_token}'")
    
    # Reconstruct the skeleton with original spacing
    # Use the original target expression to determine spacing
    if original_target_expression:
        # Reconstruct spacing based on original expression
        skeleton = ''
        current_pos = 0
        for i, target_token in enumerate(target_tokens):
            # Remove ATTACHED prefix if present
            if target_token.startswith('ATTACHED:'):
                actual_token = target_token[9:]
            else:
                actual_token = target_token
                
            # Find the position of this token in the original expression
            token_start = original_target_expression.find(actual_token, current_pos)
            
            # Add any spaces that were before this token
            if token_start > current_pos:
                skeleton += ' ' * (token_start - current_pos)
            
            # Add the skeleton part
            if target_token in target_element_to_skeleton:
                skeleton += target_element_to_skeleton[target_token]
            else:
                skeleton += f"'{actual_token}'"
            
            current_pos = token_start + len(actual_token)
    else:
        # Fallback: join with spaces
        skeleton = ' '.join(skeleton_parts)
    
    # Generate variations for numeric components (limit to prevent explosion)
    numeric_variations = []
    
    for target_token in target_tokens:
        if target_token.isnumeric() and target_token in english_element_mappings:
            variations = english_element_mappings[target_token]
            if len(variations) > 1:
                # Limit variations to prevent explosion - take only the first 2 variations
                limited_variations = variations[:2]
                numeric_variations.append((target_token, limited_variations))
    
    # Generate all combinations of numeric variations
    if numeric_variations:
        from itertools import product
        variation_combinations = list(product(*[variations for _, variations in numeric_variations]))
        
        # Limit the number of combinations to prevent explosion
        max_combinations = 10
        if len(variation_combinations) > max_combinations:
            variation_combinations = variation_combinations[:max_combinations]
        
        for combination in variation_combinations:
            # Create a copy of the skeleton and replace numeric components
            # We need to be more careful about replacement to avoid replacing parts of literal tokens
            skeleton_copy = skeleton
            for i, (target_token, _) in enumerate(numeric_variations):
                if i < len(combination):
                    # Only replace the specific skeleton code for this token, not all occurrences
                    # Find the original skeleton code for this token
                    original_code = target_element_to_skeleton[target_token]
                    new_code = combination[i]
                    
                    # Replace only complete skeleton codes, not parts of literal strings
                    # Use word boundaries to ensure we don't replace parts of quoted literals
                    import re
                    # Only replace if it's not inside single quotes (literal text)
                    pattern = r"(?<!')(" + re.escape(original_code) + r")(?!')"
                    skeleton_copy = re.sub(pattern, new_code, skeleton_copy, count=1)
            target_skeleton_strings.append(skeleton_copy)
    else:
        target_skeleton_strings.append(skeleton)
    
    # Filter out invalid skeletons (duplicate element types)
    final_skeletons = []
    for skeleton_str in target_skeleton_strings:
        # Check for duplicate element types within each side of a range
        if '-' in skeleton_str or '–' in skeleton_str:
            # Handle range expressions
            # Split on the range separator, not on every dash
            import re
            if '-' in skeleton_str:
                parts = re.split(r' - ', skeleton_str)
            else:
                parts = re.split(r' – ', skeleton_str)
            if len(parts) == 2:
                left_side, right_side = parts[0], parts[1]
                # For range expressions, allow some duplication between sides
                # Each side should be valid on its own, but we allow the same element types on both sides
                left_valid = not has_duplicate_elements(left_side)
                right_valid = not has_duplicate_elements(right_side)
                if left_valid and right_valid:
                    final_skeletons.append(skeleton_str)
        else:
            # Handle single expressions
            is_valid = not has_duplicate_elements(skeleton_str)
            if is_valid:
                final_skeletons.append(skeleton_str)
    
    if not final_skeletons:
        raise ValueError(f"Invalid skeleton generated: all options contain duplicate element types")
    
    # Remove duplicates and sort
    unique_skeletons = sorted(list(set(final_skeletons)))
    return unique_skeletons


def has_duplicate_elements(skeleton_str):
    """Check if a skeleton string has duplicate element types."""
    element_types = []
    # Split on common separators and extract skeleton codes
    import re
    parts = re.split(r'[,\.\-–—\s]+', skeleton_str)
    for part in parts:
        part = part.strip()
        if part:
            # Extract skeleton codes (M, MM, MMM, MMMM, d, dd, y, yy, E, EEE, etc.)
            codes = re.findall(r'[M]{1,4}|[d]{1,2}|[y]{1,2}|[E]{1,6}|[L]{1,5}|[c]{1,6}', part)
            for code in codes:
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
    
    # Allow some duplicates in certain contexts
    # For example, 'd/d/y' is valid (day/month/year)
    # But 'd/d/d' is invalid (three days)
    element_counts = {}
    for elem in element_types:
        element_counts[elem] = element_counts.get(elem, 0) + 1
    
    # Check for invalid duplicates
    for elem, count in element_counts.items():
        if elem == 'd' and count > 2:  # Allow up to 2 days (e.g., d/d/y)
            return True
        elif elem == 'M' and count > 2:  # Allow up to 2 months (e.g., M/M/y)
            return True
        elif elem == 'y' and count > 2:  # Allow up to 2 years (e.g., y/y/M)
            return True
        elif elem == 'E' and count > 2:  # Allow up to 2 day-of-week (e.g., E, E)
            return True
    
    return False


# Ensure the mapping logic correctly handles date ranges
def handle_date_ranges(tokens):
    # Logic to map date ranges like 'M/d - M/d' to 'd/M - d/M'
    mapped_skeleton = []
    for i, token in enumerate(tokens):
        if token.isdigit():
            # Determine if it's a month or day based on position and value
            if i % 2 == 0:  # Even positions are months
                mapped_skeleton.append('M')
            else:  # Odd positions are days
                mapped_skeleton.append('d')
        elif token.isalpha():
            mapped_skeleton.append('M')
        else:
            mapped_skeleton.append(token)
    return mapped_skeleton


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
