"""Streamlit Web Application for Receipt OCR Pipeline & Financial Manager."""

from __future__ import annotations
import os
import tempfile
import pandas as pd
from PIL import Image

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

from receipt_ocr.pipeline import ReceiptPipeline
from receipt_ocr.sample_generator import generate_synthetic_receipt
from receipt_ocr.database import ReceiptDatabase


def main():
    if not HAS_STREAMLIT:
        print("Streamlit is not installed. Run 'pip install streamlit' to launch the web dashboard.")
        return

    st.set_page_config(
        page_title="Receipt OCR Pipeline | Financial Manager",
        page_icon="🧾",
        layout="wide",
    )

    st.title("🧾 Automated Receipt OCR Pipeline")
    st.caption("Document AI & Automated Ingestion Layer for Financial Manager")

    db_path = "financial_manager.db"
    db = ReceiptDatabase(db_path)
    pipeline = ReceiptPipeline(db_path=db_path)

    tab1, tab2, tab3 = st.tabs(["📤 Ingest Receipt", "📊 Spending Dashboard", "🏗️ Pipeline Architecture"])

    with tab1:
        st.subheader("Upload & Process Receipt")
        col_input, col_preview = st.columns([1, 1])

        with col_input:
            uploaded_file = st.file_uploader(
                "Upload a grocery or store receipt",
                type=["png", "jpg", "jpeg"]
            )
            use_sample = st.button("✨ Load Sample Receipt (Esselunga)")

            img_path = None
            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    img_path = tmp.name
            elif use_sample:
                os.makedirs("sample_receipts", exist_ok=True)
                sample_file = "sample_receipts/sample_esselunga.png"
                generate_synthetic_receipt(sample_file)
                img_path = sample_file

        if img_path:
            with col_preview:
                st.image(img_path, caption="Receipt Image", use_container_width=True)

            with st.spinner("Processing image through OCR pipeline..."):
                result = pipeline.process_receipt(img_path, save_to_db=False)

            st.success(f"Processing complete in {result.latency_ms:.1f} ms! (Confidence: {result.metadata.confidence_score*100:.0f}%)")

            # Form to verify & edit before committing to DB
            with st.form("receipt_form"):
                st.subheader("Parsed Receipt Details")
                c1, c2, c3 = st.columns(3)
                merchant = c1.text_input("Merchant", value=result.metadata.merchant)
                date = c2.text_input("Date", value=result.metadata.date or "")
                category = c3.selectbox(
                    "Category",
                    ["Groceries", "Dining", "Electronics", "Pharmacy", "Sports", "Other"],
                    index=0
                )

                c4, c5, c6 = st.columns(3)
                total = c4.number_input("Total Amount (€)", value=float(result.metadata.total_amount), step=0.01)
                tax = c5.number_input("Tax / IVA (€)", value=float(result.metadata.tax_amount or 0.0), step=0.01)
                payment = c6.text_input("Payment Method", value=result.metadata.payment_method or "Card")

                if result.items:
                    st.write("Itemized Breakdown:")
                    items_df = pd.DataFrame([item.to_dict() for item in result.items])
                    st.dataframe(items_df, use_container_width=True)

                submit = st.form_submit_button("💾 Save to Financial Manager DB")
                if submit:
                    result.metadata.merchant = merchant
                    result.metadata.date = date
                    result.metadata.category = category
                    result.metadata.total_amount = total
                    result.metadata.tax_amount = tax
                    result.metadata.payment_method = payment
                    db.save_receipt(result)
                    st.balloons()
                    st.success("Receipt successfully saved to database!")

    with tab2:
        st.subheader("Financial Analytics & Spending Trends")
        receipts = db.get_all_receipts()

        if receipts:
            df = pd.DataFrame(receipts)
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Expenses", f"{df['total_amount'].sum():.2f} €")
            m2.metric("Receipts Processed", len(df))
            m3.metric("Average Receipt", f"{df['total_amount'].mean():.2f} €")

            st.write("### Spending by Category")
            cat_summary = db.get_category_summary()
            if cat_summary:
                cat_df = pd.DataFrame(cat_summary)
                st.bar_chart(data=cat_df, x="category", y="total_spent")

            st.write("### Recent Transactions")
            st.dataframe(df[["id", "date", "merchant", "category", "total_amount", "currency", "confidence_score"]], use_container_width=True)
        else:
            st.info("No receipts found. Ingest your first receipt in the 'Ingest Receipt' tab.")

    with tab3:
        st.subheader("End-to-End Pipeline Architecture")
        st.markdown("""
        ```
        [Receipt Image]
              │
              ▼
        [OpenCV / Pillow Preprocessing] (Grayscale, Bilateral Filter, Otsu Thresholding)
              │
              ▼
        [Tesseract OCR Engine] (PSM 6, OEM 3 Character Recognition)
              │
              ▼
        [Regex & RapidFuzz Parser] (Extract Merchant, ISO Date, Amounts, Line Items)
              │
              ▼
        [SQLite Ingestion & Analytics] (Financial Manager Core Database)
        ```
        """)


if __name__ == "__main__":
    main()
