import fitz
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf_path = r"C:\Users\carlos.jaramillo\Downloads\Soccer Analytics with Machine Learning.pdf"
doc = fitz.open(pdf_path)

print(f"Total pages: {len(doc)}")
print("\n" + "="*80)
print("EXTRACTING PAGES 1-20")
print("="*80 + "\n")

# Extract text from pages 1-20
extracted_text = {}
for page_num in range(min(20, len(doc))):
    page = doc[page_num]
    text = page.get_text()
    extracted_text[page_num + 1] = text
    print(f"Page {page_num + 1}: {len(text)} characters")

doc.close()

# Save to file for later processing
output_path = r"C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi\pdf_content_pages_1_20.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    for page_num, content in extracted_text.items():
        f.write(f"\n{'='*80}\nPAGE {page_num}\n{'='*80}\n")
        f.write(content)
        f.write("\n")

print(f"\nSaved full content to {output_path}")
print(f"Total extracted pages: {len(extracted_text)}")
