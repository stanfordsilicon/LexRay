from src.core.skeleton_analyzer import analyze_tokens_for_format_options, generate_valid_combinations, convert_to_skeleton_codes, format_skeleton_strings
from src.data.data_loader import load_target_language_data, populate_target_language_dict
from itertools import product

# Load data
df = load_target_language_data('cldr_data', 'english')
date_dict, lexicon = populate_target_language_dict(df)

tokens = ['2022', 'Apr', '22', '-', '27']
print('Tokens:', tokens)

format_options = analyze_tokens_for_format_options(tokens, date_dict)
print('Format options:', format_options)

# Debug the combination generation
print('\nDebugging combination generation:')

# Group tokens by dash/period-separated sections
new_formatting_options = []
current_group = []

for format_list in format_options:
    if format_list == ["-"] or format_list == ["."] or format_list == ["–"] or format_list == ["—"]:
        if current_group:
            new_formatting_options.append(current_group)
        new_formatting_options.append(format_list[0])  # Add the separator
        current_group = []
    else:
        current_group.append(format_list)

if current_group:
    new_formatting_options.append(current_group)

print('New formatting options:', new_formatting_options)

# Extract sections (ignore separators for combination generation)
sections = [item for item in new_formatting_options if item not in ["-", ".", "–", "—"]]
print('Sections:', sections)

# Generate valid combinations for each section
section_combinations = []
for i, section in enumerate(sections):
    print(f'\nSection {i}:', section)
    all_combinations = list(product(*section))
    print(f'All combinations for section {i}:', all_combinations)
    
    # Filter out combinations with duplicate date element types and invalid value assignments
    valid_combinations = []
    for combo in all_combinations:
        print(f'  Checking combo: {combo}')
        date_elements = [elem for elem in combo if isinstance(elem, str) and '_' in elem]
        print(f'    Date elements: {date_elements}')
        prefixes = [elem.split('_')[0] for elem in date_elements]
        print(f'    Prefixes: {prefixes}')
        
        # Check for duplicate prefixes
        if len(prefixes) != len(set(prefixes)):
            print(f'    REJECTED: Duplicate prefixes')
            continue
        
        # Check for logical validity of the combination
        is_valid = True
        if tokens:
            numeric_tokens = [t for t in tokens if t.isdigit()]
            print(f'    Numeric tokens: {numeric_tokens}')
            
            # Create a mapping between numeric tokens and their corresponding numeric date elements
            numeric_index = 0
            for element in date_elements:
                # Only validate elements that are likely to correspond to numeric tokens
                if (element.startswith('mday_') or 
                    (element.startswith('mon_') and element.endswith('_min_for')) or
                    (element.startswith('mon_') and element.endswith('_sma_for')) or
                    element.startswith('year')):
                    
                    if numeric_index < len(numeric_tokens):
                        token = numeric_tokens[numeric_index]
                        value = int(token)
                        print(f'      Element {element} -> token {token} (value {value})')
                        
                        # Don't validate year elements - they can be any reasonable year value
                        if element.startswith('year'):
                            numeric_index += 1
                            continue
                        
                        # Validate month elements
                        if element.startswith('mon_') and value > 12:
                            print(f'      REJECTED: Invalid month value {value}')
                            is_valid = False
                            break
                        
                        # Validate day elements
                        elif element.startswith('mday_') and value > 31:
                            print(f'      REJECTED: Invalid day value {value}')
                            is_valid = False
                            break
                        
                        numeric_index += 1
        
        if is_valid:
            print(f'    ACCEPTED: {combo}')
            valid_combinations.append(list(combo))
        else:
            print(f'    REJECTED: Invalid combination')
    
    print(f'Valid combinations for section {i}:', valid_combinations)
    section_combinations.append(valid_combinations)

print('\nSection combinations:', section_combinations)
