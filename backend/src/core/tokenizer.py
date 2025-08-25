# -*- coding: utf-8 -*-
"""
Tokenization utilities for date expressions

Handles both regex-based tokenization and semantic tokenization
that recognizes multi-word date units from CLDR data.
"""

import regex
from .constants import TOKEN_PATTERN, PUNCTUATION


def normalize_dashes(expression):
    """
    Normalize various dash/hyphen characters to standard forms.
    
    Args:
        expression (str): Input expression
        
    Returns:
        str: Expression with normalized dashes
    """
    # Normalize various dash types to standard forms
    normalized = expression
    # Convert em dash to en dash for consistency
    normalized = normalized.replace('—', '–')
    # Convert thin space + en dash to just en dash
    normalized = normalized.replace(' – ', '–')
    # Convert multiple spaces around dashes to single space
    normalized = regex.sub(r'\s*–\s*', '–', normalized)
    return normalized


def tokenize_date_expression(expression):
    """
    Tokenize date expression using regex pattern.
    
    Args:
        expression (str): Date expression to tokenize
        
    Returns:
        list: List of tokens
    """
    # Normalize dashes before tokenization
    normalized_expression = normalize_dashes(expression)
    return regex.findall(TOKEN_PATTERN, normalized_expression)


def semantic_tokenize(expression, date_dict, lexicon):
    """
    Tokenize expression by recognizing complete date units from CLDR data.
    This handles multi-word date elements better than simple regex, and preserves
    literal text as complete words/phrases rather than breaking them into characters.
    Also handles compound tokens that contain date elements, numbers, and literal text.
    
    Args:
        expression (str): Date expression to tokenize
        date_dict (dict): Target language date dictionary
        lexicon (list): Target language lexicon
        
    Returns:
        list: List of semantically meaningful tokens with attachment info
    """
    # Normalize dashes before processing
    expression = normalize_dashes(expression)
    
    # First, collect all possible date elements (including multi-word ones)
    all_date_elements = []
    for category_list in date_dict.values():
        all_date_elements.extend(category_list)

    # Sort by length (descending) for longest-match tokenization
    all_date_elements.sort(key=len, reverse=True)

    # Remove duplicates while preserving order
    unique_date_elements = []
    for element in all_date_elements:
        if element not in unique_date_elements:
            unique_date_elements.append(element)

    # Define patterns
    punctuation_pattern = r'[/,\.\-–—،፣]'  # Added Arabic comma ، and Amharic comma ፣
    number_pattern = r'\d+'
    word_pattern = r'[a-zA-Z]+'  # Match word characters (letters only)

    tokens = []
    i = 0

    while i < len(expression):
        # Skip whitespace
        while i < len(expression) and expression[i].isspace():
            i += 1

        if i >= len(expression):
            break

        # Check for punctuation (including Arabic and Amharic commas)
        if regex.match(punctuation_pattern, expression[i]):
            tokens.append(expression[i])
            i += 1
            continue

        # Check for words that contain numbers (like "Fi4", "2nd", etc.)
        # These should be treated as complete words and looked up in the lexicon
        word_with_number_match = regex.match(r'[a-zA-Z]+\d+[a-zA-Z]*|\d+[a-zA-Z]+', expression[i:])
        if word_with_number_match:
            word_with_number = word_with_number_match.group()
            
            # Check if this word exists in the lexicon or date elements
            is_known_word = (word_with_number.lower() in [elem.lower() for elem in unique_date_elements] or
                           word_with_number.lower() in [word.lower() for word in lexicon])
            
            if is_known_word:
                # This is a known word that happens to contain numbers - treat as single token
                tokens.append(word_with_number)
                i += len(word_with_number)
                continue
            else:
                # Not a known word, might be a compound that needs breaking down
                # Check if there's text immediately following the number (compound token)
                number_match = regex.match(number_pattern, expression[i:])
                if number_match:
                    number = number_match.group()
                    number_end = i + len(number)
                    
                    if (number_end < len(expression) and 
                        expression[number_end].isalpha() and 
                        not expression[number_end].isspace()):
                        
                        # This might be a compound token like "16de" - find the full word
                        word_match = regex.match(r'\d+[^\s/,\.\-–—،፣]+', expression[i:])
                        if word_match:
                            compound_word = word_match.group()
                            
                            # Break down the compound word
                            compound_parts = break_down_compound_word(compound_word, unique_date_elements)
                            
                            if len(compound_parts) > 1:
                                # This is a compound token - add each part with attachment info
                                for j, (part_type, part_text) in enumerate(compound_parts):
                                    if j == 0:
                                        # First part is not attached to anything before
                                        tokens.append(part_text)
                                    else:
                                        # Subsequent parts are attached to previous parts
                                        tokens.append(f"ATTACHED:{part_text}")
                            else:
                                # Not a compound, just add the number
                                tokens.append(number)
                            
                            i += len(compound_word)
                            continue
        
        # Check for pure numbers
        number_match = regex.match(number_pattern, expression[i:])
        if number_match:
            number = number_match.group()
            number_end = i + len(number)
            
            # Check if there's text immediately following the number (compound token)
            if (number_end < len(expression) and 
                expression[number_end].isalpha() and 
                not expression[number_end].isspace()):
                
                # This might be a compound token like "16de" - find the full word
                word_match = regex.match(r'\d+[^\s/,\.\-–—،፣]+', expression[i:])
                if word_match:
                    compound_word = word_match.group()
                    
                    # Break down the compound word
                    compound_parts = break_down_compound_word(compound_word, unique_date_elements)
                    
                    if len(compound_parts) > 1:
                        # This is a compound token - add each part with attachment info
                        for j, (part_type, part_text) in enumerate(compound_parts):
                            if j == 0:
                                # First part is not attached to anything before
                                tokens.append(part_text)
                            else:
                                # Subsequent parts are attached to previous parts
                                tokens.append(f"ATTACHED:{part_text}")
                    else:
                        # Not a compound, just add the number
                        tokens.append(number)
                    
                    i += len(compound_word)
                    continue
            
            # Regular standalone number
            tokens.append(number)
            i += len(number)
            continue

        # Check for multi-word date elements first (longest match)
        found_multi_word = False
        for date_element in unique_date_elements:
            if ' ' in date_element:  # Multi-word elements
                if expression[i:].lower().startswith(date_element.lower()):
                    # Verify word boundaries
                    start_pos = i
                    end_pos = i + len(date_element)
                    
                    # Check start boundary
                    if start_pos > 0 and expression[start_pos-1].isalpha():
                        continue
                    
                    # Check end boundary
                    if end_pos < len(expression) and expression[end_pos].isalpha():
                        continue
                    
                    # Found valid multi-word date element
                    tokens.append(expression[start_pos:end_pos])
                    i = end_pos
                    found_multi_word = True
                    break
        
        if found_multi_word:
            continue

        # Check for complete multi-word expressions that might contain Unicode characters
        # Look ahead to find complete words/phrases that match the lexicon
        remaining_text = expression[i:].strip()
        if remaining_text:
            # Try to match the longest possible phrase from the lexicon
            longest_match = None
            longest_length = 0
            
            for lexicon_word in lexicon:
                if len(lexicon_word) > longest_length and remaining_text.lower().startswith(lexicon_word.lower()):
                    # Check if it's a complete word/phrase (ends at word boundary)
                    match_end = i + len(lexicon_word)
                    if (match_end >= len(expression) or 
                        expression[match_end].isspace() or 
                        expression[match_end] in PUNCTUATION):
                        longest_match = lexicon_word
                        longest_length = len(lexicon_word)
            
            if longest_match:
                tokens.append(expression[i:i+longest_length])
                i += longest_length
                continue
        
        if found_multi_word:
            continue

        # Check for single words (including abbreviated forms with periods)
        word_match = regex.match(r'[a-zA-Z]+\.?', expression[i:])  # Allow periods after words
        if word_match:
            word = word_match.group()
            
            # Check if this word (with or without period) is a date element
            is_date_element = False
            for date_element in unique_date_elements:
                if word.lower() == date_element.lower():
                    # Found valid date element match
                    tokens.append(word)
                    i += len(word)
                    is_date_element = True
                    break
            
            if not is_date_element:
                # Not a date element - try to break down compound words
                compound_parts = break_down_compound_word(word, unique_date_elements)
                
                if len(compound_parts) > 1:
                    # This is a compound token - add each part with attachment info
                    for j, (part_type, part_text) in enumerate(compound_parts):
                        if j == 0:
                            # First part is not attached to anything before
                            tokens.append(part_text)
                        else:
                            # Subsequent parts are attached to previous parts
                            tokens.append(f"ATTACHED:{part_text}")
                else:
                    # Single word - add it as a literal token
                    tokens.append(word)
                
                i += len(word)
            continue

        # Check for date elements (longest match first) - for cases where date elements
        # might be embedded in compound words or have special formatting
        found_match = False
        for date_element in unique_date_elements:
            if expression[i:].lower().startswith(date_element.lower()):
                # Verify word boundaries (don't match partial words at start/end)
                start_pos = i
                end_pos = i + len(date_element)

                # Check start boundary
                if start_pos > 0 and expression[start_pos-1].isalpha():
                    continue

                # Note: We intentionally allow a following letter so that
                # shorter forms can match inside longer words when no longer
                # form exists in the input (e.g., 'oct' in 'octre').

                # Found valid date element match
                tokens.append(expression[start_pos:end_pos])
                i = end_pos
                found_match = True
                break

        if not found_match:
            # Check for any remaining non-whitespace characters as literal
            remaining_chars = expression[i:].strip()
            if remaining_chars:
                # Take the first non-whitespace character as literal
                tokens.append(expression[i])
                i += 1
            else:
                # Skip any remaining whitespace
                i += 1

    return tokens


