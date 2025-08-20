# Shazam

A song identification app that works by humming. You hum a melody into your mic, and it figures out which Kishore Kumar song you're trying to recall. No lyrics needed — just the tune.

Built this because I kept forgetting the names of old Hindi songs and couldn't exactly Google-search a melody stuck in my head.

---

## How it works

The pipeline has two phases — building the database, and then querying it.

**Building the database:**
1. Songs are downloaded from YouTube using `yt-dlp`
2. [Demucs](https://github.com/facebookresearch/demucs) (`htdemucs` model) strips out everything except the vocals — no drums, no instruments
3. The vocal track goes through `pYIN` (via librosa) to extract a pitch contour — essentially a sequence of MIDI note values over time
4. These contours are saved to `data/pitch_db.json`

**Identifying a hum:**
1. You record yourself humming into the browser mic
2. The audio is sent to the FastAPI backend
3. Your hum gets the same pYIN treatment — HPSS to isolate harmonics, then pitch extraction, then smoothing
4. **Subsequence DTW** (Dynamic Time Warping) slides your short hum across each song's full pitch contour to find the best-matching window
5. The match is key-invariant (centered to remove absolute pitch) and tempo-flexible (DTW allows 2x speed variance)
6. Top 3 matches are returned with confidence scores and timestamps

---

## Project structure

```
Shazam/
├── backend/
│   ├── main.py              # FastAPI server — /api/identify and /api/songs endpoints
│   ├── audio_utils.py       # Audio conversion, vocal separation, chunking
│   ├── pitch_utils.py       # pYIN pitch extraction + subsequence DTW matching
│   ├── build_pitch_db.py    # Script to build pitch_db.json from separated vocals
│   ├── ingestion_script.py  # Downloads songs via yt-dlp and runs Demucs
│   └── vector_store.py      # (Experimental) Wav2Vec2 embedding approach
├── web/                     # Next.js frontend
│   └── src/
│       ├── app/page.tsx     # Main UI
│       └── components/
│           ├── MicRecorder.tsx         # Mic access, recording, API call
│           └── WaveformVisualizer.tsx  # Animated waveform while recording
├── scripts/
│   └── download_songs.py    # Utility to batch-download songs
├── data/                    # Not committed — lives locally
│   ├── raw_audio/           # Downloaded .webm files
│   ├── separated/           # Demucs output (vocals.wav per song)
│   └── pitch_db.json        # The pitch database the server loads at startup
└── requirements.txt
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- `ffmpeg` installed and on your PATH (required by pydub for audio conversion)

### Backend

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server (from the project root)
uvicorn backend.main:app --reload --port 8000
```

The server will try to load `data/pitch_db.json` at startup. If that file doesn't exist yet, it'll start with an empty database (see the section below on building the database).

### Frontend

```bash
cd web
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

---

## Building the song database

This is the offline step you run once (or whenever you add new songs).

**Step 1 — Add songs**

Put your audio files inside `data/raw_audio/`. The ingestion script can also download them from YouTube:

```bash
python backend/ingestion_script.py
```

This runs `yt-dlp` to grab songs and then Demucs to separate the vocals. Demucs takes a few minutes per song — it's doing real ML inference.

**Step 2 — Build the pitch database**

```bash
python -m backend.build_pitch_db
```

This processes every folder inside `data/separated/htdemucs/`, extracts pitch contours from `vocals.wav`, and writes the final `data/pitch_db.json`. Restart the backend after this.

---

## Using the app

1. Make sure both the backend (`localhost:8000`) and frontend (`localhost:3000`) are running
2. Open the browser and hit the record button
3. Hum the melody of a Kishore Kumar song for a few seconds — 5–10 seconds works well
4. Hit stop, and it'll send the audio to the backend
5. Results show the song name, a confidence score, and the timestamp in the song where your hum matched

The songs currently in the database are shown at the bottom of the page as tags.

---

## Notes

- Works best when you hum clearly without too much background noise
- The matching is pitch-relative, so it doesn't matter if you hum in a different key — it still works
- It can handle humming 2x faster or slower than the original song tempo
- If confidence is below 10%, it returns "No match found" rather than a wrong guess
- The `vector_store.py` file is an older experimental approach using Wav2Vec2 embeddings — not used in the current pipeline

