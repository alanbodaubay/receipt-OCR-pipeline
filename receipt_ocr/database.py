"""Database integration module for Financial Manager SQLite database.

Persists parsed receipts, itemized records, and provides analytics aggregations.
"""

from __future__ import annotations
import sqlite3
import os
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime
from receipt_ocr.models import ParsedReceipt, ReceiptItem, ReceiptMetadata


class ReceiptDatabase:
    """SQLite database manager for receipt storage and financial queries."""

    def __init__(self, db_path: str = "financial_manager.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes database schema with indexing."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant TEXT NOT NULL,
                    date TEXT,
                    time TEXT,
                    total_amount REAL NOT NULL,
                    subtotal_amount REAL,
                    tax_amount REAL,
                    currency TEXT DEFAULT 'EUR',
                    category TEXT DEFAULT 'Groceries',
                    payment_method TEXT,
                    confidence_score REAL,
                    raw_text TEXT,
                    image_path TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipt_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL DEFAULT 1.0,
                    category TEXT,
                    FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipts_category_date ON receipts(category, date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt_id ON receipt_items(receipt_id)")
            conn.commit()

    def save_receipt(self, receipt: ParsedReceipt) -> int:
        """Inserts a parsed receipt and its line items atomically in a transaction."""
        meta = receipt.metadata
        date_val = meta.date or datetime.now().strftime("%Y-%m-%d")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO receipts (
                    merchant, date, time, total_amount, subtotal_amount, tax_amount,
                    currency, category, payment_method, confidence_score, raw_text,
                    image_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta.merchant,
                date_val,
                meta.time,
                meta.total_amount,
                meta.subtotal_amount,
                meta.tax_amount,
                meta.currency,
                meta.category,
                meta.payment_method,
                meta.confidence_score,
                receipt.raw_text,
                receipt.image_path,
                receipt.processed_at,
            ))

            receipt_id = cursor.lastrowid

            for item in receipt.items:
                cursor.execute("""
                    INSERT INTO receipt_items (receipt_id, name, price, quantity, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (receipt_id, item.name, item.price, item.quantity, item.category or meta.category))

            conn.commit()
            return receipt_id

    def get_all_receipts(self) -> List[Dict[str, Any]]:
        """Retrieves all receipts ordered by date descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM receipts ORDER BY date DESC, id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_category_summary(self) -> List[Dict[str, Any]]:
        """Aggregates total spend by category for visual analytics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, ROUND(SUM(total_amount), 2) as total_spent, COUNT(*) as count
                FROM receipts
                GROUP BY category
                ORDER BY total_spent DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_total_spend(self) -> float:
        """Returns grand total spend across all receipts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ROUND(SUM(total_amount), 2) FROM receipts")
            val = cursor.fetchone()[0]
            return float(val or 0.0)
