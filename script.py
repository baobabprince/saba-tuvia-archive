import os
import time
from pathlib import Path
from google import genai
from google.genai import types

# הגדרות
API_KEY = os.getenv("GEMINI_API_KEY")
IMAGE_DIR = Path("images")
OUTPUT_DIR = Path("outputs")
TRACKER_FILE = Path("processed_files.txt")
# אם 3-pro חסום לך, נסה gemini-2.0-flash או gemini-1.5-flash
MODEL_NAME = "gemini-3-flash-preview" 

client = genai.Client(api_key=API_KEY)

def get_processed_files():
    if not TRACKER_FILE.exists():
        return set()
    return set(TRACKER_FILE.read_text(encoding="utf-8").splitlines())

def main():
    processed = get_processed_files()
    all_images = sorted([f for f in IMAGE_DIR.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']])
    to_process = [img for img in all_images if img.name not in processed][:2]

    if not to_process:
        print("No new images to process.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # טעינת התמונות כרשימה
    content_parts = []
    for img_path in to_process:
        print(f"Reading {img_path.name}...")
        img_data = img_path.read_bytes()
        content_parts.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))

    prompt = """Analyze the provided image and perform the following tasks:

1. **Transcription**: Transcribe the text exactly as it appears in the image. Maintain the original line breaks and formatting. If any word is unclear, mark it with [unclear].
2. **Translation**: Translate the transcribed text into fluent and natural Hebrew. Ensure that the tone and context of the original message are preserved.

Please present the result in this format:
---
### Transcription (Original)
[The text here]

### Translation (Hebrew)
[The Hebrew translation here]
---
"""
    content_parts.append(prompt)

    try:
        print(f"Sending request to {MODEL_NAME}...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=content_parts
        )
        
        batch_id = f"result_{to_process[0].stem}.txt"
        (OUTPUT_DIR / batch_id).write_text(response.text, encoding="utf-8")
        
        with open(TRACKER_FILE, "a", encoding="utf-8") as f:
            for img in to_process:
                f.write(f"{img.name}\n")
        print("Done!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
