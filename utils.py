import os
from pathlib import Path
import google.genai as genai
from PIL import Image
import subprocess

def download_image(image_filename, image_dir):
    """
    Downloads an image using curl if it doesn't already exist in the specified directory.
    """
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    image_path = Path(image_dir) / image_filename
    if image_path.exists():
        print(f"Image '{image_filename}' already exists. Skipping download.")
        return str(image_path)

    base_url = "https://assets.yadvashem.org/image/upload/t_f_low_image/f_auto/v1/remote_media/documentation4/16/12612299_03263622/"
    image_url = f"{base_url}{image_filename}"

    try:
        subprocess.run(
            ["curl", "-L", "-o", str(image_path), image_url],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Image '{image_filename}' downloaded successfully.")
        return str(image_path)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading image using curl: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def get_next_image_filename(state_file, max_images=700):
    """
    Determines the next image filename to process based on a state file.
    """
    last_processed_num = 0
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            last_processed_filename = f.read().strip()
            if last_processed_filename:
                try:
                    last_processed_num = int(last_processed_filename.split('.')[0])
                except (ValueError, IndexError):
                    pass

    next_image_num = last_processed_num + 1
    if next_image_num > max_images:
        print("All images have been processed.")
        return None

    return f"{next_image_num:05d}.JPG"

def transcribe_and_translate(image_path, output_file, state_file):
    """
    Transcribes and translates an image using the Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set the 'GEMINI_API_KEY' environment variable.")

    genai.configure(api_key=api_key)

    prompt = """
    Describe this image in detail, focusing on the main subjects and any text present.
    After the description, provide a direct translation of that description into Hebrew.
    Format the output exactly like this, without any extra formatting or markdown:
    Description: [Your detailed description here]
    Hebrew: [The Hebrew translation here]
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        img = Image.open(image_path)

        print("Sending request to Gemini API...")
        response = model.generate_content([prompt, img])

        if response.text:
            print("Received response. Saving to file.")
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"---\n")
                f.write(f"File: {os.path.basename(image_path)}\n")
                f.write(f"{response.text.strip()}\n")

            with open(state_file, "w") as f:
                f.write(os.path.basename(image_path))

            print(f"Successfully processed and saved transcription for {os.path.basename(image_path)}.")
        else:
            print("Received an empty response from the API.")

    except Exception as e:
        print(f"An error occurred during the API call: {e}")
