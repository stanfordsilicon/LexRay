# -*- coding: utf-8 -*-
"""
Validation utilities for date expressions and tokens

Contains validation logic for ensuring date expressions follow proper formatting rules,
validating numeric values against date constraints, and checking tokens against lexicons.
"""

from .constants import ENGLISH_LEXICON, PUNCTUATION


def validate_tokens(tokens, expression_name="expression"):
    """
    Validate that tokenization produced results and tokens follow formatting rules.
    
    Args:
        tokens (list): List of tokens to validate
        expression_name (str): Name of expression for error messages
        
    Raises:
        ValueError: If tokens are invalid
    """
    # Validate that tokenization produced results
    if not tokens:
        raise ValueError(f"Enter a string. Rerun {expression_name} and enter a different string")

    # Validate each token according to formatting rules
    for i, token in enumerate(tokens):
        if token.isnumeric():
            # Numbers must be 1-2 digits or exactly 4 digits
            if len(token) > 4 or len(token) == 3:
                raise ValueError(f"'{token}' is not a valid element. Please rerun {expression_name} before continuing.")

        elif token in PUNCTUATION:
            # Punctuation cannot be at start/end or consecutive
            if i == 0 or i == len(tokens) - 1:
                raise ValueError(f"'{' '.join(tokens)}' is not a valid expression. Please rerun {expression_name} before continuing.")
            if i > 0 and tokens[i-1] in PUNCTUATION:
                raise ValueError(f"'{' '.join(tokens)}' has consecutive punctuation. Please rerun {expression_name} before continuing.")


def validate_english_tokens(tokens, expression):
    """
    Validate English tokens against the English lexicon.
    
    Args:
        tokens (list): List of tokens to validate
        expression (str): Original expression for error messages
        
    Raises:
        ValueError: If token not in English lexicon
    """
    for token in tokens:
        if (not token.isnumeric() and 
            token not in PUNCTUATION and 
            token.lower() not in [item.lower() for item in ENGLISH_LEXICON]):
            raise ValueError(f"'{token}' is not in the English data set.")


def validate_target_language_tokens(tokens, lexicon, expression):
    """
    Validate target language tokens against the target language lexicon.
    
    Args:
        tokens (list): List of tokens to validate
        lexicon (list): Target language lexicon
        expression (str): Original expression for error messages
        
    Raises:
        ValueError: If token not in target language lexicon
    """
    for token in tokens:
        if (not token.isnumeric() and 
            token not in PUNCTUATION and 
            token not in lexicon):
            raise ValueError(f"'{token}' is not in the target language data set.")


def validate_date_values(tokens, skeleton_tokens):
    """
    Validate numeric date values against their format interpretation.
    Ensures months ≤12 and days ≤31.
    
    Args:
        tokens (list): Original input tokens
        skeleton_tokens (list): Corresponding skeleton tokens
        
    Raises:
        ValueError: If date values are out of bounds
    """
    for i in range(min(len(tokens), len(skeleton_tokens))):
        token = skeleton_tokens[i]
        input_value = tokens[i]

        # Check month bounds (1-12)
        if token in ["MM", "M"] and input_value.isdigit():
            if int(input_value) > 12:
                raise ValueError(f"'{input_value}' is out of bounds for month of the year. Please rerun and enter a different string.")

        # Check day bounds (1-31)
        elif token in ["dd", "d"] and input_value.isdigit():
            if int(input_value) > 31:
                raise ValueError(f"'{input_value}' is out of bounds for day of the month. Please rerun and enter a different string.")


def validate_non_empty_input(input_value, field_name):
    """
    Validate that input is not empty.
    
    Args:
        input_value (str): Input to validate
        field_name (str): Name of field for error message
        
    Raises:
        ValueError: If input is empty
    """
    if not input_value or not input_value.strip():
        raise ValueError(f"{field_name} cannot be empty. Please enter a valid {field_name.lower()}.") 