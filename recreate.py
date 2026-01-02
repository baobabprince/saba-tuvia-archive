import os
import requests
import concurrent.futures
from pathlib import Path
from google import genai
from google.genai import types
import argparse

# הגדרות
API_KEY = os.getenv("GEMINI_API_KEY")
IMAGES_TO_RECREATE_FILE = Path("images_to_recreate.txt")
RECREATED_TRACKER_FILE = Path("recreated_tracker.txt") # New tracker file
BASE_URL = "https://assets.yadvashem.org/image/upload/t_f_low_image/f_auto/v1/remote_media/documentation4/16/12612299_03263622/"
MODEL_ID = "gemini-3-flash-preview"
BATCH_SIZE = 20

client = genai.Client(api_key=API_KEY)

def download_worker(file_name):
    """מוריד תמונה בודדת ב-Thread נפרד ומחזיר גם את ה-URL"""
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
    parser = argparse.ArgumentParser(description="Recreate images from a list.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the script without calling the API.")
    parser.add_argument("--max-images", type=int, default=0, help="Maximum number of images to process (0 for all).")
    args = parser.parse_args()

    if not IMAGES_TO_RECREATE_FILE.exists():
        print(f"{IMAGES_TO_RECREATE_FILE} not found.")
        return

    # Read already recreated files
    if not RECREATED_TRACKER_FILE.exists(): RECREATED_TRACKER_FILE.touch()
    recreated = set(RECREATED_TRACKER_FILE.read_text(encoding="utf-8").splitlines())

    with open(IMAGES_TO_RECREATE_FILE, "r", encoding="utf-8") as f:
        all_images_to_process = [line.strip() for line in f if line.strip()]

    # Filter out already recreated images
    to_process_files = [img for img in all_images_to_process if img not in recreated]

    if args.max_images > 0:
        to_process_files = to_process_files[:args.max_images]

    if not to_process_files:
        print("No new images to recreate.")
        return

    # Process files in batches
    for i in range(0, len(to_process_files), BATCH_SIZE):
        batch_files = to_process_files[i:i + BATCH_SIZE]

        print(f"Processing batch {i//BATCH_SIZE + 1} with {len(batch_files)} images.")

        if args.dry_run:
            print("--- DRY RUN ---")
            print("Images to download:")
            for file_name in batch_files:
                print(f"- {file_name}")
            
            prompt = """Analyze the provided images. For EACH image, you MUST provide:
            1. The Original URL (provided in the text next to the image).
            2. Transcription: Transcribe the text from the image with extreme accuracy. It is crucial that the transcription is a verbatim copy of the source text, including all words, punctuation, and formatting. Do not skip any words or phrases.
            3. Translation: Fluent Hebrew translation of the transcribed text.
            
            Format the output clearly for each document."""
            print("Prompt to be used:")
            print(prompt)
            print("--- END DRY RUN ---")
            continue

        # הורדה מקבילית
        print(f"Downloading {len(batch_files)} images in parallel...")
        downloaded_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            results = list(executor.map(download_worker, batch_files))
        
        # סינון תוצאות
        downloaded_data = [res for res in results if res is not None]
        if not downloaded_data:
            print("No images were downloaded for this batch.")
            continue

        # בניית רשימת התכנים לשליחה
        api_contents = [
            """Analyze the provided images. For EACH image, you MUST provide:
            1. The Original URL (provided in the text next to the image).
            2. Transcription: Transcribe the text from the image with extreme accuracy. It is crucial that the transcription is a verbatim copy of the source text, including all words, punctuation, and formatting. Do not skip any words or phrases.
            3. Translation: Fluent Hebrew translation of the transcribed text.
            
            Format the output clearly for each document."""
        ]

        for item in downloaded_data:
            api_contents.append(f"Source URL for the following image: {item['url']}")
            api_contents.append(types.Part.from_bytes(data=item['content'], mime_type="image/jpeg"))

        try:
            print(f"Sending batch to {MODEL_ID}...")
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=api_contents
            )
            
            # שמירה
            output_dir = Path("outputs") / "recreated"
            output_dir.mkdir(exist_ok=True, parents=True)
            # Use the first image name for the batch file name
            first_image_name = downloaded_data[0]['name']
            timestamp = int(first_image_name.split('.')[0])
            output_path = output_dir / f"batch_{timestamp:05d}.txt"
            output_path.write_text(response.text, encoding="utf-8")

            # Update recreated tracker file
            with open(RECREATED_TRACKER_FILE, "a", encoding="utf-8") as f:
                for item in downloaded_data:
                    f.write(f"{item['name']}\n")
            
            print(f"Success! Output saved to {output_path}")

        except Exception as e:
            print(f"API Error: {e}")

if __name__ == "__main__":
    main()