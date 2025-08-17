import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from collections import Counter

from backend.audio_utils import convert_to_wav
import librosa
import librosa
import numpy as np
import json
from backend.pitch_utils import extract_pitch_contour, compare_contours

app = FastAPI(title="Shazam for Kishore Kumar Songs")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load local pitch database (Hot Reload Triggered)
PITCH_DB_PATH = "data/pitch_db.json"
try:
    with open(PITCH_DB_PATH, "r") as f:
        pitch_db_raw = json.load(f)
        pitch_db = {}
        for k, v in pitch_db_raw.items():
            if isinstance(v, dict) and "pitches" in v:
                pitch_db[k] = {
                    "pitches": np.array(v["pitches"]),
                    "indices": np.array(v["indices"]),
                    "parsons": v.get("parsons", "")
                }
            else:
                pitch_db[k] = {
                    "pitches": np.array(v),
                    "indices": np.arange(len(v)),
                    "parsons": ""
                }
    print(f"Loaded pitch DB with {len(pitch_db)} songs.")
except Exception as e:
    print(f"Could not load pitch DB: {e}")
    pitch_db = {}

@app.post("/api/identify")
async def identify_song(audio: UploadFile = File(...)):
    if not pitch_db:
        raise HTTPException(status_code=500, detail="Pitch Database is empty or not loaded.")
        
    print(f"Received audio file: {audio.filename}")
    
    # Save the uploaded file temporarily
    suffix = os.path.splitext(audio.filename)[1] if audio.filename else ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        shutil.copyfileobj(audio.file, temp_audio)
        temp_audio_path = temp_audio.name
        
    try:
        # Convert to standardized WAV format
        wav_path = convert_to_wav(temp_audio_path)
        
        # Load audio using librosa
        y, sr = librosa.load(wav_path, sr=16000, mono=True)
        
        # Generate Pitch Contour
        print("Extracting pitch contour from humming...")
        query_contour, query_indices = extract_pitch_contour(y, sr)
        
        if len(query_contour) == 0:
            return {"song": "No clear humming detected", "confidence": 0}
            
        # Calculate time in seconds where the user started humming (pyin default hop_length is 512)
        query_start_frame = query_indices[0]
        query_start_time = (query_start_frame * 512) / sr
            
        print("Comparing against database using DTW...")
        
        results = []
        for song_name, target_data in pitch_db.items():
            target_contour = target_data["pitches"]
            target_indices = target_data["indices"]
            
            dist, target_start_idx = compare_contours(query_contour, target_contour)
            
            # Map the DTW match index back to the TRUE original frame index!
            if target_start_idx < len(target_indices):
                true_target_frame = target_indices[target_start_idx]
            else:
                true_target_frame = 0
                
            target_start_time = (true_target_frame * 512) / sr
            
            results.append({
                "song": song_name, 
                "distance": dist,
                "target_start_time": target_start_time
            })
            
        # Sort results by distance (lower is better)
        results.sort(key=lambda x: x['distance'])
        
        if not results:
            return {"song": "No match found", "confidence": 0}
            
        best_match = results[0]
        best_match_song = best_match['song']
        best_distance = best_match['distance']
        
        # FIX: The normalized distance is the average error in SEMITONES per frame.
        # A distance of 1.0 means an average error of 1 semitone. 
        # Previously we did 100 - (dist * 1.5). So a 10 semitone error (terrible match) gave 85%!
        # Now we do 100 - (dist * 20). 
        # A 1 semitone error gives 80%. A 5 semitone error gives 0%.
        confidence = max(0, min(100, 100 - (best_distance * 20)))
        
        # If it's a terrible match, just say no match
        if confidence < 10:
            return {"song": "No match found", "confidence": 0}
            
        # Format top 3 matches
        top_matches = []
        for r in results[:3]:
            conf = max(0, min(100, 100 - (r['distance'] * 20)))
            top_matches.append({
                "song": r['song'],
                "confidence": round(conf, 1),
                "target_start_time": round(r['target_start_time'], 1)
            })
            
        return {
            "song": best_match_song,
            "confidence": round(confidence, 1),
            "query_start_time": round(query_start_time, 1),
            "target_start_time": round(best_match['target_start_time'], 1),
            "top_matches": top_matches
        }
        
    except Exception as e:
        print(f"Error identifying song: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp files
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if 'wav_path' in locals() and os.path.exists(wav_path):
            os.remove(wav_path)

@app.get("/api/songs")
def get_songs():
    # Return keys from the loaded pitch database
    songs = [name.replace('.webm', '') for name in pitch_db.keys()]
    return {"songs": songs}

@app.get("/")
def health_check():
    return {"status": "healthy"}
