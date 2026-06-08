import pytesseract
from PIL import Image
import os

def extract_text_from_image(image_path: str) -> str:
    """
    Extracts raw text from an uploaded prescription image.
    In production, this would use a cloud OCR like AWS Textract or robust local EasyOCR.
    """
    try:
        # Open image
        img = Image.open(image_path)
        
        # Extract text
        text = pytesseract.image_to_string(img)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("Tesseract not found! Falling back to mock OCR for demonstration.")
        # Fallback if the user hasn't installed Tesseract binaries on Windows
        return "Dr. Smith\nRx: Amlodpn 10mg taken at 08:30 AM"
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""
