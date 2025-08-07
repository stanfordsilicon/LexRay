# CLDR Date Skeleton Converter

A sophisticated bilingual date format analyzer that converts natural language date expressions to CLDR (Common Locale Data Repository) skeleton patterns by analyzing parallel examples in English and target languages.

## Overview

This tool takes human-readable date expressions in two languages and automatically generates standardized CLDR skeleton patterns. It's designed for internationalization (i18n) work, allowing developers to create proper date formatting patterns for different locales.

### Example Usage

**Input:**
- English: `"July 27, 2025"`
- Spanish: `"27 julio 2025"`

**Output:**
- English skeleton: `"MMMM d, y"`
- Spanish skeleton: `"d MMMM y"`
- CLDR metadata and XPath references

## Features

- **Bilingual Analysis**: Learns date formatting patterns from parallel translations
- **Smart Tokenization**: Recognizes multi-word date elements and handles complex expressions
- **Ambiguity Resolution**: Disambiguates tokens that could have multiple meanings (e.g., "J" = January/June/July)
- **Cultural Format Detection**: Automatically detects word reordering, punctuation differences, and literal text insertions
- **CLDR Validation**: Cross-references results with official CLDR reference data
- **Length Classification**: Preserves format length (wide/abbreviated/narrow) across languages
- **Fuzzy Numeric Matching**: Handles different numeric representations (1-digit vs 2-digit, etc.)

## Installation

### Option 1: Direct Usage
1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python cldr_converter.py
   ```

### Option 2: Package Installation
1. Install as a Python package:
   ```bash
   pip install -e .
   ```
2. Run using the console command:
   ```bash
   cldr-converter
   ```

## Quick Start

1. **Add CLDR data**: Place `english_moderate.xlsx` and any target language files (e.g., `spanish_moderate.xlsx`) in the `cldr_data/` folder

2. **Run the program**:
   ```bash
   python cldr_converter.py
   ```

3. **Follow the prompts**:
   - The system will automatically detect CLDR files in the `cldr_data/` folder
   - Enter your English date expression
   - Optionally provide translations in target languages

## Project Structure

```
├── cldr_converter.py          # Main entry point script
├── setup.py                   # Package installation script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .gitignore                 # Git ignore rules
│
├── src/                       # Source code package
│   ├── __init__.py           # Main package init
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   ├── constants.py      # CLDR codes and reference data
│   │   ├── tokenizer.py      # Date expression tokenization
│   │   ├── validators.py     # Input validation
│   │   ├── skeleton_analyzer.py      # Core analysis logic
│   │   ├── ambiguity_resolver.py     # Ambiguity handling
│   │   └── cross_language_mapper.py  # Cross-language mapping
│   ├── data/                 # Data loading and processing
│   │   ├── __init__.py
│   │   └── data_loader.py    # Excel file loading
│   └── cli/                  # Command-line interface
│       ├── __init__.py
│       └── main.py           # CLI logic and user interaction
│
├── cldr_data/                # CLDR Excel data files
│   ├── README.md            # Data format specifications
│   ├── .gitkeep             # Ensures folder is tracked
│   ├── english_moderate.xlsx # English reference data (add this file)
│   └── {lang}_moderate.xlsx  # Target language files (add as needed)
│
├── tests/                    # Test suite
│   ├── __init__.py
│   └── test_basic.py        # Basic functionality tests
│
└── docs/                     # Documentation
    └── README.md            # Documentation index
```

## Usage

Run the main program:
```bash
python cldr_converter.py
```

Follow the interactive prompts:

1. **CLDR data location**: System automatically uses `cldr_data/` folder (or specify custom path)
2. **Enter English expression**: e.g., `"January 16, 2006"`, `"8/17/2022"`, `"Mon, Dec 25"`
3. **Choose skeleton** (if multiple options found)
4. **Resolve ambiguities** (if needed, e.g., "J" could be January/June/July)
5. **Enter target language code**: e.g., `spanish`, `french`, `german`
6. **Enter translation**: Exact translation of the English expression

## CLDR Data Setup

### Required Files

Place these Excel files in the `cldr_data/` folder:

1. **`english_moderate.xlsx`** - English reference data (required)
2. **`{language}_moderate.xlsx`** - Target language files (e.g., `spanish_moderate.xlsx`)

### File Format

Each Excel file should contain these columns:
- `English` - English skeleton patterns (for english_moderate.xlsx only)
- `Header` - Date element descriptions (e.g., "Months - wide - Formatting")
- `Winning` - Sample translations/date elements
- `Code` - CLDR codes
- `XPath` - CLDR specification paths

See `cldr_data/README.md` for detailed specifications and examples.

### Data Sources

CLDR data can be obtained from:
- **Unicode CLDR Project**: https://cldr.unicode.org/
- **CLDR JSON Data**: https://github.com/unicode-org/cldr-json
- **ICU Data**: https://icu.unicode.org/

## Development

### Running Tests

```bash
python -m pytest tests/
```

Or run individual test files:
```bash
python tests/test_basic.py
```

### Package Development

Install in development mode:
```bash
pip install -e .[dev]
```

This installs the package with development dependencies for testing and linting.

## Key Algorithms

### Length Classification System
```python
# Different format lengths map to different CLDR codes:
"January" → mon_wid_for → "MMMM" (wide month)
"Jan"     → mon_abb_for → "MMM"  (abbreviated month)
"J"       → mon_nar_for → "MMMMM" (narrow month)
```

### Semantic Tokenization
Recognizes complete date units rather than just word boundaries:
```python
"15 de enero" → ["15", "de", "enero"]  # Not ["15", "de", "en", "ero"]
```

### Cross-Language Mapping
Maps semantic equivalents while detecting structural differences:
```python
English: "January 16" (Month-Day) → "MMMM d"
Spanish: "16 enero"   (Day-Month) → "d MMMM"
```

## CLDR Integration

The system generates official CLDR skeleton patterns that can be used with standard internationalization libraries:

- **ICU (International Components for Unicode)**
- **Moment.js/Day.js**
- **Java DateTimeFormatter**
- **Python babel/pytz**
- **.NET CultureInfo**

## Supported Features

- ✅ Month names (wide, abbreviated, narrow)
- ✅ Day names (wide, abbreviated, short, narrow)
- ✅ Numeric dates (1-2 digits, zero-padded)
- ✅ Years (2-digit, 4-digit)
- ✅ Punctuation and separators
- ✅ Literal text elements
- ✅ Multiple date formats per expression
- ✅ Standalone vs formatting contexts
- ✅ Ambiguity resolution
- ✅ Cross-language validation

## Requirements

- Python 3.7+
- pandas (Excel file processing)
- openpyxl (Excel engine)
- regex (Unicode-aware pattern matching)

## Troubleshooting

### Common Issues

1. **"English reference file not found"**
   - Ensure `english_moderate.xlsx` is in the `cldr_data/` folder
   - Check file name spelling and case sensitivity

2. **"Could not find the file for language X"**
   - Add `{language}_moderate.xlsx` to `cldr_data/` folder
   - Use lowercase language codes (e.g., `spanish`, not `Spanish`)

3. **"No official CLDR skeleton found"**
   - Check that your date expression uses valid date elements
   - Verify the CLDR reference data contains similar patterns

## Contributing

This tool was adapted from a Google Colab notebook for local Python use. Contributions are welcome for:

- Additional language support
- Enhanced tokenization algorithms
- Performance optimizations
- New validation rules
- Extended CLDR feature support

## License

This project is designed for internationalization research and development. Please ensure compliance with CLDR licensing terms when using with official Unicode data. 