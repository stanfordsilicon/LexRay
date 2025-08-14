# CLDR Data Files

This folder contains the Excel files with CLDR (Common Locale Data Repository) data used by the Date Skeleton Converter.

## Required Files

### English Reference Data
- **`english_moderate.xlsx`** - English reference data with CLDR skeleton patterns

### Target Language Data
- **`{language}_moderate.xlsx`** - Target language data files
  - Examples: `spanish_moderate.xlsx`, `french_moderate.xlsx`, `german_moderate.xlsx`

## File Format

Each Excel file should contain the following columns:

### Required Columns
- **`English`** - English skeleton patterns (for english_moderate.xlsx only)
- **`Header`** - Date element descriptions (e.g., "Months - wide - Formatting")
- **`Winning`** - Sample translations/date elements
- **`Code`** - CLDR codes
- **`XPath`** - CLDR specification paths

### Example Structure
```
Header                          | Winning    | Code | XPath
-------------------------------|------------|------|-------
Months - wide - Formatting     | January    | jan  | //ldml/dates/...
Months - wide - Formatting     | February   | feb  | //ldml/dates/...
Months - abbreviated - Format  | Jan        | jan  | //ldml/dates/...
Days - wide - Formatting       | Sunday     | sun  | //ldml/dates/...
```

## Data Sources

CLDR data can be obtained from:
- **Unicode CLDR Project**: https://cldr.unicode.org/
- **CLDR JSON Data**: https://github.com/unicode-org/cldr-json
- **ICU Data**: https://icu.unicode.org/

## Adding New Languages

To add support for a new language:

1. Create a new Excel file named `{language}_moderate.xlsx`
2. Include all required columns
3. Populate with appropriate CLDR data for that language
4. Ensure consistency with the data structure described above

## Notes

- File names should be lowercase (e.g., `spanish_moderate.xlsx`, not `Spanish_moderate.xlsx`)
- The system will automatically clean thin space characters (`\u2009`) from data
- Empty or missing values in non-critical columns are handled gracefully
- Date elements should be in their natural form for the target language 