"""Unit tests for the SQLite receipt database."""

import unittest
import tempfile
import os
from receipt_ocr.database import ReceiptDatabase
from receipt_ocr.models import ParsedReceipt, ReceiptMetadata, ReceiptItem


class TestReceiptDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()
        self.db = ReceiptDatabase(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_retrieve_receipt(self):
        metadata = ReceiptMetadata(
            merchant="Esselunga",
            date="2026-10-14",
            total_amount=15.50,
            category="Groceries",
            confidence_score=0.9,
        )
        items = [
            ReceiptItem(name="Apples", price=5.00),
            ReceiptItem(name="Milk", price=10.50),
        ]
        parsed = ParsedReceipt(metadata=metadata, items=items)

        receipt_id = self.db.save_receipt(parsed)
        self.assertGreater(receipt_id, 0)

        all_records = self.db.get_all_receipts()
        self.assertEqual(len(all_records), 1)
        self.assertEqual(all_records[0]["merchant"], "Esselunga")
        self.assertAlmostEqual(all_records[0]["total_amount"], 15.50)

        total = self.db.get_total_spend()
        self.assertAlmostEqual(total, 15.50)

        cats = self.db.get_category_summary()
        self.assertEqual(len(cats), 1)
        self.assertEqual(cats[0]["category"], "Groceries")
        self.assertAlmostEqual(cats[0]["total_spent"], 15.50)


if __name__ == "__main__":
    unittest.main()
