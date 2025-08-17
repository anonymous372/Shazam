import numpy as np
import librosa
import pandas as pd
from scipy.spatial.distance import euclidean
from scipy.ndimage import median_filter, uniform_filter1d

def extract_pitch_contour(y, sr):
    """
    Extracts a key-invariant pitch contour from an audio signal using pYIN.
    """
    # Reject audio that is too quiet (background noise/silence)
    rms = librosa.feature.rms(y=y)[0]
    if np.mean(rms) < 0.005: # Threshold for pure silence/hiss
        return np.array([])

    # NEW: Harmonic-Percussive Source Separation (HPSS)
    # This strips away residual drum hits (transients) that bled through htdemucs,
    # ensuring pYIN only processes pure harmonic tones.
    y_harmonic, _ = librosa.effects.hpss(y)
    
    # Extract fundamental frequency (F0) using pYIN on the harmonic signal
    # UPGRADE: We raised the minimum frequency from C2 (65 Hz) to A2 (110 Hz).
    # This acts as an aggressive brick-wall filter against basslines and kick drums
    # that bleed into the separated vocal track!
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y_harmonic, 
        sr=sr, 
        fmin=librosa.note_to_hz('A2'), 
        fmax=librosa.note_to_hz('C7'),
        frame_length=2048
    )
    
    # Convert Hz to MIDI notes (leaves NaNs intact)
    midi_notes = librosa.hz_to_midi(f0)
    
    # -------------------------------------------------------------
    # THE SPATIO-TEMPORAL FIX: DO NOT DELETE NaNs!
    # Deleting NaNs squishes the arrays and destroys the time axis.
    # Instead, we use linear interpolation to bridge the silences 
    # with a continuous slope, preserving rhythm and preventing DTW abuse.
    # -------------------------------------------------------------
    
    # Convert to pandas Series for easy interpolation
    series = pd.Series(midi_notes)
    
    # Interpolate linearly. limit_direction='both' ensures that leading
    # or trailing NaNs (silence at the very start/end) are flatlined to the nearest note.
    interpolated_series = series.interpolate(method='linear', limit_direction='both')
    
    # Convert back to numpy array
    midi_notes_interpolated = interpolated_series.to_numpy()
    
    # In extremely rare cases where the ENTIRE audio is silence, it might still have NaNs
    if np.isnan(midi_notes_interpolated).all():
        return np.array([]), np.array([])

    # Apply a median filter to remove sudden sharp octave jumps or tracking errors
    # Kernel size 11 (approx 0.3 seconds) smooths out micro-glitches
    smoothed_contour = median_filter(midi_notes_interpolated, size=11)
    
    # Since we didn't delete any frames, the valid indices are just the entire range
    valid_indices = np.arange(len(smoothed_contour))
    
    return smoothed_contour, valid_indices

def compare_contours(query_contour, target_contour):
    """
    Uses Subsequence Dynamic Time Warping (DTW) to compare a short query
    against a long target contour.
    Returns the normalized distance (lower is better).
    """
    # Need at least 20 frames for a meaningful match
    if len(query_contour) < 20 or len(target_contour) < 20:
        return float('inf'), 0
        
    # MATHEMATICAL PERFECTION: Shift-Invariant Subsequence DTW
    # Center the query globally to 0.
    query_centered = query_contour - np.mean(query_contour)
    
    # Center the target LOCALLY using a moving average exactly the length of the query
    # This prevents the baseline from shifting across massive 4-minute tracks!
    window_size = len(query_contour)
    target_centered = target_contour - uniform_filter1d(target_contour, size=window_size)
        
    # librosa.sequence.dtw expects feature matrices of shape (d, t)
    X = query_centered.reshape(1, -1)
    Y = target_centered.reshape(1, -1)
    
    # STRICT TIME-WARPING CONSTRAINTS (Type III Local Continuity)
    # By default, DTW can stretch a single note infinitely to match a random 4-minute song.
    # step_sizes = [[1, 1], [1, 2], [2, 1]] physically forces the algorithm to move forward in time.
    # You can only hum up to 2x faster or 2x slower than the original song. 
    # It absolutely CANNOT infinitely stretch random notes anymore!
    step_sizes = np.array([[1, 1], [1, 2], [2, 1]])
    weights_mul = np.array([1.0, 1.5, 1.5]) # Add a 50% penalty for stretching/compressing
    
    # Run subsequence DTW
    D, wp = librosa.sequence.dtw(
        X, Y, 
        subseq=True, 
        metric='euclidean',
        step_sizes_sigma=step_sizes,
        weights_mul=weights_mul
    )
    
    # wp[0] is the end of the optimal path (n, m). 
    # wp[0, 1] is the ending index in the target sequence Y.
    # The total accumulated cost of the best path is stored in D[-1, wp[0,1]]
    total_cost = D[-1, wp[0, 1]]
    
    # Target start index is at the beginning of the path (which is the last element of wp because wp is returned backwards)
    target_start_index = wp[-1, 1]
    
    # Normalize by path length so it's a fair average distance per frame
    normalized_distance = total_cost / wp.shape[0]
    
    return float(normalized_distance), int(target_start_index)
