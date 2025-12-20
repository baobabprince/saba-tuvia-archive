import argparse
import os
from cropper import crop_image
from utils import download_image, get_next_image_filename, transcribe_and_translate

def main():
    """
    Main function to handle command-line arguments and execute the requested action.
    """
    parser = argparse.ArgumentParser(description="An all-in-one image processing and transcription tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Crop command ---
    parser_crop = subparsers.add_parser("crop", help="Crop an image.")
    parser_crop.add_argument("input_path", help="Path to the input image.")
    parser_crop.add_argument("output_path", help="Path to save the cropped image.")
    parser_crop.add_argument("--method", default="contour", choices=['fixed', 'dark_tol', 'grayscale', 'contour'], help="Cropping method to use.")

    # --- Transcribe command ---
    parser_transcribe = subparsers.add_parser("transcribe", help="Transcribe and translate the next image.")
    parser_transcribe.add_argument("--image_dir", default="images", help="Directory to download and store images.")
    parser_transcribe.add_argument("--output_file", default="transcriptions.txt", help="File to save the transcriptions.")
    parser_transcribe.add_argument("--state_file", default=".last_processed_image", help="File to store the last processed image.")

    args = parser.parse_args()

    if args.command == "crop":
        crop_image(args.input_path, args.output_path, method=args.method)

    elif args.command == "transcribe":
        next_image_filename = get_next_image_filename(args.state_file)
        if next_image_filename:
            image_path = download_image(next_image_filename, args.image_dir)
            if image_path:
                transcribe_and_translate(image_path, args.output_file, args.state_file)
        else:
            print("No new images to transcribe.")

if __name__ == "__main__":
    main()
