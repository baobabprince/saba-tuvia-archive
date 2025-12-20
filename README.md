# All-in-One Image Processing and Transcription Tool

This project provides a versatile command-line tool for image cropping, transcription, and translation. It includes multiple cropping methods and leverages the Gemini API for transcription and translation tasks.

## Features

- **Multiple Cropping Methods**: Choose from four different cropping techniques:
  - `fixed`: Crops a fixed number of pixels.
  - `dark_tol`: Crops based on a dark tolerance threshold.
  - `grayscale`: Crops based on non-zero pixels in a grayscale version of the image.
  - `contour`: Crops by finding the contours of the main object in the image.
- **Automated Transcription and Translation**: Transcribe images and translate the descriptions into Hebrew using the Gemini API.
- **Command-Line Interface**: A user-friendly CLI for easy operation.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/your-repository.git
   cd your-repository
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Key**:
   For transcription and translation, you need to set up your Gemini API key as an environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```

## Usage

### Cropping

To crop an image, use the `crop` command with the specified input path, output path, and cropping method.

```bash
python main.py crop <input_path> <output_path> --method <method_name>
```

- `<input_path>`: The path to the image you want to crop.
- `<output_path>`: The path to save the cropped image.
- `--method`: The cropping method to use (`fixed`, `dark_tol`, `grayscale`, `contour`).

**Example**:
```bash
python main.py crop images/00001.JPG output/cropped_00001.JPG --method contour
```

### Transcription and Translation

To transcribe and translate the next available image, use the `transcribe` command. The tool automatically downloads the image, processes it, and saves the output.

```bash
python main.py transcribe
```

You can also specify the image directory, output file, and state file:

```bash
python main.py transcribe --image_dir <image_directory> --output_file <output_filename> --state_file <state_filename>
```

- `--image_dir`: The directory to download and store images (default: `images`).
- `--output_file`: The file to save transcriptions (default: `transcriptions.txt`).
- `--state_file`: The file to store the last processed image (default: `.last_processed_image`).

## Dependencies

- `google-generativeai`
- `Pillow`
- `requests`
- `numpy`
- `opencv-python`
