"""Data models for Receipt OCR Pipeline."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime, timezone


@dataclass
class ReceiptItem:
    """Represents an individual line item on a receipt."""
    name: str
    price: float
    quantity: float = 1.0
    category: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReceiptMetadata:
    """Metadata extracted from a receipt."""
    merchant: str
    date: Optional[str] = None  # YYYY-MM-DD
    time: Optional[str] = None  # HH:MM:SS
    total_amount: float = 0.0
    subtotal_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    currency: str = "EUR"
    category: str = "Groceries"
    payment_method: Optional[str] = None
    confidence_score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ParsedReceipt:
    """Complete parsed receipt data payload."""
    metadata: ReceiptMetadata
    items: List[ReceiptItem] = field(default_factory=list)
    raw_text: str = ""
    image_path: Optional[str] = None
    processed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "raw_text": self.raw_text,
            "image_path": self.image_path,
            "processed_at": self.processed_at,
            "latency_ms": self.latency_ms,
        }
