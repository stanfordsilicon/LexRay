# Testing Data Structure

This folder contains input and output data for testing the CLDR Date Skeleton Converter with support for multiple trials and iterations.

## Folder Structure

```
testing/
├── README.md                    # This file
├── trial_20250807_140351/      # Trial with timestamp (YYYYMMDD_HHMMSS)
│   ├── input/                  # Input CSV files for this trial
│   ├── output/                 # Generated results and analysis files
│   ├── results/                # Additional analysis and reports
│   └── meta_data/              # Trial metadata and configuration
├── trial_20250807_143022/      # Another trial with different timestamp
│   ├── input/                  # Input CSV files for this trial
│   ├── output/                 # Generated results and analysis files
│   ├── results/                # Additional analysis and reports
│   └── meta_data/              # Trial metadata and configuration
└── ...                         # Additional trials as needed
```

## Trial Organization

Each trial folder allows you to:
- **Test different datasets** for the same languages
- **Compare results** across iterations
- **Track improvements** in your data processing
- **Maintain separate experiments** without conflicts
- **Timestamp tracking** for chronological organization

### Trial Folder Structure

Each trial folder contains:
- **`input/`**: Place your CSV files here
- **`output/`**: Automatically generated results from batch processing
- **`results/`**: Additional analysis, reports, and custom outputs
- **`meta_data/`**: Trial metadata, configuration, and tracking information

## Input Files

Place your CSV files in the `trial_YYYYMMDD_HHMMSS/input/` folder with the naming convention:
- `{language}_data.csv`

Examples:
- `spanish_data.csv`
- `french_data.csv`
- `german_data.csv`
- `japanese_data.csv`

## CSV Format

Your input CSV files should have these columns:
- `ENGLISH`: English date expressions
- `TARGET`: Target language date expressions  
- `XPATH`: CLDR XPath references (will be preserved unchanged)

Example:
```csv
ENGLISH,TARGET,XPATH
"January 16, 2006","16 de enero de 2006","//ldml/dates/calendars/calendar[@type='gregorian']/dateFormats/dateFormatLength[@type='long']/dateFormat[@type='standard']/pattern[@type='standard']"
"August 10, 2025","10 de agosto 2025","//ldml/dates/calendars/calendar[@type='gregorian']/dateFormats/dateFormatLength[@type='long']/dateFormat[@type='standard']/pattern[@type='standard']"
```

## Output Files

When you run batch processing, the following files will be generated in `trial_YYYYMMDD_HHMMSS/output/`:

1. **Results CSV**: `{language}_data_results.csv`
   - Contains: `ENGLISH_SKELETON`, `TARGET_SKELETON`, `XPATH`

2. **Analysis Report**: `{language}_data_results_analysis.json`
   - Contains: Frequency analysis, format length distribution, statistics

## Results Folder

The `results/` folder is for additional analysis and custom outputs:
- **Custom reports** and analysis
- **Comparative studies** between different runs
- **Validation results** and quality metrics
- **Research notes** and findings
- **Visualizations** and charts

## Meta Data Folder

The `meta_data/` folder contains trial metadata and configuration:
- **Trial information** (ID, creation date, description)
- **Processing parameters** (CLDR data path, target language)
- **Configuration files** (settings, parameters used)
- **Processing statistics** (success rates, row counts)
- **Research notes** and experiment documentation
- **Version information** (software versions, data versions)
- **Companion CSV files** with verified skeletons for validation

### Companion CSV Files for Validation

For each input CSV file, create a corresponding verified CSV file in `meta_data/` with the naming convention:
- `{language}_data_verified.csv`

**Format:**
- `ENGLISH_SKELETON_VERIFIED`: Verified English skeletons (ground truth)
- `TARGET_SKELETON_VERIFIED`: Verified target language skeletons (ground truth)
- `XPATH`: CLDR XPath references (must match input file)

**Multiple Options:**
Use semicolons (`;`) to separate multiple valid skeleton options:
```csv
ENGLISH_SKELETON_VERIFIED,TARGET_SKELETON_VERIFIED,XPATH
"MMMM d, y","d 'de' MMMM 'de' y; dd 'de' MMMM 'de' y","//ldml/dates/calendars/calendar[@type='gregorian']/dateFormats/dateFormatLength[@type='long']/dateFormat[@type='standard']/pattern[@type='standard']"
```

Example `meta_data/trial_info.json`:
```json
{
  "trial_id": "trial_20250807_140351",
  "created_at": "2025-08-07T14:03:51",
  "description": "Initial Spanish date pattern analysis",
  "language": "spanish",
  "input_files": ["spanish_data.csv"],
  "parameters": {
    "cldr_data_path": "/path/to/cldr_data",
    "target_language": "spanish"
  },
  "processing_stats": {
    "total_rows": 4,
    "successful_rows": 4,
    "failed_rows": 0,
    "success_rate": 1.0
  },
  "notes": "Testing basic Spanish date expressions"
}
```

