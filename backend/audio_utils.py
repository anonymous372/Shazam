import os
import io
import tempfile
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
import torch
from transformers import Wav2Vec2Processor, Wav2Vec2Model

def convert_to_wav(input_path):
    """
    Converts .webm or other formats to .wav using pydub.
    Returns the path to a temporary .wav file.
    Note: Requires ffmpeg installed on the system!
    """
    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    try:
        audio = AudioSegment.from_file(input_path)
        # Convert to mono, 16kHz for standardization
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(temp_wav, format="wav")
        return temp_wav
    except Exception as e:
        print(f"Failed to convert audio (Make sure ffmpeg is installed): {e}")
        raise e

def separate_vocals(audio_path):
    """
    Uses Demucs to separate vocals from the audio track.
    Returns the path to the isolated vocal wav file.
    """
    output_dir = "data/separated"
    os.makedirs(output_dir, exist_ok=True)
    
    import subprocess
    print(f"Separating vocals for {audio_path}...")
    
    # We use demucs's pre-trained model htdemucs
    # --two-stems vocals means it will just output vocals.wav and no_vocals.wav
    cmd = [
        "demucs",
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "--out", output_dir,
        audio_path
    ]
    
    subprocess.run(cmd, check=True)
    
    # Demucs creates a folder structure: output_dir/htdemucs/filename/vocals.wav
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    vocal_path = os.path.join(output_dir, "htdemucs", base_name, "vocals.wav")
    
    return vocal_path

def chunk_audio(audio_path, chunk_duration=5, overlap=2):
    """
    Splits audio into chunks of `chunk_duration` seconds with `overlap`.
    Returns a list of numpy arrays (the audio chunks) and their start times.
    """
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    
    chunk_samples = int(chunk_duration * sr)
    hop_samples = int((chunk_duration - overlap) * sr)
    
    chunks = []
    timestamps = []
    
    for start_sample in range(0, len(y) - chunk_samples + 1, hop_samples):
        chunk = y[start_sample : start_sample + chunk_samples]
        chunks.append(chunk)
        timestamps.append(start_sample / sr)
        
    return chunks, timestamps, sr

def extract_embedding(audio_array, sr=16000):
    """
    Extracts an embedding from an audio chunk using Wav2Vec2.
    Mean-pools the sequence output to get a single 768-dimensional vector.
    """
    # Wav2Vec2 expects 16kHz audio
    inputs = processor(audio_array, sampling_rate=sr, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    # outputs.last_hidden_state shape: (batch_size, sequence_length, hidden_size)
    # We mean-pool across the sequence length to get a single vector per chunk
    hidden_states = outputs.last_hidden_state
    pooled_embedding = torch.mean(hidden_states, dim=1).squeeze().numpy()
    
    return pooled_embedding.tolist()
