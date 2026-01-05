
import os
import csv

def parse_line_by_line(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    all_data = []
    current_data = {}
    in_transcription = False
    in_translation = False

    for line in lines:
        line = line.strip()

        if line.startswith('---'):
            if current_data:
                all_data.append(current_data)
            current_data = {}
            in_transcription = False
            in_translation = False
            continue

        if "Original URL" in line:
            try:
                url = line.split('[', 1)[1].split(']', 1)[0]
                current_data['image_url'] = url
            except IndexError:
                pass 
            in_transcription = False
            in_translation = False

        elif "Transcription" in line:
            in_transcription = True
            in_translation = False
            current_data.setdefault('transcription', '')
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    content_after_header = parts[1].strip()
                    if content_after_header:
                        current_data['transcription'] += content_after_header


        elif "Translation" in line:
            in_translation = True
            in_transcription = False
            current_data.setdefault('translation', '')
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    content_after_header = parts[1].strip()
                    if content_after_header:
                        current_data['translation'] += content_after_header

        elif in_transcription:
            current_data['transcription'] += ' ' + line
        
        elif in_translation:
            current_data['translation'] += ' ' + line

    if current_data:
        all_data.append(current_data)

    for item in all_data:
        if 'transcription' in item:
            item['transcription'] = item['transcription'].strip()
        if 'translation' in item:
            item['translation'] = item['translation'].strip()

    return all_data


def main():
    output_dir = 'outputs'
    all_extracted_data = []
    for filename in os.listdir(output_dir):
        if filename.startswith('batch_') and filename.endswith('.txt'):
            file_path = os.path.join(output_dir, filename)
            all_extracted_data.extend(parse_line_by_line(file_path))

    with open('consolidated_output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['image_url', 'transcription', 'translation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_extracted_data)

if __name__ == '__main__':
    main()