## Usage

```bash
# Process data in a specific trial
python -m src.cli.batch_cli process testing/trial_20250807_140351/input/spanish_data.csv --stats

# Process data in another trial
python -m src.cli.batch_cli process testing/trial_20250807_143022/input/french_data.csv --stats

# Compare results between trials
python -m src.cli.batch_cli analyze testing/trial_20250807_140351/output/spanish_data_results.csv
python -m src.cli.batch_cli analyze testing/trial_20250807_143022/output/french_data_results.csv

# Validate results against verified skeletons
python -m src.cli.batch_cli validate testing/trial_20250807_140351/output/spanish_data_results.csv testing/trial_20250807_140351/meta_data/spanish_data_verified.csv
```

## Trial Management

### Creating a New Trial
```bash
# Create a new trial folder with timestamp
mkdir -p "testing/trial_$(date +%Y%m%d_%H%M%S)/input" \
         "testing/trial_$(date +%Y%m%d_%H%M%S)/output" \
         "testing/trial_$(date +%Y%m%d_%H%M%S)/results" \
         "testing/trial_$(date +%Y%m%d_%H%M%S)/meta_data"

# Copy data from previous trial (optional)
cp testing/trial_20250807_140351/input/spanish_data.csv testing/trial_20250807_143022/input/
```

### Trial Naming Convention
- **Timestamp format**: `trial_YYYYMMDD_HHMMSS`
- **Example**: `trial_20250807_140351` (August 7, 2025 at 14:03:51)
- **Benefits**: 
  - Chronological organization
  - No naming conflicts
  - Easy to track when experiments were run
  - Sortable by date/time

### Comparing Trials
You can compare results across trials by:
1. Running the same language data through different trials
2. Analyzing the output files from each trial
3. Comparing the statistics and skeleton patterns
4. Using the `results/` folder for custom comparative analysis

## Example Workflow

1. **Create Trial 1**: Test with basic Spanish data
   ```bash
   mkdir -p "testing/trial_$(date +%Y%m%d_%H%M%S)/input" \
            "testing/trial_$(date +%Y%m%d_%H%M%S)/output" \
            "testing/trial_$(date +%Y%m%d_%H%M%S)/results" \
            "testing/trial_$(date +%Y%m%d_%H%M%S)/meta_data"
   # Add spanish_data.csv to input folder
   python -m src.cli.batch_cli process testing/trial_20250807_140351/input/spanish_data.csv --stats
   ```

2. **Create Trial 2**: Test with expanded Spanish data
   ```bash
   mkdir -p "testing/trial_$(date +%Y%m%d_%H%M%S)/input" \
            "testing/trial_$(date +%Y%m%d_%H%M%S)/output" \
            "testing/trial_$(date +%Y%m%d_%H%M%S)/results" \
            "testing/trial_$(date +%Y%m%d_%H%M%S)/meta_data"
   # Add expanded spanish_data.csv to input folder
   python -m src.cli.batch_cli process testing/trial_20250807_143022/input/spanish_data.csv --stats
   ```

3. **Compare Results**: Analyze both trials
   ```bash
   python -m src.cli.batch_cli analyze testing/trial_20250807_140351/output/spanish_data_results.csv
   python -m src.cli.batch_cli analyze testing/trial_20250807_143022/output/spanish_data_results.csv
   ```

4. **Custom Analysis**: Use results folder for additional analysis
   ```bash
   # Create custom reports in results folder
   cp testing/trial_20250807_140351/output/spanish_data_results_analysis.json testing/trial_20250807_140351/results/
   cp testing/trial_20250807_143022/output/spanish_data_results_analysis.json testing/trial_20250807_143022/results/
   ```

5. **Document Trial**: Add metadata for tracking
   ```bash
   # Create trial_info.json in meta_data folder
   echo '{
     "trial_id": "trial_20250807_140351",
     "created_at": "2025-08-07T14:03:51",
     "description": "Initial Spanish date pattern analysis",
     "language": "spanish",
     "notes": "Testing basic Spanish date expressions"
   }' > testing/trial_20250807_140351/meta_data/trial_info.json
   ```

6. **Validate Results**: Compare against verified skeletons
   ```bash
   # Validate generated results against ground truth
   python -m src.cli.batch_cli validate testing/trial_20250807_140351/output/spanish_data_results.csv testing/trial_20250807_140351/meta_data/spanish_data_verified.csv
   ```

## Supported Languages

The system supports all languages available in your CLDR data files. Common languages include:
- Spanish, French, German, Italian, Portuguese
- Chinese, Japanese, Korean, Arabic, Hebrew
- Russian, Polish, Dutch, Swedish, Norwegian
- And many more...

The language name in the filename should match the language name used in your CLDR data files. 