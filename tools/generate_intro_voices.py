import os
import json
import requests
import hashlib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_CACHE_DIR = Path("Saved/SystemCache/Voice")
VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

VOICE_ID = "onwK4e9ZLuTAKqWW03F9" # Cold, authoritative voice

INTRO_SCRIPTS = [
    {
        "label": "system_awakening",
        "text": "Citadel Zero-One status: Active. Neural link established. Awaiting Signal-bound unit for immediate deployment."
    },
    {
        "label": "world_intro",
        "text": "Welcome to the Iron-catacombs. A world governed by the System, where every action is monitored, and every failure is logged."
    },
    {
        "label": "gameplay_directive",
        "text": "Directive Alpha-Nine: Initiate descent. Purge the catacombs of unauthorized entities. Compliance is mandatory."
    }
]

def generate_voice(text, label):
    if not ELEVENLABS_API_KEY:
        print(f"Error: ELEVENLABS_API_KEY not found in .env")
        return

    # Using the same hash logic as the bridge to ensure consistency
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_path = VOICE_CACHE_DIR / f"{label}.mp3"
    
    print(f"Generating voice for: {label}...")
    
    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.8,
                    "similarity_boost": 0.8
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            with open(cache_path, "wb") as f:
                f.write(response.content)
            print(f"  SUCCESS: Saved to {cache_path}")
        else:
            print(f"  FAILED: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"  ERROR: {str(e)}")

if __name__ == "__main__":
    for script in INTRO_SCRIPTS:
        generate_voice(script["text"], script["label"])
