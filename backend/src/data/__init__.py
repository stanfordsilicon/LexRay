# -*- coding: utf-8 -*-
"""
Data loading and processing modules

Handles loading CLDR data from Excel files and populating
target language dictionaries and lexicons.
"""

from .data_loader import (
    load_english_reference_data,
    load_target_language_data, 
    populate_target_language_dict
)

__all__ = [
    "load_english_reference_data",
    "load_target_language_data",
    "populate_target_language_dict"
] 