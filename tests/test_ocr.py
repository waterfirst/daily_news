"""
Tests for OCR functionality
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from PIL import Image
import numpy as np

from src.utils.ocr_processor import OCRProcessor


class TestOCRProcessor:
    """Test OCR Processor"""

    def test_ocr_processor_init(self):
        """Test OCR processor initialization"""
        processor = OCRProcessor()
        assert processor is not None

    def test_preprocess_image(self):
        """Test image preprocessing"""
        processor = OCRProcessor()

        # Create a simple test image
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        image = Image.fromarray(img_array)

        # Preprocess
        preprocessed = processor.preprocess_image(image)

        assert preprocessed is not None
        assert isinstance(preprocessed, Image.Image)

    @pytest.mark.skipif(
        not pytest.config.getoption("--run-ocr", default=False),
        reason="OCR tests require Tesseract installation"
    )
    def test_extract_text_from_image(self):
        """Test text extraction (requires Tesseract)"""
        processor = OCRProcessor()

        # Create a simple image with text
        # In real test, use an actual image file
        # For now, just test the method exists
        assert hasattr(processor, 'extract_text')

    def test_extract_chart_data_method_exists(self):
        """Test chart data extraction method exists"""
        processor = OCRProcessor()
        assert hasattr(processor, 'extract_chart_data')


def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--run-ocr",
        action="store_true",
        default=False,
        help="Run tests that require Tesseract OCR"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
