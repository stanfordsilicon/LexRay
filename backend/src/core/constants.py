# -*- coding: utf-8 -*-
"""
Constants for CLDR Date Skeleton Conversion

Contains all the mapping tables, skeleton codes, and reference data
used for converting between natural language date expressions and CLDR skeletons.
"""

# CLDR Skeleton code mappings
SKELETON_CODES = {
    "mon_nar_for": "MMMMM", "mon_wid_for": "MMMM", "mon_abb_for": "MMM", 
    "mon_sma_for": "MM", "mon_min_for": "M", 
    "mon_nar_sta": "LLLLL", "mon_wid_sta": "LLLL", "mon_abb_sta": "LLL", 
    "mon_sma_sta": "LL", "mon_min_sta": "L",
    "day_sho_for": "EEEEEE", "day_nar_for": "EEEEE", "day_wid_for": "EEEE", 
    "day_abb_for": "E", 
    "day_sho_sta": "cccccc", "day_nar_sta": "ccccc", "day_wid_sta": "cccc", 
    "day_abb_sta": "c",
    "mday_sma_for": "dd", "mday_min_for": "d", 
    "mday_sma_sta": "dd", "mday_min_sta": "d", 
    "year": "y", "year_abb_for": "yy", "year_abb_sta": "yy"
}

# Full name descriptions for skeleton codes
SKELETON_FULL_NAME = {
    "mon_nar_for": "Months - narrow - Formatting", 
    "mon_wid_for": "Months - wide - Formatting", 
    "mon_abb_for": "Months - abbreviated - Formatting", 
    "mon_sma_for": "MM", "mon_min_for": "M", 
    "mon_nar_sta": "Months - narrow - Standalone", 
    "mon_wid_sta": "Months - wide - Standalone", 
    "mon_abb_sta": "Months - abbreviated - Standalone", 
    "mon_sma_sta": "LL", "mon_min_sta": "L",
    "day_sho_for": "Days - short - Formatting", 
    "day_nar_for": "Days - narrow - Formatting", 
    "day_wid_for": "Days - wide - Formatting", 
    "day_abb_for": "Days - abbreviated - Formatting", 
    "day_sho_sta": "Days - short - Standalone", 
    "day_nar_sta": "Days - narrow - Standalone", 
    "day_wid_sta": "Days - wide - Standalone", 
    "day_abb_sta": "Days - abbreviated - Standalone",
    "mday_sma_for": "", "mday_min_for": "", 
    "mday_sma_sta": "", "mday_min_sta": "", 
    "year": "", "year_abb_for": "", "year_abb_sta": ""
}

# English date reference data
ENGLISH_DATE_DICT = {
    'mon_nar_for': ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'],
    'mon_wid_for': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'mon_abb_for': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    'mon_nar_sta': ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'],
    'mon_wid_sta': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'mon_abb_sta': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    'day_sho_for': ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
    'day_nar_for': ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
    'day_wid_for': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    'day_abb_for': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    'day_sho_sta': ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
    'day_nar_sta': ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
    'day_wid_sta': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    'day_abb_sta': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
}

# English lexicon for validation
ENGLISH_LEXICON = [
    'J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D',
    'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December',
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    'J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D',
    'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December',
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Su',
    'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'S', 'M', 'T', 'W', 'T', 'F', 'S',
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
    'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat',
    'Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa',
    'S', 'M', 'T', 'W', 'T', 'F', 'S',
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
    'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'
]

# Indexing for disambiguation
MONTH_INDEXING = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_INDEXING = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# Tokenization pattern
TOKEN_PATTERN = r'[\p{L}\p{M}]+\.?|\p{N}+|[/,\.\-–—،፣]'

# Punctuation characters - comprehensive list of all dash/hyphen variations
PUNCTUATION = [",", "/", "-", "—", "–", "–—", ".", "،", "፣"] 