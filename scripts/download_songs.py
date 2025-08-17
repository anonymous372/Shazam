import os
import subprocess
import argparse

# List of some popular Kishore Kumar songs on YouTube
# You can add the full 100 songs to this list, or use a playlist URL
DEFAULT_SONGS = [
    "https://www.youtube.com/watch?v=9PdSmDRGIwM&list=RD9PdSmDRGIwM&start_radio=1", # Mere sapno ki rani
    "https://www.youtube.com/watch?v=XINI9JtypMw&list=RDXINI9JtypMw&start_radio=1", # Mere samne wali khidki
    "https://www.youtube.com/watch?v=H7Y5a7Y-jng&list=RDH7Y5a7Y-jng&start_radio=1", # Ek ajnabee haseena se
]

def download_audio(url_list, output_dir="data/raw_audio", is_playlist=False):
    """
    Downloads audio from a list of YouTube URLs using yt-dlp.
    Extracts the audio as a high-quality MP3 file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Downloading {len(url_list)} items to '{output_dir}'...")

    for i, url in enumerate(url_list):
        print(f"\n--- Downloading Item {i+1}/{len(url_list)} ---")
        print(f"URL: {url}")
        
        # yt-dlp command to extract audio as mp3
        command = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", f"{output_dir}/%(title)s.%(ext)s",
        ]
        
        if not is_playlist:
            command.append("--no-playlist")
            
        command.append(url)

        try:
            subprocess.run(command, check=True)
            print(f"Successfully downloaded: {url}")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading {url}: {e}")
        except FileNotFoundError:
            print("Error: 'yt-dlp' is not installed or not in PATH.")
            print("Please install it using: pip install yt-dlp")
            break

    print("\nDownload process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Kishore Kumar songs from YouTube")
    parser.add_argument("--playlist", type=str, help="YouTube playlist URL containing the songs")
    parser.add_argument("--output", type=str, default="data/raw_audio", help="Output directory for audio files")
    
    args = parser.parse_args()

    if args.playlist:
        print(f"Downloading playlist: {args.playlist}")
        # When given a playlist URL, yt-dlp will automatically download all videos in it
        download_audio([args.playlist], args.output, is_playlist=True)
    else:
        print("No playlist provided. Downloading default sample list of 5 songs.")
        download_audio(DEFAULT_SONGS, args.output)
