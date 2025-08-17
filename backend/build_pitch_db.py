import os
import json
import librosa
from backend.pitch_utils import extract_pitch_contour

def build_db():
    base_dir = "data/separated/htdemucs"
    db_path = "data/pitch_db.json"
    
    db = {}
    
    # Iterate through all folders in the demucs directory
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} not found.")
        return

    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
            
        real_name = folder_name
        vocals_path = os.path.join(folder_path, "vocals.wav")
        if not os.path.exists(vocals_path):
            continue
            
        print(f"Extracting pitch contour for {folder_name}...")
        
        # Load the audio
        y, sr = librosa.load(vocals_path, sr=16000, mono=True)
        
        # Extract normalized contour and valid indices
        contour, indices = extract_pitch_contour(y, sr)
        
        if len(contour) > 0:
            db[real_name] = {
                "pitches": contour.tolist(),
                "indices": indices.tolist()
            }
            print(f"Extracted {len(contour)} pitch frames.")
        else:
            print("Warning: No voiced frames found.")
            
    # Save the database
    with open(db_path, "w") as f:
        json.dump(db, f)
        
    print(f"\nSuccessfully built pitch database with {len(db)} songs!")
    print(f"Saved to {db_path}")

if __name__ == "__main__":
    build_db()
