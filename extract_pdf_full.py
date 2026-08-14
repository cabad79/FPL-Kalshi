import fitz
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf_path = r"C:\Users\carlos.jaramillo\Downloads\Soccer Analytics with Machine Learning.pdf"
doc = fitz.open(pdf_path)

print(f"Total pages: {len(doc)}")

# Extract pages 21-80
extracted_text = {}
for page_num in range(20, min(80, len(doc))):
    page = doc[page_num]
    text = page.get_text()
    extracted_text[page_num + 1] = text
    print(f"Extracted page {page_num + 1}: {len(text)} characters")

doc.close()

# Save to file
output_path = r"C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi\pdf_content_pages_21_80.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    for page_num in sorted(extracted_text.keys()):
        f.write(f"\n{'='*80}\nPAGE {page_num}\n{'='*80}\n")
        f.write(extracted_text[page_num])
        f.write("\n")

print(f"\nSaved to {output_path}")
