#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLDR Date Skeleton Converter - Main Entry Point

Run this script to start the interactive CLDR date skeleton converter.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli.main import main

if __name__ == "__main__":
    main() 