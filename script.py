import os
import google.generativeai as genai
from pathlib import Path

# הגדרות
API_KEY = os.getenv("GEMINI_API_KEY")
IMAGE_DIR = Path("images")
OUTPUT_DIR = Path("outputs")
TRACKER_FILE = Path("processed_files.txt")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-pro-preview') # מודל מהיר וחסכוני

def get_already_processed():
    if not TRACKER_FILE.exists():
        return set()
    return set(TRACKER_FILE.read_text().splitlines())

def main():
    processed = get_already_processed()
    all_images = [f for f in IMAGE_DIR.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    # סינון תמונות שטרם עובדו
    to_process = [img for img in all_images if img.name not in processed][:2]

    if not to_process:
        print("אין תמונות חדשות לעיבוד.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    for img_path in to_process:
        print(f"מעבד את: {img_path.name}...")
        
        # העלאה וקבלת תשובה
        sample_file = genai.upload_file(path=img_path)
        prompt = "Please provide a full transcription of the text in this image, followed by a translation into Hebrew."
        
        response = model.generate_content([prompt, sample_file])
        
        # שמירת הפלט
        output_file = OUTPUT_DIR / f"{img_path.stem}.txt"
        output_file.write_text(response.text, encoding="utf-8")
        
        # עדכון מעקב
        with open(TRACKER_FILE, "a") as f:
            f.write(f"{img_path.name}\n")

if __name__ == "__main__":
    main()
