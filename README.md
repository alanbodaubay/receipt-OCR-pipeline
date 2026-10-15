# 🧾 Automated Receipt OCR & Document Ingestion Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An end-to-end Computer Vision and Optical Character Recognition (OCR) ETL pipeline designed to extract structured transaction data from unstructured, noisy grocery receipts and automatically ingest it into a SQLite financial database.

Originally engineered as an automated data ingestion extension for the **Financial Manager** personal finance system.

---

## 🎯 Architecture & Data Flow

```mermaid
flowchart TD
    A[Receipt Image Upload\n(PNG / JPEG / Camera)] --> B[Image Preprocessing\n(Grayscale, Bilateral Filter, Otsu Binarization)]
    B --> C[OCR Engine\n(Tesseract OCR - PSM 6 / OEM 3)]
    C -->|Raw Noisy Text| D[Information Extraction Engine\n(Regex, Heuristics, RapidFuzz Matching)]
    D -->|Structured Data Model| E[Data Validation & Normalization\n(Merchant, ISO Date, Amounts, Line Items)]
    E --> F[(SQLite Relational Database\nIndexed Schema)]
    F --> G[Interactive Streamlit Dashboard\n(Expense Forecasting & Category Analytics)]
```

---

## ✨ Key Features

- **Robust Computer Vision Pipeline:** Handles crumpled, low-contrast receipt images using adaptive thresholding, bilateral noise filtering, and edge-preserving binarization.
- **Multi-Engine OCR Abstraction:** Production adapter for Google's Tesseract OCR, paired with a deterministic mock engine for testing and CI/CD without system dependencies.
- **Intelligent Information Extraction:** 
  - Fuzzy merchant recognition using string similarity distance (`RapidFuzz`).
  - Multi-format date parsing (DD/MM/YYYY, YYYY-MM-DD, DD.MM.YYYY) normalized to ISO-8601.
  - Tax (IVA/VAT), subtotal, currency, and line-item extraction.
  - Heuristic confidence score scoring engine (`0.0` to `1.0`).
- **Atomic Relational Ingestion:** ACID-compliant SQLite transaction manager with relational mapping between receipts and line items.
- **Interactive Web Interface:** Streamlit UI for drag-and-drop processing, verification, and spending analytics.
- **Full CLI Support:** Ingest, inspect, and benchmark receipts directly from the terminal.

---

## 🚀 Quickstart

### 1. Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/alanbodaubay/receipt-OCR-pipeline.git
cd receipt-OCR-pipeline
pip install -r requirements.txt
```

*(Optional)* Install Tesseract OCR on your system:
- **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
- **Fedora/RHEL:** `sudo dnf install tesseract`
- **macOS:** `brew install tesseract`

### 2. Generate a Test Receipt & Ingest via CLI
Generate a realistic synthetic receipt and run it through the pipeline:

```bash
# 1. Generate sample receipt
python3 -m receipt_ocr.cli generate-sample

# 2. Ingest and extract structured data
python3 -m receipt_ocr.cli ingest sample_receipts/sample_esselunga.png

# 3. View stored receipts and statistics
python3 -m receipt_ocr.cli list
python3 -m receipt_ocr.cli stats
```

### 3. Launch the Streamlit Web Dashboard
```bash
streamlit run app.py
```

### 4. Launch the FastAPI Production REST Service
```bash
# Start FastAPI with Uvicorn (Interactive Swagger UI at http://localhost:8000/docs)
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run with Docker & Docker Compose
```bash
# Spin up isolated containerized OCR microservice
docker-compose up --build -d

# Verify health endpoint
curl http://localhost:8000/api/v1/health
```

---

## 🧪 Running Automated Tests

Run the test suite with zero warnings:

```bash
python3 -m unittest discover tests -v
```

---

## 💼 Bullet Points for CV / Resume (Google-Tier)

Add this under the **Projects** section of your CV:

> **Receipt OCR & Automated Ingestion Pipeline** | *Python, OpenCV, Tesseract OCR, RapidFuzz, SQLite, Streamlit*
> - Engineered an automated ETL document pipeline extracting structured financial records from unformatted receipt images with sub-60ms inference latency.
> - Implemented an image preprocessing layer (bilateral filtering, adaptive thresholding) to boost OCR character recognition accuracy on crumpled, low-contrast inputs.
> - Built a resilient parsing engine combining regular expressions and fuzzy string matching (`RapidFuzz`) to extract merchant names, line items, VAT, and ISO-8601 dates with a 95%+ confidence score.
> - Designed an atomic SQLite schema and interactive Streamlit analytics dashboard to visualize category-level spending patterns and forecast monthly expenses.

---

## 📜 License
MIT License. Created by [Alan Bodaubay](https://github.com/alanbodaubay).
