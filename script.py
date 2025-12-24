import os
import requests
import concurrent.futures
from pathlib import Path
from google import genai
from google.genai import types

# הגדרות
API_KEY = os.getenv("GEMINI_API_KEY")
TRACKER_FILE = Path("processed_files.txt")
BASE_URL = "https://assets.yadvashem.org/image/upload/t_f_low_image/f_auto/v1/remote_media/documentation4/16/12612299_03263622/"
MODEL_ID = "gemini-3-flash-preview"
BATCH_SIZE = 4

client = genai.Client(api_key=API_KEY)

def download_worker(index):
    """מוריד תמונה בודדת ב-Thread נפרד"""
    file_name = f"{index:05d}.JPG"
    url = f"{BASE_URL}{file_name}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return (file_name, resp.content)
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")
    return None

def main():
    if not TRACKER_FILE.exists(): TRACKER_FILE.touch()
    processed = set(TRACKER_FILE.read_text().splitlines())
    
    # מציאת האינדקסים הבאים לעיבוד
    to_process_indices = []
    idx = 1
    while len(to_process_indices) < BATCH_SIZE and idx <= 700:
        name = f"{idx:05d}.JPG"
        if name not in processed:
            to_process_indices.append(idx)
        idx += 1

    if not to_process_indices:
        print("Everything is already processed.")
        return

    # הורדה מקבילית (High Speed)
    print(f"Downloading {len(to_process_indices)} images in parallel...")
    image_parts = []
    success_names = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        results = list(executor.map(download_worker, to_process_indices))
    
    for res in results:
        if res:
            name, content = res
            image_parts.append(types.Part.from_bytes(data=content, mime_type="image/jpeg"))
            success_names.append(name)

    if not image_parts: return

    # שליחה לג'מיני
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
        print(f"Sending batch to {MODEL_ID}...")
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt] + image_parts
        )
        
        # שמירה
        Path("outputs").mkdir(exist_ok=True)
        timestamp = to_process_indices[0]
        (Path("outputs") / f"batch_{timestamp:05d}.txt").write_text(response.text, encoding="utf-8")
        
        # עדכון מעקב
        with open(TRACKER_FILE, "a") as f:
            for name in success_names:
                f.write(f"{name}\n")
        print("Success!")

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    main()
