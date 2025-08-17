import os
import hashlib
from backend.audio_utils import chunk_audio, extract_embedding
from backend.vector_store import get_index, upsert_vectors

mapping = {
    "tmpo6hutga_": "Main Shayar To Nahin 4K Song ｜ मैं शायर तो नहीं ｜ Bobby ｜ Shailendra Singh ｜ Romantic Gaane Hindi.webm",
    "tmpl1az25a7": "Yeh Sham Mastani ｜ Timeless 70s Classic with lyrics ｜ Kishore Kumar ｜ Rajesh Khanna ｜ Hindi Song.webm",
    "tmpwxclkgr8": "Pyar Deewana Hota Hai 4K Song ： Kishore Kumar Classics ｜ Rajesh Khanna ｜ Hindi Romantic-Kati Patang.webm",
    "tmphtzqxe1q": "Mere Mehboob Qayamat Hogi  (Original) - Mr. X In Bombay - Kishore Kumar's Greatest Hits - Old Songs.webm",
    "tmpzlqgjygx": "Kehdoon Tumhen Ya Chup Rahun 4K ｜ Deewaar (1975) ｜ Shashi Kapoor, Neetu Singh ｜ Popular Hindi Song.webm",
    "tmpyphpxrtl": "Mere Sapno Ki Rani 4K Song ： मेरे सपनो की रानी ｜ आराधना ｜ राजेश खन्ना - शर्मिला टैगोर - किशोर कुमार.webm",
    "tmp16_pyh9p": "Mere Samne Wali Khidki Mein - Padosan - Saira Banu, Sunil Dutt & Kishore Kumar - Old Hindi Songs.webm",
    "tmpcu1q8lu9": "Kya Khoob Lagti Ho with lyrics｜ क्या खूब लगती हो गाने ｜ Dharmatma ｜ Hema Malini ｜ Feroz Khan.webm",
    "tmphmv_cy8_": "Kora Kagaz Tha Yeh Man Mera 4K Video Song ｜ Lata Mangeshkar｜ Kishore Kumar ｜ Aradhana｜ Rajesh Khanna.webm",
    "tmpu62m0sn_": "Dekha Ek Khwab Song ｜ Silsila ｜ Amitabh Bachchan, Rekha ｜ Kishore Kumar, Lata Mangeshkar, Shiv-Hari.webm"
}

def fix_failed_vectors():
    index = get_index()
    base_dir = "data/separated/htdemucs"
    
    for tmp_name, real_name in mapping.items():
        vocal_path = os.path.join(base_dir, tmp_name, "vocals.wav")
        
        # Two songs successfully uploaded, but let's re-upload them to fix their IDs just in case, 
        # actually no, if they uploaded successfully, their IDs were ASCII safe.
        # But wait! We'll just run it for all existing vocals.wav.
        
        if os.path.exists(vocal_path):
            print(f"Fixing {real_name}...")
            chunks, timestamps, sr = chunk_audio(vocal_path, chunk_duration=5, overlap=2)
            
            vectors = []
            safe_hash = hashlib.md5(real_name.encode('utf-8')).hexdigest()
            for i, (chunk, start_time) in enumerate(zip(chunks, timestamps)): 
                embedding = extract_embedding(chunk, sr)
                chunk_id = f"{safe_hash}_chunk_{i}"
                vectors.append({
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": {
                        "song": real_name,
                        "start_time": float(start_time),
                        "end_time": float(start_time + 5.0)
                    }
                })
                
            print(f"Upserting {len(vectors)} chunks for {real_name}...")
            upsert_vectors(index, vectors)
            print("Done!")
            
            # Now we can safely rename the folder as requested by the user
            new_folder_path = os.path.join(base_dir, safe_hash) # Rename to hash to avoid unicode issues on Mac
            os.rename(os.path.join(base_dir, tmp_name), new_folder_path)
            print(f"Renamed {tmp_name} to {safe_hash} (Hash of original name)")

if __name__ == "__main__":
    fix_failed_vectors()