def break_down_compound_word(word, date_elements):
    """
    Break down a compound word into date elements, numbers, and literal text.
    Uses longest-match first approach to find date elements within the word.
    
    Args:
        word (str): The compound word to break down
        date_elements (list): List of known date elements (already sorted by length desc)
        
    Returns:
        list: List of tuples (type, text) where type is 'date', 'number', or 'literal'
    """
    parts = []
    i = 0
    
    while i < len(word):
        found_match = False
        
        # Check for numbers first
        number_match = regex.match(r'\d+', word[i:])
        if number_match:
            parts.append(('number', number_match.group()))
            i += len(number_match.group())
            found_match = True
            continue
        
        # Check for date elements (longest match first - date_elements already sorted)
        for date_element in date_elements:
            # Skip single-character matches when we're in the middle of a word
            # (single chars should only match as standalone tokens)
            if len(date_element) == 1 and len(word) > 1:
                continue
                
            # Check if this date element matches at current position
            if (i + len(date_element) <= len(word) and 
                word[i:i+len(date_element)].lower() == date_element.lower()):
                # Accept matches even if a letter follows. Longest-match-first
                # ensures the widest form wins; if not present, shorter forms
                # like 'oct' can still match in 'octre'.
                parts.append(('date', word[i:i+len(date_element)]))
                i += len(date_element)
                found_match = True
                break
        
        if not found_match:
            # Collect literal characters one by one until we find a date element or number
            literal_start = i
            
            # Look ahead to find the next date element or number
            next_match_pos = len(word)  # Default to end of word
            
            # Check for numbers ahead
            for j in range(i + 1, len(word) + 1):
                number_match = regex.match(r'\d+', word[j:])
                if number_match:
                    next_match_pos = j
                    break
            
            # Check for date elements ahead (multi-character only in compound words)
            for j in range(i + 1, len(word) + 1):
                for date_element in date_elements:
                    # Skip single-character date elements in compound words
                    if len(date_element) == 1:
                        continue
                        
                    if (j + len(date_element) <= len(word) and 
                        word[j:j+len(date_element)].lower() == date_element.lower()):
                        next_match_pos = min(next_match_pos, j)
                        break
                if next_match_pos < len(word):
                    break
            
            # Extract literal text up to the next match
            if next_match_pos > i:
                literal_text = word[i:next_match_pos]
                parts.append(('literal', literal_text))
                i = next_match_pos
            else:
                # No more matches, take the rest as literal
                literal_text = word[i:]
                parts.append(('literal', literal_text))
                i = len(word)
    return parts if len(parts) > 1 else [('literal', word)]