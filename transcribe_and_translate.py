import os
from pathlib import Path
import google.generativeai as genai
from PIL import Image

# --- Configuration ---
IMAGE_DIR = "images"
STATE_FILE = ".last_processed_image"
OUTPUT_FILE = "transcriptions.txt"
API_KEY_ENV_VAR = "GEMINI_API_KEY"
MODEL_NAME = "gemini-1.5-pro"
PROMPT = """
Describe this image in detail, focusing on the main subjects and any text present.
After the description, provide a direct translation of that description into Hebrew.
Format the output exactly like this, without any extra formatting or markdown:
Description: [Your detailed description here]
Hebrew: [The Hebrew translation here]
"""

def get_next_image():
    """
    Determines the next image to process based on a state file.
    """
    try:
        image_files = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if not image_files:
            print("No images found in the 'images' directory.")
            return None

        last_processed = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                last_processed = f.read().strip()

        if not last_processed:
            # If state file is empty or doesn't exist, start with the first image
            return image_files[0]

        try:
            last_index = image_files.index(last_processed)
            if last_index + 1 < len(image_files):
                return image_files[last_index + 1]
            else:
                print("All images have been processed.")
                return None
        except ValueError:
            # The file in the state file wasn't found in the directory, start from the beginning
            print(f"Warning: State file contains an image not found in the directory ('{last_processed}'). Starting from the first image.")
            return image_files[0]

    except FileNotFoundError:
        print(f"Error: The directory '{IMAGE_DIR}' was not found.")
        return None

def main():
    """
    Main function to run the transcription and translation process.
    """
    # 1. Get API Key and configure the model
    api_key = os.getenv(API_KEY_ENV_VAR)
    if not api_key:
        raise ValueError(f"API key not found. Please set the '{API_KEY_ENV_VAR}' environment variable.")
    genai.configure(api_key=api_key)

    # 2. Determine the next image to process
    next_image_filename = get_next_image()
    if not next_image_filename:
        return  # Exit if no new image to process

    print(f"Processing image: {next_image_filename}")
    image_path = Path(IMAGE_DIR) / next_image_filename

    # 3. Call the Gemini API
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        img = Image.open(image_path)
        
        print("Sending request to Gemini API...")
        response = model.generate_content([PROMPT, img])
        
        # 4. Process the response and save it
        if response.text:
            print("Received response. Saving to file.")
            # Append the result to the output file
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"---\n")
                f.write(f"File: {next_image_filename}\n")
                f.write(f"{response.text.strip()}\n")
            
            # Update the state file with the image we just processed
            with open(STATE_FILE, "w") as f:
                f.write(next_image_filename)
            
            print(f"Successfully processed and saved transcription for {next_image_filename}.")
        else:
            print("Received an empty response from the API.")

    except Exception as e:
        print(f"An error occurred during the API call: {e}")
        # Do not update the state file, so we can retry this image on the next run


if __name__ == "__main__":
    main()
