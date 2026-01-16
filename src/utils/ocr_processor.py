"""
OCR Processing Utility for Daily Automated Intelligence Platform (DAIP)
Extracts text from images using Tesseract OCR
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys
from PIL import Image
import pytesseract
import numpy as np
import cv2

from src.logger import setup_logger

logger = setup_logger("daip.ocr")


class OCRProcessor:
    """OCR processor for extracting text from images"""

    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR processor

        Args:
            tesseract_path: Path to Tesseract executable (Windows only)
        """
        # Set Tesseract path for Windows
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif sys.platform == "win32":
            # Default Windows installation path
            default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if Path(default_path).exists():
                pytesseract.pytesseract.tesseract_cmd = default_path
                logger.info(f"Using Tesseract at: {default_path}")
            else:
                logger.warning("Tesseract not found at default Windows path")

        logger.info("OCR Processor initialized")

    def preprocess_image(self, image: Image.Image, enhance: bool = True) -> Image.Image:
        """
        Preprocess image for better OCR results

        Args:
            image: PIL Image object
            enhance: Apply image enhancement

        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to numpy array
            img_array = np.array(image)

            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            if enhance:
                # Apply adaptive thresholding
                img_array = cv2.adaptiveThreshold(
                    img_array,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2
                )

                # Denoise
                img_array = cv2.fastNlMeansDenoising(img_array)

            # Convert back to PIL Image
            return Image.fromarray(img_array)

        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return image

    def extract_text(
        self,
        image_path: str,
        lang: str = 'kor+eng',
        preprocess: bool = True
    ) -> str:
        """
        Extract text from image

        Args:
            image_path: Path to image file
            lang: Language for OCR (kor, eng, jpn, chi_sim, etc.)
            preprocess: Apply preprocessing

        Returns:
            Extracted text
        """
        try:
            logger.info(f"Extracting text from: {image_path}")

            # Load image
            image = Image.open(image_path)

            # Preprocess if requested
            if preprocess:
                image = self.preprocess_image(image)

            # Extract text
            text = pytesseract.image_to_string(image, lang=lang)

            logger.info(f"Extracted {len(text)} characters")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""

    def extract_data(
        self,
        image_path: str,
        lang: str = 'kor+eng'
    ) -> Dict[str, Any]:
        """
        Extract structured data from image

        Args:
            image_path: Path to image file
            lang: Language for OCR

        Returns:
            Dictionary with text, confidence, and bounding boxes
        """
        try:
            logger.info(f"Extracting data from: {image_path}")

            # Load image
            image = Image.open(image_path)

            # Extract data
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                output_type=pytesseract.Output.DICT
            )

            # Filter out empty text
            filtered_data = {
                'text': [],
                'confidence': [],
                'bbox': []
            }

            for i, text in enumerate(data['text']):
                if text.strip():
                    filtered_data['text'].append(text)
                    filtered_data['confidence'].append(data['conf'][i])
                    filtered_data['bbox'].append({
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })

            logger.info(f"Extracted {len(filtered_data['text'])} text elements")
            return filtered_data

        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            return {'text': [], 'confidence': [], 'bbox': []}

    def extract_chart_data(self, image_path: str) -> Dict[str, Any]:
        """
        Extract numerical data from chart/graph images

        Args:
            image_path: Path to chart image

        Returns:
            Dictionary with extracted numbers and labels
        """
        try:
            logger.info(f"Extracting chart data from: {image_path}")

            # Extract text
            text = self.extract_text(image_path, preprocess=True)

            # Parse numbers from text
            import re
            numbers = re.findall(r'[-+]?\d*\.\d+|\d+', text)

            # Extract data with positions
            data = self.extract_data(image_path)

            result = {
                'raw_text': text,
                'numbers': [float(n) for n in numbers if n],
                'elements': data
            }

            logger.info(f"Found {len(result['numbers'])} numbers in chart")
            return result

        except Exception as e:
            logger.error(f"Error extracting chart data: {str(e)}")
            return {'raw_text': '', 'numbers': [], 'elements': {}}

    def batch_extract(
        self,
        image_paths: List[str],
        lang: str = 'kor+eng'
    ) -> Dict[str, str]:
        """
        Extract text from multiple images

        Args:
            image_paths: List of image file paths
            lang: Language for OCR

        Returns:
            Dictionary mapping image path to extracted text
        """
        results = {}

        for image_path in image_paths:
            text = self.extract_text(image_path, lang=lang)
            results[image_path] = text

        logger.info(f"Processed {len(results)} images")
        return results


# Singleton instance
_ocr_processor: Optional[OCRProcessor] = None


def get_ocr_processor(tesseract_path: Optional[str] = None) -> OCRProcessor:
    """Get or create OCR processor instance"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor(tesseract_path)
    return _ocr_processor


# Example usage
if __name__ == "__main__":
    # Test OCR processor
    processor = OCRProcessor()

    # Test with sample image
    # text = processor.extract_text("sample_chart.png")
    # print(f"Extracted text: {text}")

    # Test chart data extraction
    # chart_data = processor.extract_chart_data("etf_chart.png")
    # print(f"Chart numbers: {chart_data['numbers']}")

    logger.info("OCR Processor test completed")
