#!/usr/bin/env python3
"""
Generate bank statement PDF with left-right translation layout.
Extracts data from 交易流水中文.pdf and creates a side-by-side PDF.
"""
import os
import re
import fitz
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                  Paragraph, Spacer, HRFlowable, Image as RLImage, PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PIL import Image
import io
import tempfile

# Colors
COLOR_DARK_BLUE = colors.HexColor("#1A3A5C")
COLOR_MID_BLUE = colors.HexColor("#2C5F8A")
COLOR_LIGHT_BLUE = colors.HexColor("#EEF3F8")
COLOR_ALT_ROW = colors.HexColor("#F5F7FA")
COLOR_BORDER = colors.HexColor("#CCCCCC")
COLOR_DARK_TEXT = colors.HexColor("#1A1A1A")
COLOR_GREY_TEXT = colors.HexColor("#555555")
COLOR_WHITE = colors.white
COLOR_GREEN = colors.HexColor("#1A7A1A")
COLOR_RED = colors.HexColor("#CC0000")

# Translation dictionary for transaction types
TRANSACTION_TYPE_MAP = {
    "个贷交易": "Personal Loan Transaction",
    "银联快捷支付": "UnionPay Quick Pay",
    "快捷支付": "Quick Pay",
    "网联收款": "Online Payment Received",
    "代扣煤气费": "Gas Bill Direct Debit",
    "银联无卡自助消费": "Cardless UnionPay Consumption",
    "代发款项": "Payroll Deposit",
    "综合代发款": "Consolidated Payroll Deposit",
    "电信业务费": "Telecom Service Fee",
    "其他费用": "Other Fees",
    "转账汇款": "Bank Transfer",
    "银证转账(第三方存管)": "Securities Transfer (Third-Party Custody)",
    "汇入汇款": "Incoming Remittance",
    "账户结息": "Account Interest",
    "行内转账转入": "Internal Transfer Received",
    "银联代付": "UnionPay Disbursement",
    "一网通支付鼓励金": "OneNet Payment Rebate",
    "基金加速赎回": "Fund Accelerated Redemption",
    "朝朝宝转入": "ZhaoZhaoBao Transfer In",
    "朝朝宝转出": "ZhaoZhaoBao Transfer Out",
    "申购": "Subscription",
    "数字人民币自动兑换": "Digital RMB Auto Exchange",
    "活动现金红包": "Activity Cash Red Packet",
    "集中代收（提回定借）业务付款": "Centralized Collection Payment",
    "实时代收业务付款": "Real-time Collection Payment",
    "还款": "Repayment",
    "信用卡还款": "Credit Card Repayment",
    "掌上生活还款": "CMBC Life Repayment",
    "养老金缴存（招行渠道招行卡转入）": "Pension Contribution",
    "快捷退款": "Quick Refund",
}

def translate_transaction_type(text):
    """Translate Chinese transaction type to English."""
    if not text:
        return ""
    text = text.strip()
    # Direct match
    if text in TRANSACTION_TYPE_MAP:
        return TRANSACTION_TYPE_MAP[text]
    # Partial match for compound types
    for cn, en in TRANSACTION_TYPE_MAP.items():
        if cn in text:
            return text.replace(cn, en)
    return text

def parse_date(date_str):
    """Convert YYYY-MM-DD to 'DD Month YYYY' format."""
    try:
        from datetime import datetime
        d = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return d.strftime("%d %b %Y")
    except:
        return date_str

