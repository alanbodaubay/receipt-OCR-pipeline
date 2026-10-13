"""Command Line Interface (CLI) for Receipt OCR Pipeline."""

from __future__ import annotations
import argparse
import json
import sys
from receipt_ocr.pipeline import ReceiptPipeline
from receipt_ocr.sample_generator import generate_synthetic_receipt
from receipt_ocr.database import ReceiptDatabase


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="receipt_ocr",
        description="Receipt OCR & Ingestion Pipeline for Financial Manager",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest and process a receipt image")
    ingest_parser.add_argument("image_path", help="Path to receipt image file")
    ingest_parser.add_argument("--db", default="financial_manager.db", help="SQLite DB path")
    ingest_parser.add_argument("--no-save", action="store_true", help="Dry run without DB save")

    # Generate sample command
    gen_parser = subparsers.add_parser("generate-sample", help="Generate a synthetic receipt image")
    gen_parser.add_argument(
        "--output", default="sample_receipts/sample_esselunga.png", help="Output PNG path"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List stored receipts in DB")
    list_parser.add_argument("--db", default="financial_manager.db", help="SQLite DB path")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show financial spending statistics")
    stats_parser.add_argument("--db", default="financial_manager.db", help="SQLite DB path")

    args = parser.parse_args()

    if args.command == "generate-sample":
        out = generate_synthetic_receipt(args.output)
        print(f"✅ Generated sample receipt at: {out}")

    elif args.command == "ingest":
        pipeline = ReceiptPipeline(db_path=args.db)
        print(f"🔍 Processing receipt: {args.image_path}...")
        result = pipeline.process_receipt(args.image_path, save_to_db=not args.no_save)

        print("\n--- 🧾 Extracted Receipt Summary ---")
        print(f"Merchant:    {result.metadata.merchant}")
        print(f"Date:        {result.metadata.date}")
        print(f"Time:        {result.metadata.time}")
        print(f"Category:    {result.metadata.category}")
        print(f"Total:       {result.metadata.total_amount:.2f} {result.metadata.currency}")
        print(f"Confidence:  {result.metadata.confidence_score * 100:.1f}%")
        print(f"Latency:     {result.latency_ms:.1f} ms")

        if result.items:
            print(f"\nItemized Products ({len(result.items)} items):")
            for item in result.items:
                print(f"  • {item.name:<25} {item.price:>6.2f} {result.metadata.currency}")

        if not args.no_save:
            print(f"\n💾 Saved successfully to SQLite database: {args.db}")

    elif args.command == "list":
        db = ReceiptDatabase(args.db)
        receipts = db.get_all_receipts()
        if not receipts:
            print("No receipts recorded in database.")
            return

        print(f"{'ID':<4} {'Date':<12} {'Merchant':<18} {'Category':<14} {'Total':>8}")
        print("-" * 60)
        for r in receipts:
            print(
                f"{r['id']:<4} {str(r['date']):<12} {r['merchant'][:17]:<18} "
                f"{r['category']:<14} {r['total_amount']:>7.2f} {r['currency']}"
            )

    elif args.command == "stats":
        db = ReceiptDatabase(args.db)
        total = db.get_total_spend()
        categories = db.get_category_summary()

        print(f"💰 Grand Total Spend: {total:.2f} EUR")
        print("\nCategory Breakdown:")
        for cat in categories:
            print(f"  • {cat['category']:<16}: {cat['total_spent']:>8.2f} EUR ({cat['count']} receipts)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
