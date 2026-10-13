"""End-to-End Receipt Processing Pipeline Orchestrator."""

from __future__ import annotations
import time
from typing import Optional
from receipt_ocr.models import ParsedReceipt
from receipt_ocr.preprocessor import ImagePreprocessor
from receipt_ocr.ocr_engine import BaseOCREngine, get_ocr_engine
from receipt_ocr.parser import ReceiptParser
from receipt_ocr.database import ReceiptDatabase


class ReceiptPipeline:
    """Full ETL Pipeline: Ingestion -> Preprocessing -> OCR -> Parsing -> DB Persistence."""

    def __init__(
        self,
        db_path: str = "financial_manager.db",
        ocr_engine: Optional[BaseOCREngine] = None,
        preprocessor: Optional[ImagePreprocessor] = None,
        parser: Optional[ReceiptParser] = None,
    ):
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.ocr_engine = ocr_engine or get_ocr_engine()
        self.parser = parser or ReceiptParser()
        self.database = ReceiptDatabase(db_path=db_path)

    def process_receipt(
        self,
        image_path: str,
        save_to_db: bool = True,
        save_preprocessed_path: Optional[str] = None,
    ) -> ParsedReceipt:
        """Executes the entire automated pipeline on an input receipt image."""
        start_time = time.perf_counter()

        # Step 1: Preprocessing (grayscaling, contrast, thresholding)
        preprocessed_img = self.preprocessor.preprocess(
            image_path=image_path,
            output_path=save_preprocessed_path
        )

        # Step 2: Optical Character Recognition (OCR)
        raw_text = self.ocr_engine.extract_text(preprocessed_img)

        # Step 3: Information Extraction & Regex/NLP Parsing
        parsed_receipt = self.parser.parse(raw_text=raw_text, image_path=image_path)

        # Compute total latency
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        parsed_receipt.latency_ms = round(elapsed_ms, 2)

        # Step 4: Database Ingestion
        if save_to_db:
            receipt_id = self.database.save_receipt(parsed_receipt)
            # Tag metadata with database ID if needed

        return parsed_receipt
