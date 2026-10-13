"""Regex and Heuristic Receipt Parser for Information Extraction.

Extracts merchant name, dates, line items, tax, and total amount from raw OCR text.
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import List, Tuple, Optional
from receipt_ocr.models import ParsedReceipt, ReceiptItem, ReceiptMetadata

try:
    from rapidfuzz import process, fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

KNOWN_MERCHANTS = [
    ("Esselunga", "Groceries"),
    ("Carrefour", "Groceries"),
    ("Conad", "Groceries"),
    ("Coop", "Groceries"),
    ("Lidl", "Groceries"),
    ("Aldi", "Groceries"),
    ("Pam", "Groceries"),
    ("Eurospin", "Groceries"),
    ("MediaWorld", "Electronics"),
    ("Unieuro", "Electronics"),
    ("Decathlon", "Sports"),
    ("McDonald's", "Dining"),
    ("Burger King", "Dining"),
    ("Starbucks", "Dining"),
    ("Farmacia", "Pharmacy"),
]

TOTAL_KEYWORDS = [
    r"\bTOTAL\b",
    r"\bTOTALE\b",
    r"\bTOTALE\s+EURO\b",
    r"\bTOTALE\s+DOVUTO\b",
    r"\bTOTAL\s+DUE\b",
    r"\bAMOUNT\s+DUE\b",
    r"\bIMPORTE\b",
    r"\bBALANCE\b",
]

SUBTOTAL_KEYWORDS = [
    r"\bSUBTOTAL\b",
    r"\bSUBTOTALE\b",
    r"\bIMPORTO\s+NETTO\b",
]

TAX_KEYWORDS = [
    r"\bTAX\b",
    r"\bIVA\b",
    r"\bVAT\b",
    r"\bIMPOSTA\b",
]


class ReceiptParser:
    """Parses noisy, unstructured OCR text strings into structured models."""

    def parse(self, raw_text: str, image_path: Optional[str] = None) -> ParsedReceipt:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        merchant, category = self._extract_merchant(lines)
        date, time = self._extract_date_time(raw_text)
        total, subtotal, tax = self._extract_amounts(lines)
        items = self._extract_line_items(lines)
        currency = self._extract_currency(raw_text)
        payment_method = self._extract_payment_method(raw_text)

        confidence = self._calculate_confidence(merchant, date, total, items)

        metadata = ReceiptMetadata(
            merchant=merchant,
            date=date,
            time=time,
            total_amount=total,
            subtotal_amount=subtotal,
            tax_amount=tax,
            currency=currency,
            category=category,
            payment_method=payment_method,
            confidence_score=confidence,
        )

        return ParsedReceipt(
            metadata=metadata,
            items=items,
            raw_text=raw_text,
            image_path=image_path,
        )

    def _extract_merchant(self, lines: List[str]) -> Tuple[str, str]:
        """Identifies the store/vendor name using fuzzy matching or top-of-receipt text."""
        if not lines:
            return "Unknown Merchant", "Other"

        top_lines = lines[:5]

        if HAS_RAPIDFUZZ:
            for line in top_lines:
                clean_line = line.lower()
                for name, category in KNOWN_MERCHANTS:
                    score = fuzz.partial_ratio(name.lower(), clean_line)
                    if score >= 75:
                        return name, category

        # Fallback: clean the first line
        first_line = re.sub(r"[^A-Za-z0-9\s\.\&]", "", top_lines[0]).strip()
        return (first_line if len(first_line) > 2 else "Receipt Store"), "Groceries"

    def _extract_date_time(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts date and normalizes to ISO YYYY-MM-DD."""
        date_str = None
        time_str = None

        # Matches: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD.MM.YYYY
        date_patterns = [
            (r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b", "%d/%m/%Y"),
            (r"\b(\d{4})[/-](\d{2})[/-](\d{2})\b", "%Y-%m-%d"),
            (r"\b(\d{2})\.(\d{2})\.(\d{4})\b", "%d.%m.%Y"),
            (r"\b(\d{2})[/-](\d{2})[/-](\d{2})\b", "%d/%m/%y"),
        ]

        for pattern, date_fmt in date_patterns:
            match = re.search(pattern, text)
            if match:
                raw_matched = match.group(0).replace("-", "/").replace(".", "/")
                clean_fmt = date_fmt.replace("-", "/").replace(".", "/")
                try:
                    dt = datetime.strptime(raw_matched, clean_fmt)
                    date_str = dt.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

        # Matches: HH:MM:SS or HH:MM
        time_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)(:([0-5]\d))?\b", text)
        if time_match:
            time_str = time_match.group(0)

        return date_str, time_str

    def _extract_amounts(self, lines: List[str]) -> Tuple[float, Optional[float], Optional[float]]:
        """Extracts Total, Subtotal, and Tax values from lines."""
        total = 0.0
        subtotal = None
        tax = None

        amount_regex = re.compile(r"(\d+[\.,]\d{2})")

        for line in reversed(lines):
            # Check for TOTAL
            if any(re.search(kw, line, re.IGNORECASE) for kw in TOTAL_KEYWORDS):
                matches = amount_regex.findall(line)
                if matches and total == 0.0:
                    val = float(matches[-1].replace(",", "."))
                    if val > total:
                        total = val

            # Check for SUBTOTAL
            if any(re.search(kw, line, re.IGNORECASE) for kw in SUBTOTAL_KEYWORDS):
                matches = amount_regex.findall(line)
                if matches and subtotal is None:
                    subtotal = float(matches[-1].replace(",", "."))

            # Check for TAX
            if any(re.search(kw, line, re.IGNORECASE) for kw in TAX_KEYWORDS):
                matches = amount_regex.findall(line)
                if matches and tax is None:
                    tax = float(matches[-1].replace(",", "."))

        # Fallback for total: highest price found in bottom half
        if total == 0.0:
            candidate_floats = []
            for line in lines[len(lines)//2:]:
                for match in amount_regex.findall(line):
                    candidate_floats.append(float(match.replace(",", ".")))
            if candidate_floats:
                total = max(candidate_floats)

        return total, subtotal, tax

    def _extract_line_items(self, lines: List[str]) -> List[ReceiptItem]:
        """Extracts itemized products and prices."""
        items: List[ReceiptItem] = []
        item_regex = re.compile(r"^(.+?)\s+([0-9]+[\.,][0-9]{2})\s*[$€£]?$")

        for line in lines:
            # Skip totals or headers
            if any(re.search(kw, line, re.IGNORECASE) for kw in TOTAL_KEYWORDS + SUBTOTAL_KEYWORDS + TAX_KEYWORDS):
                continue
            if "DATA" in line or "DATE" in line or "ORA" in line or "---" in line:
                continue

            match = item_regex.match(line)
            if match:
                desc, price_str = match.groups()
                desc = desc.strip()
                # Exclude purely numeric or short noise
                if len(desc) >= 3 and not desc.isdigit():
                    price = float(price_str.replace(",", "."))
                    items.append(ReceiptItem(name=desc, price=price))

        return items

    def _extract_currency(self, text: str) -> str:
        if "€" in text or "EUR" in text or "EURO" in text:
            return "EUR"
        if "$" in text or "USD" in text:
            return "USD"
        if "£" in text or "GBP" in text:
            return "GBP"
        return "EUR"

    def _extract_payment_method(self, text: str) -> Optional[str]:
        text_upper = text.upper()
        if "BANCOMAT" in text_upper or "CARTA" in text_upper or "CARD" in text_upper or "VISA" in text_upper:
            return "Card"
        if "CONTANTI" in text_upper or "CASH" in text_upper:
            return "Cash"
        return None

    def _calculate_confidence(
        self, merchant: str, date: Optional[str], total: float, items: List[ReceiptItem]
    ) -> float:
        """Calculates a deterministic confidence score [0.0 - 1.0]."""
        score = 0.0
        if merchant and merchant != "Unknown Merchant":
            score += 0.3
        if date:
            score += 0.25
        if total > 0.0:
            score += 0.35
        if items:
            score += 0.1
        return round(min(score, 1.0), 2)
