"""Synthetic Receipt Image Generator for automated testing and demonstrations."""

from __future__ import annotations
import os
from PIL import Image, ImageDraw, ImageFont


def generate_synthetic_receipt(
    output_path: str = "sample_receipts/sample_esselunga.png",
    merchant: str = "ESSELUNGA S.P.A.",
    address: str = "CORSO RE UMBERTO 50 - TORINO",
    date: str = "12/10/2026",
    time: str = "14:32",
) -> str:
    """Generates a realistic receipt image using Pillow."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    width = 480
    height = 680
    background_color = (252, 252, 250)
    text_color = (20, 20, 20)

    img = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(img)

    # Use default bitmap font
    font = ImageFont.load_default()

    lines = [
        "****************************************",
        f"          {merchant}          ",
        f"    {address}    ",
        f"        DATA: {date}  ORA: {time}        ",
        "****************************************",
        "",
        "DESCRIZIONE                    PREZZO",
        "----------------------------------------",
        "LATTE INTERO 1L                 1.49 EUR",
        "PANE INTEGRALE 500G             2.20 EUR",
        "PASTA BARILLA 500G              1.15 EUR",
        "MELE GOLDEN 1KG                 2.80 EUR",
        "CAFFE LAVAZZA 250G              3.95 EUR",
        "ACQUA NATURALE 6X1.5L           1.80 EUR",
        "----------------------------------------",
        "SUBTOTALE                      13.39 EUR",
        "IVA 10%                         1.34 EUR",
        "TOTALE DOVUTO                  13.39 EUR",
        "----------------------------------------",
        "PAGAMENTO CARTA BANCOMAT",
        "TRANS. N. 849204 APPROVED",
        "",
        "     GRAZIE PER LA VISITA E ARRIVEDERCI!     ",
        "         P.IVA: IT01234567890           ",
        "========================================",
    ]

    y_offset = 30
    for line in lines:
        draw.text((35, y_offset), line, fill=text_color, font=font)
        y_offset += 22

    # Draw simulated barcode at the bottom
    barcode_y = y_offset + 15
    for x in range(60, 420, 4):
        if (x // 4) % 3 != 0:
            draw.line([(x, barcode_y), (x, barcode_y + 40)], fill=(30, 30, 30), width=2)

    img.save(output_path)
    return output_path


if __name__ == "__main__":
    generate_synthetic_receipt()
