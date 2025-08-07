# -*- coding: utf-8 -*-
"""
Basic tests for CLDR Date Skeleton Converter

Tests basic functionality and imports to ensure the package structure works correctly.
"""

import sys
import os
import unittest

# Add the src directory to the Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.constants import SKELETON_CODES, ENGLISH_DATE_DICT
from core.tokenizer import tokenize_date_expression


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality and imports."""
    
    def test_constants_import(self):
        """Test that constants can be imported correctly."""
        self.assertIsInstance(SKELETON_CODES, dict)
        self.assertIsInstance(ENGLISH_DATE_DICT, dict)
        self.assertIn('mon_wid_for', SKELETON_CODES)
        self.assertEqual(SKELETON_CODES['mon_wid_for'], 'MMMM')
    
    def test_tokenizer_import(self):
        """Test that tokenizer functions can be imported and used."""
        tokens = tokenize_date_expression("January 16, 2006")
        expected = ['January', '16', ',', '2006']
        self.assertEqual(tokens, expected)
    
    def test_english_date_dict(self):
        """Test English date dictionary structure."""
        self.assertIn('mon_wid_for', ENGLISH_DATE_DICT)
        self.assertIn('January', ENGLISH_DATE_DICT['mon_wid_for'])
        self.assertEqual(ENGLISH_DATE_DICT['mon_wid_for'][0], 'January')


if __name__ == '__main__':
    unittest.main() 