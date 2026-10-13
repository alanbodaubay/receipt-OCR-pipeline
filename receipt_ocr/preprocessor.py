"""Image Preprocessor module for receipt image normalization.

Applies contrast stretching, grayscale conversion, binarization, and deskewing
to maximize OCR character recognition accuracy.
"""

from __future__ import annotations
import os
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class ImagePreprocessor:
    """Preprocesses receipt images for downstream OCR processing."""

    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi

    def preprocess(self, image_path: str, output_path: Optional[str] = None) -> Image.Image:
        """Preprocesses an input image using OpenCV if available, else Pillow.

        Steps:
        1. Convert to grayscale.
        2. Enhance contrast and sharpness.
        3. Denoise and threshold.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Receipt image not found at: {image_path}")

        if HAS_OPENCV:
            processed_pil = self._preprocess_opencv(image_path)
        else:
            processed_pil = self._preprocess_pillow(image_path)

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            processed_pil.save(output_path)

        return processed_pil

    def _preprocess_opencv(self, image_path: str) -> Image.Image:
        """High-performance OpenCV pipeline with Gaussian blur and Otsu binarization."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Failed to decode image with OpenCV: {image_path}")

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Resize if small
        h, w = gray.shape[:2]
        if w < 1000:
            scale = 1000.0 / w
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        # 3. Bilateral filter for noise reduction while keeping edges sharp
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # 4. Adaptive thresholding or Otsu thresholding
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            12
        )

        return Image.fromarray(thresh)

    def _preprocess_pillow(self, image_path: str) -> Image.Image:
        """Pure-Pillow fallback pipeline ensuring zero-crash dependency portability."""
        img = Image.open(image_path)

        # 1. Convert to grayscale
        gray = ImageOps.grayscale(img)

        # 2. Upscale small images
        w, h = gray.size
        if w < 1000:
            factor = 1000.0 / w
            gray = gray.resize((int(w * factor), int(h * factor)), Image.Resampling.BICUBIC)

        # 3. Enhance contrast
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(2.0)

        # 4. Enhance sharpness
        sharpness = ImageEnhance.Sharpness(high_contrast)
        sharpened = sharpness.enhance(1.8)

        # 5. Median filter for noise reduction
        cleaned = sharpened.filter(ImageFilter.MedianFilter(size=3))

        return cleaned
