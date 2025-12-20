from PIL import Image
import numpy as np
import cv2
import os

def crop_image(input_path, output_path, method='bbox', **kwargs):
    """
    Crops an image using various methods.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return

    img = Image.open(input_path)

    if method == 'fixed':
        width, height = img.size
        is_landscape = width > height
        crop_amount = kwargs.get('crop_amount', (1661, 1580))
        if is_landscape:
            img = img.crop((0, 0, width, height - crop_amount[0]))
        else:
            img = img.crop((0, 0, width, height - crop_amount[1]))
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

    elif method == 'dark_tol':
        image_np = np.array(img)
        mask = np.any(image_np > kwargs.get('upper_threshold', 50), axis=-1)
        coords = np.argwhere(mask)
        if coords.size > 0:
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0) + 1
            img = Image.fromarray(image_np[y0:y1, x0:x1])
        else:
            print("No object found to crop.")
            return

    elif method == 'grayscale':
        img_gray = img.convert('L')
        img_array = np.array(img_gray)
        non_zero = img_array > 0
        rows = np.any(non_zero, axis=1)
        cols = np.any(non_zero, axis=0)
        if np.where(rows)[0].size > 0 and np.where(cols)[0].size > 0:
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            img = img.crop((cmin, rmin, cmax + 1, rmax + 1))
        else:
            print("No object found to crop.")
            return

    elif method == 'contour':
        image_cv = cv2.imread(input_path)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
            cropped_image_cv = image_cv[y:y+h, x:x+w]
            cv2.imwrite(output_path, cropped_image_cv)
            print(f"Image cropped successfully and saved to {output_path}")
        else:
            print("No object found to crop.")
        return

    else:
        print(f"Error: Unknown cropping method '{method}'")
        return

    quality = kwargs.get('quality', 70)
    img.save(output_path, quality=quality, optimize=True)
    print(f"Image cropped successfully and saved to {output_path}")

def main():
    """
    Main function to demonstrate the cropping methods.
    """
    input_dir = 'images'
    output_dir = 'output'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    test_images = {
        'fixed': 'images/00001.JPG',
        'dark_tol': 'images/00003.JPG',
        'grayscale': 'images/00001.JPG',
        'contour': 'images/00001.JPG'
    }

    for method, img_path in test_images.items():
        if os.path.exists(img_path):
            output_path = os.path.join(output_dir, f'cropped_{method}_{os.path.basename(img_path)}')
            print(f"\n--- Testing method: {method} ---")
            crop_image(img_path, output_path, method=method)
        else:
            print(f"Warning: Test image not found at {img_path}")

if __name__ == '__main__':
    main()
