"""Unit tests for the receipt text parser."""

import unittest
from receipt_ocr.parser import ReceiptParser


class TestReceiptParser(unittest.TestCase):

    def setUp(self):
        self.parser = ReceiptParser()

    def test_parse_esselunga_receipt(self):
        sample_text = (
            "ESSELUNGA S.P.A.\n"
            "CORSO RE UMBERTO 50 - TORINO\n"
            "DATA: 12/10/2026 ORA: 14:32\n"
            "--------------------------------\n"
            "LATTE INTERO 1L          1.49 €\n"
            "PANE INTEGRALE           2.20 €\n"
            "PASTA BARILLA 500G       1.15 €\n"
            "--------------------------------\n"
            "SUBTOTALE                4.84 €\n"
            "IVA 10%                  0.48 €\n"
            "TOTALE EURO              4.84 €\n"
            "PAGAMENTO BANCOMAT\n"
        )
        result = self.parser.parse(sample_text)
        self.assertEqual(result.metadata.merchant, "Esselunga")
        self.assertEqual(result.metadata.date, "2026-10-12")
        self.assertEqual(result.metadata.time, "14:32")
        self.assertAlmostEqual(result.metadata.total_amount, 4.84)
        self.assertEqual(result.metadata.category, "Groceries")
        self.assertEqual(result.metadata.payment_method, "Card")
        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.items[0].name, "LATTE INTERO 1L")
        self.assertAlmostEqual(result.items[0].price, 1.49)

    def test_parse_dates(self):
        text_iso = "STORE ABC\nDATE: 2026-05-18\nTOTAL: 15.00 EUR"
        res_iso = self.parser.parse(text_iso)
        self.assertEqual(res_iso.metadata.date, "2026-05-18")

        text_dot = "STORE ABC\nDATA: 25.12.2025\nTOTALE: 99.00 EUR"
        res_dot = self.parser.parse(text_dot)
        self.assertEqual(res_dot.metadata.date, "2025-12-25")

    def test_parse_empty_or_noisy_text(self):
        result = self.parser.parse("   \n\n  ")
        self.assertEqual(result.metadata.merchant, "Unknown Merchant")
        self.assertEqual(result.metadata.total_amount, 0.0)
        self.assertEqual(result.items, [])


if __name__ == "__main__":
    unittest.main()
