#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API bridge for LexRay backend to be called from the Next.js frontend.

Usage examples:
  python api_bridge.py single-english --english "January 16, 2006" --cldr_path /abs/path/backend/cldr_data
  python api_bridge.py single-cldr --english "January 16, 2006" --language spanish --translation "16 de enero de 2006" --cldr_path /abs/path/backend/cldr_data
  python api_bridge.py single-new --english "January 16, 2006" --language klingon --translation "16 foo 2006" --elements_csv /abs/tmp/elements.csv

  python api_bridge.py batch-english --csv /abs/tmp/english.csv --cldr_path /abs/path/backend/cldr_data
  python api_bridge.py batch-cldr --csv /abs/tmp/pairs.csv --language spanish --cldr_path /abs/path/backend/cldr_data
  python api_bridge.py batch-noncldr --pairs_csv /abs/tmp/pairs.csv --elements_csv /abs/tmp/elements.csv --language elvish
"""

import os
import sys
import json
import argparse
import csv
import io
from contextlib import contextmanager
import pandas as pd

# Make src importable
PROJECT_ROOT = os.path.dirname(__file__)
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from src.core.tokenizer import tokenize_date_expression, semantic_tokenize
from src.core.validators import (
    validate_tokens, validate_english_tokens, validate_date_values
)
from src.data.data_loader import load_english_reference_data, load_target_language_data, populate_target_language_dict
from src.core.skeleton_analyzer import (
    analyze_tokens_for_format_options, generate_valid_combinations,
    convert_to_skeleton_codes, format_skeleton_strings, expand_dash_variations
)
from src.core.ambiguity_resolver import detect_ambiguities, get_metadata_for_skeleton
from src.core.cross_language_mapper import map_english_to_target_skeleton
from src.core.constants import (
    ENGLISH_DATE_DICT,
    VALID_ENGLISH_SKELETONS,
    normalize_english_skeleton,
)

# Mapping from English skeletons to Xpstr values
SKELETON_TO_XPSTR = {
    "d": "76c392ebd666b0bd",
    "ccc": "140cf3a4c102803b",
    "d E": "7676ac749ef2cc62",
    "L": "959cbb42bb2962f",
    "M/d": "5abbc8f185730579",
    "E, M/d": "2d123e52098e97f2",
    "LLL": "e11a0c5e17bc068",
    "MMM d": "3124a5a401a45c9",
    "E, MMM d": "7f7bdb9593a8cc11",
    "MMMM d": "4f2a987be79e4e60",
    "y": "1a6ebe1471a0c10e",
    "M/y": "1b1e9f12a8fa3124",
    "M/d/y": "4af189b39e4e8ddf",
    "E, M/d/y": "695f62f84cfa7807",
    "MMM y": "6fea4427938536b8",
    "MMM d, y": "531768795c3cdb89",
    "E, MMM d, y": "7f63e28000f4612e",
    "MMMM y": "21dded0fd50ba37e",
    "d–d": "233a2f04cd0f85ce",
    "M–M": "5d6266e6fa97e95b",
    "M/d–M/d": "49a0d610084123b",
    "E, M/d–E, M/d": "18084ea0d3dfbabf",
    "MMM–MMM": "268fa3faf41b2154",
    "MMM d–d": "2ab400991072dbb2",
    "MMM d–MMM d": "1a013fd44bcfa040",
    "E, MMM d–E, MMM d": "61a41721d307be57",
    "y–y": "6433efb78f40e99a",
    "M/y–M/y": "3c6f0ce3063dc961",
    "M/d/y–M/d/y": "1937499d61343fb7",
    "E, M/d/y–E, M/d/y": "153a46c24508d0d4",
    "MMM–MMM y": "702784b915bcc899",
    "MMM y–MMM y": "6be28cb008f1aa65",
    "MMM d–d, y": "563c1e00ebce475e",
    "MMM d–MMM d, y": "22b38b49476d5bfd",
    "MMM d, y–MMM d, y": "44a032783d6ebae7",
    "E, MMM d–E, MMM d, y": "1d5027db323f2929",
    "E, MMM d, y–E, MMM d, y": "4557fe31de6087e0",
    "MMMM–MMMM y": "3fedd19e7c6533e3",
    "MMMM y–MMMM y": "7093f3bd95acbecc",
    "EEEE, MMMM d, y": "562f98c4c6b2e321",
    "MMMM d, y": "5d6ea98708b9b43b",
    "MMM d, y": "14164b88b71705de",
    "M/d/yy": "57dac0d1b36c1261",
    "MM-dd": "5caadf5d118016f5",
    "MM-dd, E": "de5cfd160ab31d6",
    "MMM d": "5b43c1398ea8b5a7",
    "MMM d, E": "7d2f93230e368caf",
    "MMMM d": "10090e2ed7afe7c2",
    "y-MM": "14a7fa5a8a306d0d",
    "y-MM-dd": "4bd4cef0273d5611",
    "y-MM-dd, E": "b7411728a36ad24",
    "y MMM": "59e614e6c0f56a0a",
    "y MMM d": "333b185b7068e865",
    "y MMM d, E": "3cefebacf3faa4b8",
    "y MMMM": "118ee93e94934ef4",
}


def get_xpstr_from_skeleton(english_skeleton: str) -> str:
    """
    Get Xpstr value from English skeleton pattern.
    
    Args:
        english_skeleton: English skeleton pattern (e.g., "E, MMM d")
        
    Returns:
        Xpstr value if found, empty string otherwise
    """
    try:
        if not english_skeleton or english_skeleton == "ERROR":
            return ""
        
        # Normalize the skeleton to handle dash variations
        normalized = normalize_english_skeleton(english_skeleton)
        
        # Try exact match first
        if normalized in SKELETON_TO_XPSTR:
            return SKELETON_TO_XPSTR[normalized]
        
        # Try original skeleton
        if english_skeleton in SKELETON_TO_XPSTR:
            return SKELETON_TO_XPSTR[english_skeleton]
        
        # Return empty string if not found
        return ""
    except Exception:
        # If anything goes wrong, return empty string to prevent batch processing from failing
        return ""


def english_to_skeleton(english_text: str, cldr_path: str):
    english_tokens = tokenize_date_expression(english_text)
    validate_tokens(english_tokens, "English string")
    validate_english_tokens(english_tokens, english_text)

    formatting_options = analyze_tokens_for_format_options(english_tokens, ENGLISH_DATE_DICT)
    options = generate_valid_combinations(formatting_options)
    skeleton_options = convert_to_skeleton_codes(options)
    string_options = format_skeleton_strings(skeleton_options)
    expanded_options = expand_dash_variations(string_options)

    english_df = load_english_reference_data(cldr_path)
    english_values = english_df['English'].dropna().values.tolist()
    
    # Clean thin spaces from the values for comparison
    english_values = [val.replace('\u2009', ' ') if isinstance(val, str) else val for val in english_values]
    
    # First try exact matches
    confirmed = [opt for opt in expanded_options if opt in english_values or len(set(opt.lower())) == 1]
    
    # If no exact matches, try to find the best approximation
    if not confirmed:
        # For zero-padded numbers, prefer MM over M
        # Check for MM/y first (zero-padded months)
        if 'MM/y' in expanded_options:
            confirmed = ['MM/y']
        # Then check for other patterns
        elif any(opt in ['dd/y'] for opt in expanded_options) and 'M/y' in english_values:
            confirmed = ['M/y']
        elif any(opt in ['MMM y', 'MMMM y'] for opt in expanded_options) and 'M/y' in english_values:
            confirmed = ['M/y']
        # Handle range expressions that might not have exact CLDR matches
        else:
            # Create a comprehensive range pattern mapping
            def skeleton_signature(value: str):
                tokens = tokenize_date_expression(value.replace('–', '-'))
                return [t for t in tokens if t.strip()]

            def find_best_range_match(pattern, english_values):
                """Find the best matching range pattern in CLDR data."""
                pattern_sig = skeleton_signature(pattern)
                pattern_normalized = pattern.replace('-', ' – ')

                # Exact structural match (including dash type differences)
                for value in english_values:
                    if skeleton_signature(value) == pattern_sig:
                        return value

                    if skeleton_signature(value) == skeleton_signature(pattern_normalized):
                        return value

                return None
            
            # Try to find matches for each expanded option
            for opt in expanded_options:
                match = find_best_range_match(opt, english_values)
                if match:
                    confirmed = [match]
                    break
    
    if not confirmed:
        if expanded_options:
            # Fall back to the most specific skeleton we generated
            confirmed = [expanded_options[0].replace('-', '–')]
        else:
            raise ValueError(f"No official CLDR skeleton for '{english_text}'.")

    chosen = confirmed[0]

    normalized_chosen = normalize_english_skeleton(chosen)
    if normalized_chosen not in VALID_ENGLISH_SKELETONS:
        raise ValueError("Invalid English skeleton generated (unsupported pattern).")
    english_skeleton_tokens = tokenize_date_expression(chosen)
    ambiguities, ambiguity_options = detect_ambiguities(english_tokens, english_skeleton_tokens)
    metainfo = get_metadata_for_skeleton(chosen, ambiguities, english_df)
    return chosen, ambiguities, metainfo, ambiguity_options


def resolve_ambiguities_with_selections(english_text: str, english_skeleton: str, ambiguity_selections: dict, ambiguity_options: dict, cldr_path: str):
    """
    Resolve ambiguities with user-selected options and return updated ambiguities and skeleton.
    
    Args:
        english_text: Original English text
        english_skeleton: Original English skeleton pattern (may need to be updated)
        ambiguity_selections: Dict mapping token position to selected option name
        ambiguity_options: Dict mapping token position to list of option dicts with name and skeleton_code
        cldr_path: Path to CLDR data
        
    Returns:
        tuple: (updated_skeleton, updated_ambiguities, metainfo)
    """
    from src.core.tokenizer import tokenize_date_expression
    english_tokens = tokenize_date_expression(english_text)
    english_skeleton_tokens = list(tokenize_date_expression(english_skeleton))
    
    # Build resolved ambiguities from user selections and update skeleton codes
    resolved_ambiguities = []
    for position, selected_option_name in ambiguity_selections.items():
        pos = int(position)
        if pos < len(english_skeleton_tokens) and pos in ambiguity_options:
            # Find the selected option to get its skeleton code
            selected_option = None
            for option in ambiguity_options[pos]:
                if option.get("name") == selected_option_name:
                    selected_option = option
                    break
            
            if selected_option:
                # Update the skeleton code for this position
                new_skeleton_code = selected_option.get("skeleton_code")
                if new_skeleton_code:
                    english_skeleton_tokens[pos] = new_skeleton_code
                resolved_ambiguities.append((pos, english_skeleton_tokens[pos], selected_option_name))
            else:
                # Fallback: use original skeleton code
                resolved_ambiguities.append((pos, english_skeleton_tokens[pos], selected_option_name))
    
    # Reconstruct the skeleton string
    updated_skeleton = "".join(english_skeleton_tokens)
    
    english_df = load_english_reference_data(cldr_path)
    metainfo = get_metadata_for_skeleton(updated_skeleton, resolved_ambiguities, english_df)
    
    return updated_skeleton, resolved_ambiguities, metainfo


def map_to_target(language: str, translation: str, english_text: str, english_skeleton: str, ambiguities, cldr_path: str, target_df: pd.DataFrame | None = None):
    if target_df is None:
        df = load_target_language_data(cldr_path, language)
    else:
        df = target_df

    date_dict, lexicon = populate_target_language_dict(df)
    target_tokens = semantic_tokenize(translation, date_dict, lexicon)
    validate_tokens(target_tokens, "Target language string")
    english_tokens = tokenize_date_expression(english_text)
    skeletons = map_english_to_target_skeleton(english_tokens, english_skeleton, target_tokens, date_dict, ambiguities, translation)
    # If nothing mapped, fall back to empty
    return skeletons or []


def handle_single_english(args):
    result = english_to_skeleton(args.english, args.cldr_path)
    eng = result[0]
    ambiguities = result[1]
    meta = result[2]
    return {"mode": "english", "english_skeleton": eng, "meta": meta}


def handle_single_cldr(args):
    result = english_to_skeleton(args.english, args.cldr_path)
    eng = result[0]
    ambiguities = result[1]
    meta = result[2]
    targets = map_to_target(args.language, args.translation, args.english, eng, ambiguities, args.cldr_path)
    return {"mode": "cldr", "english_skeleton": eng, "target_skeletons": targets, "language": args.language}


def handle_single_new(args):
    result = english_to_skeleton(args.english, args.cldr_path)
    eng = result[0]
    ambiguities = result[1]
    meta = result[2]
    df = pd.read_csv(args.elements_csv)
    targets = map_to_target(args.language, args.translation, args.english, eng, ambiguities, args.cldr_path, target_df=df)
    return {"mode": "new", "english_skeleton": eng, "target_skeletons": targets, "language": args.language}


def handle_batch_english(args):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["ENGLISH", "ENGLISH_SKELETON", "Xpstr"]) 
    writer.writeheader()
    
    try:
        with open(args.csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if 'ENGLISH' not in reader.fieldnames:
                raise ValueError("CSV must contain ENGLISH column. Please use the English list template.")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                text = (row.get('ENGLISH') or '').strip()
                if not text:
                    continue
                
                try:
                    result = english_to_skeleton(text, args.cldr_path)
                    eng_skel = result[0]
                    try:
                        xpstr = get_xpstr_from_skeleton(eng_skel)
                    except Exception as xpstr_error:
                        # If Xpstr lookup fails, continue with empty string
                        print(f"Warning: Xpstr lookup failed for skeleton '{eng_skel}': {xpstr_error}")
                        xpstr = ""
                    writer.writerow({"ENGLISH": text, "ENGLISH_SKELETON": eng_skel, "Xpstr": xpstr})
                except Exception as e:
                    # Put ERROR for this specific row
                    print(f"Error processing row {row_num}: {text}: {str(e)}")
                    writer.writerow({"ENGLISH": text, "ENGLISH_SKELETON": "ERROR", "Xpstr": ""})
                    
    except Exception as e:
        if "CSV must contain" in str(e):
            raise e
        else:
            raise ValueError(f"Error reading CSV file: {str(e)}. Please ensure you're using the correct template format.")
            
    return {"csv_content": out.getvalue(), "suggested_filename": "english_results.csv"}


def handle_batch_cldr(args):
    print(f"Starting batch CLDR processing for language: {args.language}")
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["ENGLISH", "TARGET", "ENGLISH_SKELETON", "TARGET_SKELETON", "Xpstr"]) 
    writer.writeheader()
    
    try:
        print(f"Opening CSV file: {args.csv}")
        with open(args.csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if 'ENGLISH' not in reader.fieldnames or 'TARGET' not in reader.fieldnames:
                raise ValueError("CSV must contain ENGLISH and TARGET columns. Please use the English, translation pairs template.")
            
            row_count = 0
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                english = (row.get('ENGLISH') or '').strip()
                target = (row.get('TARGET') or '').strip()
                if not english or not target:
                    continue
                
                row_count += 1
                if row_count % 10 == 0:
                    print(f"Processing row {row_num}...")
                
                try:
                    result = english_to_skeleton(english, args.cldr_path)
                    eng_skel = result[0]
                    ambiguities = result[1]
                    targets = map_to_target(args.language, target, english, eng_skel, ambiguities, args.cldr_path)
                    try:
                        xpstr = get_xpstr_from_skeleton(eng_skel)
                    except Exception as xpstr_error:
                        # If Xpstr lookup fails, continue with empty string
                        print(f"Warning: Xpstr lookup failed for skeleton '{eng_skel}': {xpstr_error}")
                        xpstr = ""
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": eng_skel,
                        "TARGET_SKELETON": "; ".join(targets) if targets else "ERROR",
                        "Xpstr": xpstr
                    })
                except Exception as e:
                    # Put ERROR for this specific row
                    print(f"Error processing row {row_num}: {english} -> {target}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": "ERROR",
                        "TARGET_SKELETON": "ERROR",
                        "Xpstr": ""
                    })
            
            print(f"Completed processing {row_count} rows")
                    
    except Exception as e:
        if "CSV must contain" in str(e):
            raise e
        else:
            raise ValueError(f"Error reading CSV file: {str(e)}. Please ensure you're using the correct template format.")
            
    return {"csv_content": out.getvalue(), "suggested_filename": f"{args.language}_results.csv"}


def handle_batch_noncldr(args):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["ENGLISH", "TARGET", "ENGLISH_SKELETON", "TARGET_SKELETON", "Xpstr"]) 
    writer.writeheader()
    
    try:
        # Load the custom date elements
        df = pd.read_csv(args.elements_csv)
        
        with open(args.pairs_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if 'ENGLISH' not in reader.fieldnames or 'TARGET' not in reader.fieldnames:
                raise ValueError("Pairs CSV must contain ENGLISH and TARGET columns. Please use the English, translation pairs template.")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                english = (row.get('ENGLISH') or '').strip()
                target = (row.get('TARGET') or '').strip()
                if not english or not target:
                    continue
                
                try:
                    result = english_to_skeleton(english, args.cldr_path)
                    eng_skel = result[0]
                    ambiguities = result[1]
                    targets = map_to_target(args.language, target, english, eng_skel, ambiguities, args.cldr_path, target_df=df)
                    try:
                        xpstr = get_xpstr_from_skeleton(eng_skel)
                    except Exception as xpstr_error:
                        # If Xpstr lookup fails, continue with empty string
                        print(f"Warning: Xpstr lookup failed for skeleton '{eng_skel}': {xpstr_error}")
                        xpstr = ""
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": eng_skel,
                        "TARGET_SKELETON": "; ".join(targets) if targets else "ERROR",
                        "Xpstr": xpstr
                    })
                except Exception as e:
                    # Put ERROR for this specific row
                    print(f"Error processing row {row_num}: {english} -> {target}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": "ERROR",
                        "TARGET_SKELETON": "ERROR",
                        "Xpstr": ""
                    })
                    
    except Exception as e:
        if "CSV must contain" in str(e) or "Pairs CSV must contain" in str(e):
            raise e
        else:
            raise ValueError(f"Error reading CSV file: {str(e)}. Please ensure you're using the correct template format.")
            
    return {"csv_content": out.getvalue(), "suggested_filename": f"{args.language}_results.csv"}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("single-english")
    p1.add_argument("--english", required=True)
    p1.add_argument("--cldr_path", required=True)

    p2 = sub.add_parser("single-cldr")
    p2.add_argument("--english", required=True)
    p2.add_argument("--language", required=True)
    p2.add_argument("--translation", required=True)
    p2.add_argument("--cldr_path", required=True)

    p3 = sub.add_parser("single-new")
    p3.add_argument("--english", required=True)
    p3.add_argument("--language", required=True)
    p3.add_argument("--translation", required=True)
    p3.add_argument("--elements_csv", required=True)
    p3.add_argument("--cldr_path", required=True)

    p4 = sub.add_parser("batch-english")
    p4.add_argument("--csv", required=True)
    p4.add_argument("--cldr_path", required=True)

    p5 = sub.add_parser("batch-cldr")
    p5.add_argument("--csv", required=True)
    p5.add_argument("--language", required=True)
    p5.add_argument("--cldr_path", required=True)

    p6 = sub.add_parser("batch-noncldr")
    p6.add_argument("--pairs_csv", required=True)
    p6.add_argument("--elements_csv", required=True)
    p6.add_argument("--language", required=True)
    p6.add_argument("--cldr_path", required=True)

    args = parser.parse_args()
    @contextmanager
    def suppress_stdout():
        saved = sys.stdout
        try:
            sys.stdout = io.StringIO()
            yield
        finally:
            sys.stdout = saved

    try:
        with suppress_stdout():
            if args.cmd == "single-english":
                out = handle_single_english(args)
            elif args.cmd == "single-cldr":
                out = handle_single_cldr(args)
            elif args.cmd == "single-new":
                out = handle_single_new(args)
            elif args.cmd == "batch-english":
                out = handle_batch_english(args)
            elif args.cmd == "batch-cldr":
                out = handle_batch_cldr(args)
            elif args.cmd == "batch-noncldr":
                out = handle_batch_noncldr(args)
            else:
                raise ValueError("Unknown command")
        print(json.dumps(out))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()


