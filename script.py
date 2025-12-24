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
    """מוריד תמונה בודדת ב-Thread נפרד ומחזיר גם את ה-URL"""
    file_name = f"{index:05d}.JPG"
    url = f"{BASE_URL}{file_name}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            print(f"Downloaded: {file_name}")
            return {
                "name": file_name,
                "url": url,
                "content": resp.content
            }
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")
    return None

def main():
    if not TRACKER_FILE.exists(): TRACKER_FILE.touch()
    processed = set(TRACKER_FILE.read_text(encoding="utf-8").splitlines())
    
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

    # הורדה מקבילית
    print(f"Downloading {len(to_process_indices)} images in parallel...")
    downloaded_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        results = list(executor.map(download_worker, to_process_indices))
    
    # סינון תוצאות
    downloaded_data = [res for res in results if res is not None]
    if not downloaded_data:
        print("No images were downloaded.")
        return

    # בניית רשימת התכנים לשליחה (פרומפט -> תמונה + שם/URL -> תמונה + שם/URL...)
    # 
    api_contents = [
        """Analyze the provided images. For EACH image, you MUST provide:
        1. The Original URL (provided in the text next to the image).
        2. Transcription: Exact text from the image.
        3. Translation: Fluent Hebrew translation.
        
        Format the output clearly for each document."""
    ]

    for item in downloaded_data:
        # אנחנו מצמידים לכל תמונה את ה-URL שלה כחלק מההקשר
        api_contents.append(f"Source URL for the following image: {item['url']}")
        api_contents.append(types.Part.from_bytes(data=item['content'], mime_type="image/jpeg"))

    try:
        print(f"Sending batch to {MODEL_ID}...")
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=api_contents
        )
        
        # שמירה
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        timestamp = to_process_indices[0]
        output_path = output_dir / f"batch_{timestamp:05d}.txt"
        output_path.write_text(response.text, encoding="utf-8")
        
        # עדכון מעקב
        with open(TRACKER_FILE, "a", encoding="utf-8") as f:
            for item in downloaded_data:
                f.write(f"{item['name']}\n")
        print(f"Success! Output saved to {output_path}")

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    main()
