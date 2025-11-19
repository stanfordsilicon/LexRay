#!/usr/bin/env python3
"""
FastAPI web server for LexRay backend
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import pandas as pd

# Add src to path
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from api_bridge import (
    english_to_skeleton, 
    map_to_target, 
    handle_batch_english, 
    handle_batch_cldr, 
    handle_batch_noncldr,
    resolve_ambiguities_with_selections
)

app = FastAPI(title="LexRay API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "LexRay API is running"}

@app.get("/api/languages")
async def get_languages():
    """Get list of available languages"""
    try:
        cldr_dir = PROJECT_ROOT / "cldr_data"
        languages = []
        
        if cldr_dir.exists():
            for file in cldr_dir.glob("*_moderate.xlsx"):
                lang_name = file.stem.replace("_moderate", "")
                if lang_name.lower() != "english":
                    languages.append(lang_name)
        
        languages.sort()
        return {"languages": languages}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Could not read CLDR languages: {str(e)}"}
        )

@app.post("/api/process")
async def process_request(
    mode: str = Form(...),
    english: str = Form(None),
    language: str = Form(None),
    translation: str = Form(None),
    csv: UploadFile = File(None),
    pairs_csv: UploadFile = File(None),
    elements_csv: UploadFile = File(None),
    english_skeleton: str = Form(None),
    ambiguity_selections: str = Form(None),
    ambiguity_options: str = Form(None)
):
    """Process various types of requests"""
    try:
        cldr_path = str(PROJECT_ROOT / "cldr_data")
        
        # Debug: Log the received data
        print(f"DEBUG: Received mode={mode}, english='{english}', language='{language}', translation='{translation}'")
        
        if mode == "single-english":
            if not english:
                raise HTTPException(status_code=400, detail="English text required")
            
            try:
                result = english_to_skeleton(english, cldr_path)
                eng_skel = result[0] if result else "ERROR"
                ambiguities = result[1] if len(result) > 1 else []
                metainfo = result[2] if len(result) > 2 else []
                ambiguity_options = result[3] if len(result) > 3 else {}
                
                # If there are ambiguity options, return them for user selection
                if ambiguity_options:
                    return {
                        "success": True,
                        "requires_ambiguity_resolution": True,
                        "english_skeleton": eng_skel,
                        "ambiguity_options": ambiguity_options,
                        "ambiguities": ambiguities,
                        "metadata": metainfo
                    }
                
                return {
                    "success": True,
                    "requires_ambiguity_resolution": False,
                    "english_skeleton": eng_skel,
                    "ambiguities": ambiguities,
                    "metadata": metainfo
                }
            except Exception as e:
                error_msg = str(e)
                if "not in the English data set" in error_msg:
                    return {
                        "success": False,
                        "error": f"Non-Latin characters detected: '{english}'. Please use English date formats like 'September 5, 2025' or '2025-09-05'.",
                        "suggestion": "Try converting to English format first, or use the CLDR language tab for non-English dates."
                    }
                if "Invalid English skeleton generated" in error_msg:
                    return {
                        "success": False,
                        "error": "Invalid input. Please re-enter."
                    }
                else:
                    raise HTTPException(status_code=500, detail=f"Processing error: {error_msg}")
        
        elif mode == "single-cldr":
            if not all([english, language, translation]):
                raise HTTPException(status_code=400, detail="English, language, and translation required")
            
            try:
                result = english_to_skeleton(english, cldr_path)
                eng_skel = result[0]
                ambiguities = result[1]
                metainfo = result[2]
                ambiguity_options = result[3] if len(result) > 3 else {}
                
                # If there are ambiguity options, return them for user selection
                if ambiguity_options:
                    return {
                        "success": True,
                        "requires_ambiguity_resolution": True,
                        "english_skeleton": eng_skel,
                        "ambiguity_options": ambiguity_options,
                        "ambiguities": ambiguities,
                        "metadata": metainfo
                    }
                
                targets = map_to_target(language, translation, english, eng_skel, ambiguities, cldr_path)
                
                # Debug logging
                print(f"DEBUG single-cldr: eng_skel={eng_skel}, targets={targets}, language={language}, translation={translation}")
                
                # Check if targets is empty or invalid
                if not targets or not isinstance(targets, list) or len(targets) == 0:
                    # If no targets found, return error
                    return {
                        "success": False,
                        "error": "Could not generate target skeleton. Please check that the translation matches the English date format.",
                        "english_skeleton": eng_skel,
                        "target_skeletons": []
                    }
                
                # Check for actual corruption (non-printable characters, encoding errors)
                # Single quotes are legitimate for literal text, so don't filter those out
                valid_targets = []
                for target in targets:
                    target_str = str(target)
                    # Check for actual corruption: non-ASCII characters that aren't valid CLDR codes
                    # Valid CLDR skeleton can contain: letters, numbers, spaces, quotes, punctuation
                    if target_str and any(c.isprintable() or c in ['\n', '\r', '\t'] for c in target_str):
                        # Check if it contains only valid CLDR skeleton characters
                        # CLDR skeletons can have: M, d, y, E, a, h, H, m, s, quotes, spaces, punctuation
                        if any(c.isalnum() or c in ["'", '"', " ", ",", "/", "-", ".", ":", ";"] for c in target_str):
                            valid_targets.append(target_str)
                
                if not valid_targets:
                    # If all targets were filtered out, return the first one anyway (might be false positive)
                    valid_targets = [str(targets[0])] if targets else []
                
                # Safety check: if target skeleton equals English skeleton, something went wrong
                # This should never happen - target should be different (e.g., different order, literal text)
                if valid_targets and len(valid_targets) == 1 and valid_targets[0] == eng_skel:
                    return {
                        "success": False,
                        "error": "Target skeleton matches English skeleton. This usually means the mapping failed. Please check that the translation is correct and matches the English date format.",
                        "english_skeleton": eng_skel,
                        "target_skeletons": []
                    }
                
                return {
                    "success": True,
                    "english_skeleton": eng_skel,
                    "target_skeletons": valid_targets,
                    "xpath": metainfo[0][2][0] if metainfo and len(metainfo) > 0 and len(metainfo[0]) > 2 else ""
                }
            except Exception as e:
                error_msg = str(e)
                if "Invalid English skeleton generated" in error_msg:
                    return {
                        "success": False,
                        "error": "Invalid input. Please re-enter."
                    }
                return {
                    "success": False,
                    "error": f"CLDR processing failed: {error_msg}",
                    "suggestion": "Try using a different language or check if the translation is correct."
                }
        
        elif mode == "resolve-ambiguity":
            # Handle ambiguity resolution - for English-only mode
            if not english:
                raise HTTPException(status_code=400, detail="English text required")
            
            if not ambiguity_selections:
                raise HTTPException(status_code=400, detail="Ambiguity selections required")
            
            if not english_skeleton:
                raise HTTPException(status_code=400, detail="English skeleton required")
            
            import json
            try:
                ambiguity_selections_dict = json.loads(ambiguity_selections)
                ambiguity_options_dict = json.loads(ambiguity_options) if ambiguity_options else {}
            except:
                raise HTTPException(status_code=400, detail="Invalid ambiguity selections format")
            
            # Resolve ambiguities with user selections
            updated_skeleton, resolved_ambiguities, metainfo = resolve_ambiguities_with_selections(
                english, english_skeleton, ambiguity_selections_dict, ambiguity_options_dict, cldr_path
            )
            
            return {
                "success": True,
                "requires_ambiguity_resolution": False,
                "english_skeleton": updated_skeleton,
                "ambiguities": resolved_ambiguities,
                "metadata": metainfo
            }
        
        elif mode == "resolve-ambiguity-cldr":
            # Handle ambiguity resolution for CLDR mode
            if not all([english, language, translation]):
                raise HTTPException(status_code=400, detail="English, language, and translation required")
            
            if not ambiguity_selections:
                raise HTTPException(status_code=400, detail="Ambiguity selections required")
            
            if not english_skeleton:
                raise HTTPException(status_code=400, detail="English skeleton required")
            
            import json
            try:
                ambiguity_selections_dict = json.loads(ambiguity_selections)
                ambiguity_options_dict = json.loads(ambiguity_options) if ambiguity_options else {}
            except:
                raise HTTPException(status_code=400, detail="Invalid ambiguity selections format")
            
            # Resolve ambiguities with user selections
            updated_skeleton, resolved_ambiguities, metainfo = resolve_ambiguities_with_selections(
                english, english_skeleton, ambiguity_selections_dict, ambiguity_options_dict, cldr_path
            )
            
            # Map to target language using the updated skeleton
            targets = map_to_target(language, translation, english, updated_skeleton, resolved_ambiguities, cldr_path)
            
            if not targets or not isinstance(targets, list) or len(targets) == 0:
                return {
                    "success": False,
                    "error": "Could not generate target skeleton. Please check that the translation matches the English date format.",
                    "english_skeleton": english_skeleton,
                    "target_skeletons": []
                }
            
            valid_targets = []
            for target in targets:
                target_str = str(target)
                if target_str and any(c.isprintable() or c in ['\n', '\r', '\t'] for c in target_str):
                    if any(c.isalnum() or c in ["'", '"', " ", ",", "/", "-", ".", ":", ";"] for c in target_str):
                        valid_targets.append(target_str)
            
            if not valid_targets:
                valid_targets = [str(targets[0])] if targets else []
            
            return {
                "success": True,
                "english_skeleton": updated_skeleton,
                "target_skeletons": valid_targets,
                "xpath": metainfo[0][2][0] if metainfo and len(metainfo) > 0 and len(metainfo[0]) > 2 else ""
            }
        
        elif mode == "resolve-ambiguity-noncldr":
            # Handle ambiguity resolution for non-CLDR mode
            if not all([english, language, translation]):
                raise HTTPException(status_code=400, detail="English, language, and translation required")
            
            if not elements_csv or elements_csv.filename is None:
                raise HTTPException(status_code=400, detail="Elements CSV file required")
            
            if not ambiguity_selections:
                raise HTTPException(status_code=400, detail="Ambiguity selections required")
            
            if not english_skeleton:
                raise HTTPException(status_code=400, detail="English skeleton required")
            
            import json
            try:
                ambiguity_selections_dict = json.loads(ambiguity_selections)
                ambiguity_options_dict = json.loads(ambiguity_options) if ambiguity_options else {}
            except:
                raise HTTPException(status_code=400, detail="Invalid ambiguity selections format")
            
            # Save uploaded elements CSV temporarily
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as elements_tmp:
                elements_content = await elements_csv.read()
                elements_tmp.write(elements_content)
                elements_path = elements_tmp.name
            
            try:
                # Resolve ambiguities with user selections
                updated_skeleton, resolved_ambiguities, metainfo = resolve_ambiguities_with_selections(
                    english, english_skeleton, ambiguity_selections_dict, ambiguity_options_dict, cldr_path
                )
                
                # Load elements CSV as DataFrame
                elements_df = pd.read_csv(elements_path)
                
                # Map to target using the custom elements CSV and updated skeleton
                targets = map_to_target(language, translation, english, updated_skeleton, resolved_ambiguities, cldr_path, target_df=elements_df)
                
                if not targets or not isinstance(targets, list) or len(targets) == 0:
                    return {
                        "success": False,
                        "error": "Could not generate target skeleton. Please check that the translation matches the English date format and that the elements CSV contains the necessary date elements.",
                        "english_skeleton": updated_skeleton,
                        "target_skeletons": []
                    }
                
                valid_targets = []
                for target in targets:
                    target_str = str(target)
                    if target_str and any(c.isprintable() or c in ['\n', '\r', '\t'] for c in target_str):
                        if any(c.isalnum() or c in ["'", '"', " ", ",", "/", "-", ".", ":", ";"] for c in target_str):
                            valid_targets.append(target_str)
                
                if not valid_targets:
                    valid_targets = [str(targets[0])] if targets else []
                
                return {
                    "success": True,
                    "english_skeleton": updated_skeleton,
                    "target_skeletons": valid_targets,
                    "xpath": metainfo[0][2][0] if metainfo and len(metainfo) > 0 and len(metainfo[0]) > 2 else ""
                }
            finally:
                os.unlink(elements_path)
        
        elif mode == "single-new":
            if not all([english, language, translation]):
                raise HTTPException(status_code=400, detail="English, language, and translation required")
            
            if not elements_csv or elements_csv.filename is None:
                raise HTTPException(status_code=400, detail="Elements CSV file required")
            
            # Save uploaded elements CSV temporarily
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as elements_tmp:
                elements_content = await elements_csv.read()
                elements_tmp.write(elements_content)
                elements_path = elements_tmp.name
            
            try:
                # Get English skeleton
                result = english_to_skeleton(english, cldr_path)
                eng_skel = result[0]
                ambiguities = result[1]
                metainfo = result[2]
                ambiguity_options = result[3] if len(result) > 3 else {}
                
                # If there are ambiguity options, return them for user selection
                if ambiguity_options:
                    return {
                        "success": True,
                        "requires_ambiguity_resolution": True,
                        "english_skeleton": eng_skel,
                        "ambiguity_options": ambiguity_options,
                        "ambiguities": ambiguities,
                        "metadata": metainfo
                    }
                
                # Load elements CSV as DataFrame
                elements_df = pd.read_csv(elements_path)
                
                # Map to target using the custom elements CSV
                targets = map_to_target(language, translation, english, eng_skel, ambiguities, cldr_path, target_df=elements_df)
                
                # Debug logging
                print(f"DEBUG single-new: eng_skel={eng_skel}, targets={targets}, language={language}, translation={translation}")
                
                # Check if targets is empty or invalid
                if not targets or not isinstance(targets, list) or len(targets) == 0:
                    return {
                        "success": False,
                        "error": "Could not generate target skeleton. Please check that the translation matches the English date format and that the elements CSV contains the necessary date elements.",
                        "english_skeleton": eng_skel,
                        "target_skeletons": []
                    }
                
                # Safety check: if target skeleton equals English skeleton, something went wrong
                if targets and len(targets) == 1 and targets[0] == eng_skel:
                    return {
                        "success": False,
                        "error": "Target skeleton matches English skeleton. This usually means the mapping failed. Please check that the translation is correct and that the elements CSV contains the necessary date elements.",
                        "english_skeleton": eng_skel,
                        "target_skeletons": []
                    }
                
                return {
                    "success": True,
                    "english_skeleton": eng_skel,
                    "target_skeletons": targets,
                    "xpath": metainfo[0][2][0] if metainfo and len(metainfo) > 0 and len(metainfo[0]) > 2 else ""
                }
            except Exception as e:
                error_msg = str(e)
                if "Invalid English skeleton generated" in error_msg:
                    return {
                        "success": False,
                        "error": "Invalid input. Please re-enter."
                    }
                return {
                    "success": False,
                    "error": f"Processing failed: {error_msg}",
                    "suggestion": "Please check that the elements CSV is in the correct format and contains the necessary date elements."
                }
            finally:
                os.unlink(elements_path)
        
        elif mode == "batch-english":
            if not csv:
                raise HTTPException(status_code=400, detail="CSV file required")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
                content = await csv.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Create args object like the CLI expects
                class Args:
                    def __init__(self):
                        self.csv = tmp_path
                        self.cldr_path = cldr_path
                
                args = Args()
                result = handle_batch_english(args)
                # Ensure we return the correct structure - handle both nested and flat responses
                if isinstance(result, dict):
                    csv_content = result.get("csv_content", "")
                    if isinstance(csv_content, dict):
                        csv_content = csv_content.get("csv_content", "")
                    suggested_filename = result.get("suggested_filename", "english_results.csv")
                    if isinstance(suggested_filename, dict):
                        suggested_filename = suggested_filename.get("suggested_filename", "english_results.csv")
                else:
                    csv_content = ""
                    suggested_filename = "english_results.csv"
                
                return {
                    "success": True,
                    "csv_content": csv_content if isinstance(csv_content, str) else str(csv_content),
                    "suggested_filename": suggested_filename if isinstance(suggested_filename, str) else str(suggested_filename)
                }
            finally:
                os.unlink(tmp_path)
        
        elif mode == "batch-cldr":
            if not all([csv, language]):
                raise HTTPException(status_code=400, detail="CSV file and language required")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
                content = await csv.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Create args object like the CLI expects
                class Args:
                    def __init__(self):
                        self.csv = tmp_path
                        self.language = language
                        self.cldr_path = cldr_path
                
                args = Args()
                result = handle_batch_cldr(args)
                # Ensure we return the correct structure - handle both nested and flat responses
                if isinstance(result, dict):
                    csv_content = result.get("csv_content", "")
                    if isinstance(csv_content, dict):
                        csv_content = csv_content.get("csv_content", "")
                    suggested_filename = result.get("suggested_filename", f"{language}_results.csv")
                    if isinstance(suggested_filename, dict):
                        suggested_filename = suggested_filename.get("suggested_filename", f"{language}_results.csv")
                else:
                    csv_content = ""
                    suggested_filename = f"{language}_results.csv"
                
                return {
                    "success": True,
                    "csv_content": csv_content if isinstance(csv_content, str) else str(csv_content),
                    "suggested_filename": suggested_filename if isinstance(suggested_filename, str) else str(suggested_filename)
                }
            finally:
                os.unlink(tmp_path)
        
        elif mode == "batch-noncldr":
            if not all([pairs_csv, elements_csv, language]):
                raise HTTPException(status_code=400, detail="Pairs CSV, elements CSV, and language required")
            
            # Save uploaded files temporarily
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as pairs_tmp:
                pairs_content = await pairs_csv.read()
                pairs_tmp.write(pairs_content)
                pairs_path = pairs_tmp.name
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as elements_tmp:
                elements_content = await elements_csv.read()
                elements_tmp.write(elements_content)
                elements_path = elements_tmp.name
            
            try:
                # Create args object like the CLI expects
                class Args:
                    def __init__(self):
                        self.pairs_csv = pairs_path
                        self.elements_csv = elements_path
                        self.language = language
                        self.cldr_path = cldr_path
                
                args = Args()
                result = handle_batch_noncldr(args)
                
                # Debug logging
                print(f"DEBUG batch-noncldr: result type = {type(result)}, result keys = {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                # Ensure we return the correct structure - handle both nested and flat responses
                csv_content = ""
                suggested_filename = f"{language}_results.csv"
                
                if isinstance(result, dict):
                    # Get csv_content - handle nested structure
                    raw_csv = result.get("csv_content", "")
                    if isinstance(raw_csv, dict):
                        # Double-nested case
                        csv_content = raw_csv.get("csv_content", "")
                        if not csv_content and "csv_content" in raw_csv:
                            csv_content = str(raw_csv.get("csv_content", ""))
                    elif isinstance(raw_csv, str):
                        csv_content = raw_csv
                    else:
                        csv_content = str(raw_csv) if raw_csv else ""
                    
                    # Get suggested_filename - handle nested structure
                    raw_filename = result.get("suggested_filename", f"{language}_results.csv")
                    if isinstance(raw_filename, dict):
                        suggested_filename = raw_filename.get("suggested_filename", f"{language}_results.csv")
                    elif isinstance(raw_filename, str):
                        suggested_filename = raw_filename
                    else:
                        suggested_filename = str(raw_filename) if raw_filename else f"{language}_results.csv"
                
                # Final safety check - ensure we have strings
                if not isinstance(csv_content, str):
                    csv_content = str(csv_content) if csv_content else ""
                if not isinstance(suggested_filename, str):
                    suggested_filename = str(suggested_filename) if suggested_filename else f"{language}_results.csv"
                
                print(f"DEBUG batch-noncldr: final csv_content type = {type(csv_content)}, length = {len(csv_content)}")
                
                return {
                    "success": True,
                    "csv_content": csv_content,
                    "suggested_filename": suggested_filename
                }
            finally:
                os.unlink(pairs_path)
                os.unlink(elements_path)
        
        else:
            raise HTTPException(status_code=400, detail="Unknown mode")
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
