import easyocr
import re

# initialize OCR reader once
reader = easyocr.Reader(['en'], gpu=False)

def extract_text(image_path):
    """
    Extract text from image using EasyOCR
    """
    result = reader.readtext(image_path, detail=0)
    text = " ".join(result)
    return text


def parse_fields(text):
    """
    Extract amount + date from extracted text
    """
    amount = None
    date = None

    # Extract amount: supports ₹450.00 or 450.00
    amt_match = re.search(r'(\d+\.\d{2})', text)
    if amt_match:
        amount = amt_match.group(1)

    # Extract date: YYYY-MM-DD
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if date_match:
        date = date_match.group(1)

    return amount, date
