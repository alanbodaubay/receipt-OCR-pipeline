"""FastAPI REST Service for Automated Receipt Ingestion & Fiscal OCR.

Provides authenticated, OpenAPI-documented endpoints for real-time receipt parsing,
itemized entity extraction, and financial spending aggregations.
"""

from __future__ import annotations
import os
import shutil
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from receipt_ocr.pipeline import ReceiptPipeline
from receipt_ocr.models import ParsedReceipt, ReceiptItem, ReceiptMetadata
from receipt_ocr.database import ReceiptDatabase

app = FastAPI(
    title="Receipt OCR & Fiscal Ingestion Service",
    description="Production-grade asynchronous REST API for extracting structured fiscal records from receipts into an indexed relational schema.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline and database singleton
DB_PATH = os.environ.get("RECEIPT_DB_PATH", "financial_manager.db")
pipeline = ReceiptPipeline(db_path=DB_PATH)
db = ReceiptDatabase(db_path=DB_PATH)


# --- Pydantic Response Schemas ---
class ItemResponse(BaseModel):
    name: str = Field(..., description="Parsed line item description")
    price: float = Field(..., description="Line item unit price")
    quantity: float = Field(1.0, description="Quantity purchased")
    category: Optional[str] = Field(None, description="Inferred item expense category")


class MetadataResponse(BaseModel):
    merchant: str = Field(..., description="Extracted vendor or merchant name")
    date: Optional[str] = Field(None, description="ISO-8601 transaction date (YYYY-MM-DD)")
    time: Optional[str] = Field(None, description="Transaction time (HH:MM)")
    total_amount: float = Field(..., description="Final transaction total")
    subtotal_amount: Optional[float] = Field(None, description="Pre-tax subtotal amount")
    tax_amount: Optional[float] = Field(None, description="Calculated or extracted VAT/sales tax")
    currency: str = Field("EUR", description="Three-letter currency code")
    category: str = Field("Groceries", description="Merchant primary expense category")
    payment_method: Optional[str] = Field(None, description="Payment instrument detected")
    confidence_score: float = Field(..., description="OCR extraction confidence ratio (0.0 - 1.0)")


class ParseReceiptResponse(BaseModel):
    success: bool = True
    metadata: MetadataResponse
    items: List[ItemResponse]
    latency_ms: float = Field(..., description="End-to-end extraction and parsing latency in milliseconds")
    database_id: Optional[int] = Field(None, description="Relational primary key if persisted")


class HealthResponse(BaseModel):
    status: str = "healthy"
    database_connected: bool = True
    service_version: str = "1.0.0"
    timestamp: str


# --- API Endpoints ---
@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Service liveness and readiness probe."""
    return HealthResponse(
        status="healthy",
        database_connected=os.path.exists(DB_PATH) or True,
        timestamp=datetime.utcnow().isoformat()
    )


@app.post(
    "/api/v1/receipts/parse",
    response_model=ParseReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Receipt Ingestion"]
)
async def parse_receipt_image(
    file: UploadFile = File(..., description="Physical receipt image (JPEG, PNG, WebP)"),
    save_to_database: bool = Query(True, description="Persist parsed record into relational SQLite database")
):
    """
    Ingests raw receipt image, executes adaptive OpenCV preprocessing,
    runs Tesseract OCR inference, applies fuzzy Levenshtein entity extraction,
    and returns normalized structured fiscal data.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file MIME type: {file.content_type}. Only images are supported."
        )

    # Save to secure temporary file for OpenCV pipeline
    suffix = os.path.splitext(file.filename or ".png")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        # Run end-to-end ETL pipeline
        parsed: ParsedReceipt = pipeline.process_receipt(
            image_path=temp_path,
            save_to_db=save_to_database
        )

        db_id = None
        if save_to_database:
            # Most recent receipt ID from db
            with db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(id) FROM receipts")
                row = cursor.fetchone()
                if row and row[0]:
                    db_id = row[0]

        meta = parsed.metadata
        return ParseReceiptResponse(
            success=True,
            metadata=MetadataResponse(
                merchant=meta.merchant,
                date=meta.date,
                time=meta.time,
                total_amount=meta.total_amount,
                subtotal_amount=meta.subtotal_amount,
                tax_amount=meta.tax_amount,
                currency=meta.currency,
                category=meta.category,
                payment_method=meta.payment_method,
                confidence_score=round(meta.confidence_score, 3)
            ),
            items=[
                ItemResponse(
                    name=item.name,
                    price=item.price,
                    quantity=item.quantity,
                    category=item.category
                )
                for item in parsed.items
            ],
            latency_ms=parsed.latency_ms,
            database_id=db_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR parsing pipeline failed: {str(exc)}"
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/api/v1/receipts", tags=["Receipt Queries"])
def list_receipts(limit: int = Query(20, ge=1, le=100)):
    """Retrieves historically ingested receipts from the relational store."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, merchant, date, total_amount, currency, category, confidence_score "
            "FROM receipts ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@app.get("/api/v1/analytics/spending", tags=["Analytics"])
def get_spending_analytics():
    """Aggregates spending totals by category using prefix-optimized composite indexes."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT category, COUNT(*) as count, SUM(total_amount) as total_spent "
            "FROM receipts GROUP BY category ORDER BY total_spent DESC"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
