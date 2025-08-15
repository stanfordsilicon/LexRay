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
from src.core.constants import ENGLISH_DATE_DICT


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
    confirmed = [opt for opt in expanded_options if opt in english_df['English'].values.tolist() or len(set(opt.lower())) == 1]
    if not confirmed:
        raise ValueError(f"No official CLDR skeleton for '{english_text}'.")

    chosen = confirmed[0]
    english_skeleton_tokens = tokenize_date_expression(chosen)
    ambiguities = detect_ambiguities(english_tokens, english_skeleton_tokens)
    metainfo = get_metadata_for_skeleton(chosen, ambiguities, english_df)
    return chosen, ambiguities, metainfo


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
    eng, ambiguities, meta = english_to_skeleton(args.english, args.cldr_path)
    return {"mode": "english", "english_skeleton": eng, "meta": meta}


def handle_single_cldr(args):
    eng, ambiguities, meta = english_to_skeleton(args.english, args.cldr_path)
    targets = map_to_target(args.language, args.translation, args.english, eng, ambiguities, args.cldr_path)
    return {"mode": "cldr", "english_skeleton": eng, "target_skeletons": targets, "language": args.language}


def handle_single_new(args):
    eng, ambiguities, meta = english_to_skeleton(args.english, args.cldr_path)
    df = pd.read_csv(args.elements_csv)
    targets = map_to_target(args.language, args.translation, args.english, eng, ambiguities, args.cldr_path, target_df=df)
    return {"mode": "new", "english_skeleton": eng, "target_skeletons": targets, "language": args.language}


def handle_batch_english(args):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["ENGLISH", "ENGLISH_SKELETON"]) 
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
                    eng_skel, _, _ = english_to_skeleton(text, args.cldr_path)
                    writer.writerow({"ENGLISH": text, "ENGLISH_SKELETON": eng_skel})
                except Exception as e:
                    # Put ERROR for this specific row
                    writer.writerow({"ENGLISH": text, "ENGLISH_SKELETON": "ERROR"})
                    
    except Exception as e:
        if "CSV must contain" in str(e):
            raise e
        else:
            raise ValueError(f"Error reading CSV file: {str(e)}. Please ensure you're using the correct template format.")
            
    return {"csv_content": out.getvalue(), "suggested_filename": "english_results.csv"}


def handle_batch_cldr(args):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["ENGLISH", "TARGET", "ENGLISH_SKELETON", "TARGET_SKELETON"]) 
    writer.writeheader()
    
    try:
        with open(args.csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if 'ENGLISH' not in reader.fieldnames or 'TARGET' not in reader.fieldnames:
                raise ValueError("CSV must contain ENGLISH and TARGET columns. Please use the English, translation pairs template.")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                english = (row.get('ENGLISH') or '').strip()
                target = (row.get('TARGET') or '').strip()
                if not english or not target:
                    continue
                
                try:
                    eng_skel, ambiguities, _ = english_to_skeleton(english, args.cldr_path)
                    targets = map_to_target(args.language, target, english, eng_skel, ambiguities, args.cldr_path)
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": eng_skel,
                        "TARGET_SKELETON": ", ".join(targets) if targets else "ERROR"
                    })
                except Exception as e:
                    # Put ERROR for this specific row
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": "ERROR",
                        "TARGET_SKELETON": "ERROR"
                    })
                    
    except Exception as e:
        if "CSV must contain" in str(e):
            raise e
        else:
            raise ValueError(f"Error reading CSV file: {str(e)}. Please ensure you're using the correct template format.")
            
    return {"csv_content": out.getvalue(), "suggested_filename": f"{args.language}_results.csv"}


def handle_batch_noncldr(args):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["ENGLISH", "TARGET", "ENGLISH_SKELETON", "TARGET_SKELETON"]) 
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
                    eng_skel, ambiguities, _ = english_to_skeleton(english, args.cldr_path)
                    targets = map_to_target(args.language, target, english, eng_skel, ambiguities, args.cldr_path, target_df=df)
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": eng_skel,
                        "TARGET_SKELETON": ", ".join(targets) if targets else "ERROR"
                    })
                except Exception as e:
                    # Put ERROR for this specific row
                    writer.writerow({
                        "ENGLISH": english,
                        "TARGET": target,
                        "ENGLISH_SKELETON": "ERROR",
                        "TARGET_SKELETON": "ERROR"
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