def parse_bank_pdf(pdf_path):
    """Parse bank statement PDF and extract all transaction data."""
    doc = fitz.open(pdf_path)
    all_pages_data = []

    for p in range(len(doc)):
        lines = doc[p].get_text().split('\n')
        lines = [l.strip() for l in lines if l.strip()]

        page_tx = []
        i = 0
        while i < len(lines):
            l = lines[i]
            # Check if line starts with a date pattern
            if re.match(r'^\d{4}-\d{2}-\d{2}$', l):
                date = l
                currency = lines[i+1] if i+1 < len(lines) else ''
                amount = lines[i+2] if i+2 < len(lines) else ''
                balance = lines[i+3] if i+3 < len(lines) else ''
                summary = lines[i+4] if i+4 < len(lines) else ''
                counterparty = lines[i+5] if i+5 < len(lines) else ''

                # Translate summary
                summary_en = translate_transaction_type(summary)

                page_tx.append({
                    'date': parse_date(date),
                    'currency': currency,
                    'amount': amount,
                    'balance': balance,
                    'summary': summary,
                    'summary_en': summary_en,
                    'counterparty': counterparty
                })
                i += 6
            else:
                i += 1

        all_pages_data.append(page_tx)

    doc.close()
    return all_pages_data

def render_pdf_page_as_image(pdf_path, page_num, dpi=150):
    """Render a PDF page as a PIL image."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # Render at higher DPI for quality
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    img_data = pix.tobytes("png")
    doc.close()

    pil_img = Image.open(io.BytesIO(img_data))
    return pil_img

def create_styles():
    """Create paragraph styles."""
    styles = {}

    base = ParagraphStyle("base", fontName="Helvetica", fontSize=8, textColor=COLOR_DARK_TEXT)

    styles["section"] = ParagraphStyle(
        "section", parent=base,
        fontName="Helvetica-Bold", fontSize=11,
        textColor=COLOR_WHITE, backColor=COLOR_MID_BLUE,
        leftIndent=5, rightIndent=5, spaceBefore=4, spaceAfter=4,
        leading=14
    )

    styles["header"] = ParagraphStyle(
        "header", parent=base,
        fontName="Helvetica-Bold", fontSize=12,
        textColor=COLOR_DARK_BLUE, alignment=TA_CENTER
    )

    styles["translator"] = ParagraphStyle(
        "translator", parent=base,
        fontName="Helvetica-Oblique", fontSize=7,
        textColor=colors.HexColor("#888888"), alignment=TA_RIGHT
    )

    styles["note"] = ParagraphStyle(
        "note", parent=base,
        fontName="Helvetica-Oblique", fontSize=7,
        textColor=COLOR_GREY_TEXT
    )

    return styles

def format_amount(amount_str):
    """Format amount with + for credits, - for debits."""
    if not amount_str:
        return ""
    try:
        val = float(amount_str.replace(',', ''))
        if val >= 0:
            return f"+{amount_str}"
        else:
            return amount_str
    except:
        return amount_str

def generate_bank_statement_pdf(input_pdf, output_pdf, translator_name="Professional Translation Services"):
    """Generate the bank statement translation PDF."""

    # Parse the original PDF
    all_pages_data = parse_bank_pdf(input_pdf)

    # Check if we got data
    total_tx = sum(len(p) for p in all_pages_data)
    print(f"Extracted {total_tx} transactions across {len(all_pages_data)} pages")

    if total_tx == 0:
        print("WARNING: No transactions extracted, creating template page")
        all_pages_data = [[]]

    styles = create_styles()

    # Create the document
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=landscape(A4),
        leftMargin=8*mm,
        rightMargin=8*mm,
        topMargin=10*mm,
        bottomMargin=15*mm
    )

    story = []

    # Title
    story.append(Paragraph("Bank Statement — China Merchants Bank (招商银行流水)", styles["section"]))
    story.append(Spacer(1, 3*mm))

    # Page info
    page_info = Paragraph(
        f"<b>Statement Period:</b> 12 Apr 2025 – 12 Apr 2026 | <b>Currency:</b> CNY | <b>Account Holder:</b> Account Holder",
        ParagraphStyle("page_info", parent=styles["note"], fontSize=8, spaceAfter=2*mm)
    )
    story.append(page_info)
    story.append(Spacer(1, 2*mm))

    # Process each page
    _temp_files = []

    for page_num, transactions in enumerate(all_pages_data):
        if page_num > 0:
            story.append(PageBreak())
            # Add header for subsequent pages
            story.append(Paragraph("Bank Statement — China Merchants Bank (Continued)", styles["section"]))
            story.append(Spacer(1, 2*mm))

        # Render original page as small thumbnail
        pil_img = render_pdf_page_as_image(input_pdf, page_num, dpi=100)

        # Save to temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        pil_img.save(tmp.name, "PNG")
        _temp_files.append(tmp.name)
        tmp.close()

        # Create image element - smaller for fit
        img_width = 110*mm
        img_height = 150*mm  # Fixed height for consistency

        img_elem = RLImage(tmp.name, width=img_width, height=img_height)

        # Build table data with English translations - limit rows if too many
        header = ["Date", "Currency", "Transaction Amount", "Balance", "Transaction Summary", "Counter Party Information"]

        table_data = [header]

        # Limit to first 20 transactions per page if there are many
        display_transactions = transactions[:20]

        for tx in display_transactions:
            # Format amount with +/- indicator
            amount = tx['amount']
            try:
                val = float(amount.replace(',', ''))
                if val >= 0:
                    amount_display = f"+{amount}"
                else:
                    amount_display = amount
            except:
                amount_display = amount

            row = [
                tx['date'],
                tx['currency'],
                amount_display,
                tx['balance'],
                tx['summary_en'],
                tx['counterparty'][:25] if tx['counterparty'] else ""
            ]
            table_data.append(row)

        # Column widths for translation table (right side)
        col_widths = [22*mm, 16*mm, 28*mm, 22*mm, 42*mm, 32*mm]

        trans_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Build table style
        ts = [
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 6.5),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Data rows
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 6),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Date centered
            ("ALIGN", (1, 1), (1, -1), "CENTER"),  # Currency centered
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),   # Amount right-aligned
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),   # Balance right-aligned
            ("ALIGN", (4, 1), (-1, -1), "LEFT"),   # Summary and counterparty left-aligned
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]

        # Alternating row colors
        if len(table_data) > 1:
            ts.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ALT_ROW]))

        # Amount colors (green for positive, red for negative)
        for row_idx in range(1, len(table_data)):
            amount = table_data[row_idx][2]  # Column 2 is Transaction Amount
            if amount.startswith('+'):
                ts.append(("TEXTCOLOR", (2, row_idx), (2, row_idx), COLOR_GREEN))
            elif amount.startswith('-'):
                ts.append(("TEXTCOLOR", (2, row_idx), (2, row_idx), COLOR_RED))

        trans_table.setStyle(TableStyle(ts))

        # Create side-by-side layout
        left_content = [[img_elem]]
        left_table = Table(left_content, colWidths=[110*mm])
        left_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        right_content = [[trans_table]]
        right_table = Table(right_content, colWidths=[165*mm])
        right_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        # Combine left and right
        layout = Table([[left_table, right_table]], colWidths=[110*mm, 165*mm])
        layout.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (1, 0), (1, 0), 3),
        ]))

        story.append(layout)

        # Add note
        if len(transactions) > len(display_transactions):
            note_text = f"<i>Original on LEFT | Translation on RIGHT | Showing {len(display_transactions)}/{len(transactions)} transactions | Page {page_num + 1}</i>"
        else:
            note_text = f"<i>Original Chinese bank statement on LEFT | English translation on RIGHT | Page {page_num + 1} of {len(all_pages_data)}</i>"

        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(note_text, styles["note"]))

        # Footer
        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER))
        story.append(Paragraph(
            f"Translated by: {translator_name}",
            styles["translator"]
        ))

    # Build PDF
    doc.build(story)

    # Cleanup temp files
    for f in _temp_files:
        try:
            os.unlink(f)
        except:
            pass

    return output_pdf

if __name__ == "__main__":
    input_pdf = "./input/bank_statement.pdf"
    output_pdf = "./output/05_bank_statements.pdf"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    print(f"Input: {input_pdf}")
    print(f"Output: {output_pdf}")

    generate_bank_statement_pdf(input_pdf, output_pdf)

    print(f"\nGenerated: {output_pdf}")
    print(f"Size: {os.path.getsize(output_pdf)/1024:.1f} KB")