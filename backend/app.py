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

# Add src to path
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from api_bridge import (
    english_to_skeleton, 
    map_to_target, 
    handle_batch_english, 
    handle_batch_cldr, 
    handle_batch_noncldr
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
    elements_csv: UploadFile = File(None)
):
    """Process various types of requests"""
    try:
        cldr_path = str(PROJECT_ROOT / "cldr_data")
        
        if mode == "single-english":
            if not english:
                raise HTTPException(status_code=400, detail="English text required")
            
            result = english_to_skeleton(english, cldr_path)
            return {
                "success": True,
                "english_skeleton": result[0] if result else "ERROR",
                "ambiguities": result[1] if len(result) > 1 else [],
                "metadata": result[2] if len(result) > 2 else []
            }
        
        elif mode == "single-cldr":
            if not all([english, language, translation]):
                raise HTTPException(status_code=400, detail="English, language, and translation required")
            
            eng_skel, ambiguities, metainfo = english_to_skeleton(english, cldr_path)
            targets = map_to_target(language, translation, english, eng_skel, ambiguities, cldr_path)
            
            return {
                "success": True,
                "english_skeleton": eng_skel,
                "target_skeletons": targets,
                "xpath": metainfo[0][2][0] if metainfo and len(metainfo) > 0 and len(metainfo[0]) > 2 else ""
            }
        
        elif mode == "single-new":
            if not all([english, language, translation]):
                raise HTTPException(status_code=400, detail="English, language, and translation required")
            
            if not elements_csv or elements_csv.filename is None:
                raise HTTPException(status_code=400, detail="Elements CSV file required")
            
            # For now, return a placeholder response
            # TODO: Implement proper single-new processing with elements CSV
            return {
                "success": True,
                "english_skeleton": "MMMM d, y",  # Placeholder
                "target_skeletons": ["MMMM d, y"],  # Placeholder
                "message": "Single-new mode not fully implemented yet"
            }
        
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
                return {"success": True, "csv_content": result}
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
                return {"success": True, "csv_content": result}
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
                
                args = Args()
                result = handle_batch_noncldr(args)
                return {"success": True, "csv_content": result}
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
