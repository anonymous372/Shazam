import os
import glob
from backend.audio_utils import convert_to_wav, separate_vocals, chunk_audio, extract_embedding
from backend.vector_store import get_index, upsert_vectors

def process_and_ingest(raw_dir="data/raw_audio"):
    """
    1. Finds all audio files in raw_dir
    2. Converts to WAV if needed
    3. Separates vocals using Demucs
    4. Chunks the vocal track
    5. Extracts embeddings
    6. Upserts to Pinecone
    """
    index = get_index()
    
    # Find all webm/mp3/wav files
    audio_files = []
    for ext in ("*.webm", "*.mp3", "*.wav", "*.m4a"):
        audio_files.extend(glob.glob(os.path.join(raw_dir, ext)))
        
    print(f"Found {len(audio_files)} audio files for ingestion.")
    
    for audio_file in audio_files:
        song_name = os.path.basename(audio_file)
        print(f"\nProcessing {song_name}...")
        
        try:
            # 1. Convert to WAV (Standardization)
            wav_path = convert_to_wav(audio_file)
            
            # 2. Isolate Vocals
            vocal_path = separate_vocals(wav_path)
            
            # 3. Chunk Audio (5 seconds, 2 seconds overlap)
            chunks, timestamps, sr = chunk_audio(vocal_path, chunk_duration=5, overlap=2)
            
            # 4. Extract Embeddings & Prepare for Pinecone
            vectors = []
            for i, (chunk, start_time) in enumerate(zip(chunks, timestamps)): 
                embedding = extract_embedding(chunk, sr)
                
                import hashlib
                safe_hash = hashlib.md5(song_name.encode('utf-8')).hexdigest()
                # Create a unique, ASCII-safe ID for this chunk
                chunk_id = f"{safe_hash}_chunk_{i}"
                
                vectors.append({
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": {
                        "song": song_name,
                        "start_time": float(start_time),
                        "end_time": float(start_time + 5.0)
                    }
                })
            
            # 5. Upsert to Pinecone
            print(f"Extracted {len(vectors)} chunks. Upserting...")
            upsert_vectors(index, vectors)
            print(f"Successfully processed {song_name}")
                
        except Exception as e:
            print(f"Failed to process {song_name}: {e}")

if __name__ == "__main__":
    process_and_ingest()
