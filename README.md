# Automated Receipt OCR Pipeline

This project extends the "Financial Manager" by automating data entry using Computer Vision and OCR. Instead of manually typing expenses, users upload an image of a grocery receipt, and the pipeline automatically extracts the store, date, and total amount, inserting it directly into the database.

## 🏗️ Pipeline Architecture

```mermaid
flowchart TD
    A[Upload Receipt Image\n(Streamlit UI)] --> B(Image Preprocessing\nOpenCV)
    B -->|Grayscale, Thresholding,\nDeskewing| C(Optical Character Recognition\nTesseract OCR)
    C -->|Raw Text String| D(Information Extraction\nPython Regex / NLP)
    D -->|Parsed: Store, Date, Total| E(Data Validation\nPandas)
    E --> F[(SQLite Database\nFinancial Manager)]
    F --> G[Update Spending Forecasts\n& Visualizations]
```

## 🛠️ Technology Stack
*   **Computer Vision:** `OpenCV` (for cleaning the image so the OCR can read it clearly)
*   **OCR Engine:** `pytesseract` (Python wrapper for Google's Tesseract OCR)
*   **Text Processing:** `re` (Regular Expressions for finding prices and dates)
*   **Data Handling:** `pandas`
*   **Database:** `SQLite`
*   **Frontend:** `Streamlit`

## 🚀 Implementation Phases

1.  **Phase 1: Image Preprocessing (OpenCV)**
    *   Real-world receipts are crumpled, shadowed, and low-contrast. We will write an OpenCV script to convert the image to grayscale, apply adaptive thresholding, and increase contrast.
2.  **Phase 2: Text Extraction (Tesseract)**
    *   Pass the cleaned image to Tesseract to extract the raw text.
3.  **Phase 3: Parsing the Data**
    *   Write logic to scan the text for keywords like "TOTAL", "EUR", "$", and parse dates.
4.  **Phase 4: Integration**
    *   Connect the parsed data to your existing SQLite database and update the Streamlit UI to include a "Drag and Drop Receipt" feature.
