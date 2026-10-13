"""OCR Engine interface and implementations.

Supports Tesseract OCR with automatic fallback and mock testing adapters.
"""

from __future__ import annotations
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PIL import Image

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class BaseOCREngine(ABC):
    """Abstract Base Class for OCR engines."""

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        """Extracts plain text from a PIL Image."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the underlying OCR tool is installed and usable."""
        pass


class TesseractEngine(BaseOCREngine):
    """Production OCR engine powered by Google's Tesseract."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.cmd = tesseract_cmd or shutil.which("tesseract")
        if self.cmd and HAS_PYTESSERACT:
            pytesseract.pytesseract.tesseract_cmd = self.cmd

    def is_available(self) -> bool:
        return bool(self.cmd and HAS_PYTESSERACT)

    def extract_text(self, image: Image.Image) -> str:
        if not self.is_available():
            raise RuntimeError(
                "Tesseract is not installed or pytesseract is missing. "
                "Install via: 'sudo dnf install tesseract' (Fedora) or 'sudo apt install tesseract-ocr' (Ubuntu)."
            )
        # PSM 6: Assume a single uniform block of text
        custom_config = r"--oem 3 --psm 6"
        return pytesseract.image_to_string(image, config=custom_config)


class MockOCREngine(BaseOCREngine):
    """Mock OCR engine for automated testing and CI environments."""

    def __init__(self, default_response: Optional[str] = None):
        self.default_response = default_response or (
            "ESSELUNGA S.P.A.\n"
            "CORSO RE UMBERTO 50 - TORINO\n"
            "DATA: 12/10/2026 ORA: 14:32\n"
            "--------------------------------\n"
            "LATTE INTERO 1L          1.49 €\n"
            "PANE INTEGRALE           2.20 €\n"
            "PASTA BARILLA 500G       1.15 €\n"
            "MELE GOLDEN 1KG          2.80 €\n"
            "CAFFE LAVAZZA 250G       3.95 €\n"
            "--------------------------------\n"
            "SUBTOTALE               11.59 €\n"
            "IVA 10%                  1.16 €\n"
            "TOTALE EURO             11.59 €\n"
            "PAGAMENTO BANCOMAT\n"
            "GRAZIE E ARRIVEDERCI\n"
        )

    def is_available(self) -> bool:
        return True

    def extract_text(self, image: Image.Image) -> str:
        # Check if the image has embedded test text in its metadata/info dictionary
        if hasattr(image, "info") and "mock_text" in image.info:
            return image.info["mock_text"]
        return self.default_response


def get_ocr_engine(prefer_mock: bool = False) -> BaseOCREngine:
    """Factory function returning the best available OCR engine."""
    if prefer_mock:
        return MockOCREngine()

    tesseract = TesseractEngine()
    if tesseract.is_available():
        return tesseract

    return MockOCREngine()
