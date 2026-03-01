import os
import json
import time
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

CACHE_DIR = Path("Saved/SystemCache")
VOICE_CACHE_DIR = CACHE_DIR / "Voice"
DIRECTIVE_CACHE_FILE = CACHE_DIR / "directives_cache.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class SystemAIVoiceBridge:
    def __init__(self):
        self.directive_cache = self._load_directive_cache()

    def _load_directive_cache(self):
        if DIRECTIVE_CACHE_FILE.exists():
            try:
                with open(DIRECTIVE_CACHE_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_directive_cache(self):
        with open(DIRECTIVE_CACHE_FILE, "w") as f:
            json.dump(self.directive_cache, f, indent=2)

    def generate_directive(self, context_tag, prompt_override=None):
        """Generate a directive using Mistral AI."""
        if not MISTRAL_API_KEY:
            return {"status": "error", "message": "No Mistral API Key"}

        prompt = prompt_override or f"Generate a short, cryptic, and authoritative system directive for a player in a sci-fi/gothic world. Context: {context_tag}. Max 15 words."
        
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-tiny",
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=10
            )
            if response.status_code != 200:
                return {"status": "error", "message": f"Mistral API error {response.status_code}: {response.text}"}

            data = response.json()
            if "choices" not in data or not data["choices"]:
                return {"status": "error", "message": f"Unexpected Mistral response: {json.dumps(data)}"}
                
            text = data["choices"][0]["message"]["content"].strip()
            
            directive = {
                "DirectiveId": hashlib.md5(text.encode()).hexdigest()[:8],
                "Text": text,
                "ContextTag": context_tag,
                "TimestampUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            # Update cache
            self.directive_cache[context_tag] = directive
            self._save_directive_cache()
            
            return {"status": "success", "directive": directive}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_voice(self, text):
        """Generate voice using ElevenLabs."""
        if not ELEVENLABS_API_KEY:
            return {"status": "error", "message": "No ElevenLabs API Key"}

        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_path = VOICE_CACHE_DIR / f"{text_hash}.mp3"

        if cache_path.exists():
            return {"status": "success", "file_path": str(cache_path.absolute()), "cached": True}

        try:
            # Voice ID for "System" (using a cold, authoritative voice)
            voice_id = "onwK4e9ZLuTAKqWW03F9" # 'Daniel' or similar
            
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.75,
                        "similarity_boost": 0.75
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                with open(cache_path, "wb") as f:
                    f.write(response.content)
                return {"status": "success", "file_path": str(cache_path.absolute()), "cached": False}
            else:
                return {"status": "error", "message": f"ElevenLabs error: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["directive", "voice", "both"], required=True)
    parser.add_argument("--context", default="General")
    parser.add_argument("--text", default="")
    args = parser.parse_args()

    bridge = SystemAIVoiceBridge()
    if args.action == "directive":
        print(json.dumps(bridge.generate_directive(args.context)))
    elif args.action == "voice":
        print(json.dumps(bridge.generate_voice(args.text)))
    elif args.action == "both":
        res = bridge.generate_directive(args.context)
        if res["status"] == "success":
            voice_res = bridge.generate_voice(res["directive"]["Text"])
            res["voice"] = voice_res
        print(json.dumps(res))
