"""End-to-end integration tests for the Receipt Pipeline."""

import unittest
import tempfile
import os
from receipt_ocr.pipeline import ReceiptPipeline
from receipt_ocr.ocr_engine import MockOCREngine
from receipt_ocr.sample_generator import generate_synthetic_receipt


class TestReceiptPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        self.sample_img = os.path.join(self.temp_dir.name, "receipt.png")
        generate_synthetic_receipt(self.sample_img)

        # Use mock OCR engine to ensure fast and deterministic execution
        self.pipeline = ReceiptPipeline(
            db_path=self.db_path,
            ocr_engine=MockOCREngine()
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_execution(self):
        result = self.pipeline.process_receipt(self.sample_img, save_to_db=True)

        self.assertIsNotNone(result)
        self.assertEqual(result.metadata.merchant, "Esselunga")
        self.assertGreater(result.metadata.total_amount, 0.0)
        self.assertGreater(result.latency_ms, 0.0)

        # Verify database record
        receipts = self.pipeline.database.get_all_receipts()
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["merchant"], "Esselunga")


if __name__ == "__main__":
    unittest.main()
