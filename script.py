import os
import requests
import concurrent.futures
from pathlib import Path
from google import genai
from google.genai import types
import argparse

# הגדרות
API_KEY = os.getenv("GEMINI_API_KEY")
TRACKER_FILE = Path("processed_files.txt")
BASE_URL = "https://assets.yadvashem.org/image/upload/t_f_low_image/f_auto/v1/remote_media/documentation4/16/12612299_03263622/"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
BATCH_SIZE = 5

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
    parser = argparse.ArgumentParser(description="Download and process Yad Vashem document images.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="The Gemini model ID to use.")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Number of images to process in this batch.")
    args = parser.parse_args()

    model_id = args.model
    batch_size = args.batch_size

    if not API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    client = genai.Client(api_key=API_KEY)

    if not TRACKER_FILE.exists(): TRACKER_FILE.touch()
    processed = set(TRACKER_FILE.read_text(encoding="utf-8").splitlines())
    
    to_process_indices = []
    idx = 1
    while len(to_process_indices) < batch_size and idx <= 700:
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        results = list(executor.map(download_worker, to_process_indices))
    
    # סינון תוצאות
    downloaded_data = [res for res in results if res is not None]
    if not downloaded_data:
        print("No images were downloaded.")
        return

    # בניית רשימת התכנים לשליחה (פרומפט -> תמונה + שם/URL -> תמונה + שם/URL...)
    api_contents = [
        """Analyze the provided images. For EACH image, you MUST provide:
        1. The Original URL (provided in the text next to the image).
        2. Transcription: Transcribe the text from the image with extreme accuracy. It is crucial that the transcription is a verbatim copy of the source text, including all words, punctuation, and formatting. Do not skip any words or phrases.
        3. Translation: Fluent Hebrew translation of the transcribed text.
        
        Format the output clearly for each document."""
    ]

    for item in downloaded_data:
        # אנחנו מצמידים לכל תמונה את ה-URL שלה כחלק מההקשר
        api_contents.append(f"Source URL for the following image: {item['url']}")
        api_contents.append(types.Part.from_bytes(data=item['content'], mime_type="image/jpeg"))

    try:
        print(f"Sending batch to {model_id}...")
        response = client.models.generate_content(
            model=model_id,
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
