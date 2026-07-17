#!/usr/bin/env python3
"""
NZ Visa PDF Generator - v3
Fixes: no stretch, cn font in cells, bank right side = english,
       proper col widths, no travel history, proper itinerary
"""
import os, io, re, atexit, tempfile, copy
from datetime import datetime, date

import fitz
from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, HRFlowable, PageBreak,
                                Image as RLImage)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUTDIR = "./input/output"
SRCDIR = "./input"
os.makedirs(OUTDIR, exist_ok=True)

# Info
INFO = {
    "name_cn": "张三", "name_en": "Zhang San",
    "gender": "Male", "dob": "1995-05-25",
    "id_num": "110101199001011014", "passport": "ER1234567",
    "phone": "(000) 0000 0000", "email": "example@example.com",
    "address_en": "Feiyada Hi-Tech Building, Gaoxin South 1st Rd, Nanshan, Shenzhen",
    "employer_en": "Futu Network Technology (Shenzhen) Co., Ltd.",
    "job_title": "HR Manager", "salary": "CNY 45,000",
}

# Colors
C_DB = colors.HexColor("#1A3A5C")
C_MB = colors.HexColor("#2C5F8A")
C_LB = colors.HexColor("#EEF3F8")
C_AR = colors.HexColor("#F5F7FA")
C_BR = colors.HexColor("#CCCCCC")
C_DT = colors.HexColor("#1A1A1A")
C_GR = colors.HexColor("#555555")
C_WH = colors.white
C_RD = colors.HexColor("#CC0000")
C_GN = colors.HexColor("#1A7A1A")
C_TL = colors.HexColor("#888888")

# Font
CN_FONT = None
for fp in ["/System/Library/Fonts/STHeiti Light.ttc", "/Library/Fonts/Arial Unicode.ttf"]:
    if os.path.exists(fp):
        try:
            if fp.endswith('.ttc'):
                pdfmetrics.registerFont(TTFont("CN", fp, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont("CN", fp))
            CN_FONT = "CN"
            print(f"Font: {fp}")
            break
        except: pass
if not CN_FONT: CN_FONT = "Helvetica"

# Temp file mgmt
_tmp = []
def _cln():
    for f in _tmp:
        try: os.unlink(f)
        except: pass
atexit.register(_cln)

def tmpf(img):
    f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(f.name, "JPEG", quality=92)
    _tmp.append(f.name); f.close()
    return f.name

def proc_img(path, max_s=1200):
    pil = Image.open(path)
    pil = ImageOps.exif_transpose(pil)
    w, h = pil.size
    if max(w, h) > max_s:
        r = max_s / max(w, h)
        pil = pil.resize((int(w*r), int(h*r)), Image.LANCZOS)
    if pil.mode in ('RGBA', 'P'): pil = pil.convert('RGB')
    return pil

def img_keep_ratio(path, max_w_mm=130, max_h_mm=85):
    """RLImage keeping original aspect ratio"""
    pil = proc_img(path)
    w, h = pil.size
    mw, mh = max_w_mm*mm, max_h_mm*mm
    s = min(mw/w, mh/h, 1.0)
    return RLImage(tmpf(pil), width=w*s, height=h*s)

def img_from_pdf_page(pdf_path, pg, max_w_mm=130, max_h_mm=80, dpi=2.5):
    doc = fitz.open(pdf_path)
    p = doc[pg]
    pix = p.get_pixmap(matrix=fitz.Matrix(dpi, dpi))
    img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
    w, h = img.size
    mw, mh = max_w_mm*mm, max_h_mm*mm
    s = min(mw/w, mh/h, 1.0)
    doc.close()
    return RLImage(tmpf(img), width=w*s, height=h*s)

# Styles
S = {}
B = ParagraphStyle("b", fontName="Helvetica", fontSize=9, textColor=C_DT)
S["N"] = B
S["T"] = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=14, textColor=C_DB, alignment=TA_CENTER, spaceAfter=6)
S["ST"] = ParagraphStyle("st", fontName="Helvetica", fontSize=10, textColor=C_GR, alignment=TA_CENTER, spaceAfter=6)
S["SH"] = ParagraphStyle("sh", parent=B, fontName=CN_FONT, fontSize=11, textColor=C_WH, backColor=C_MB, leftIndent=5, rightIndent=5, spaceBefore=6, spaceAfter=4, leading=14)
S["TL"] = ParagraphStyle("tl", parent=B, fontName="Helvetica-Oblique", fontSize=7, textColor=C_TL, alignment=TA_RIGHT)
S["LT"] = ParagraphStyle("lt", parent=B, fontName="Helvetica-Bold", fontSize=12, alignment=TA_CENTER, spaceAfter=14)
S["LB"] = ParagraphStyle("lb", parent=B, fontName="Helvetica", fontSize=10, leading=15, spaceAfter=6, alignment=TA_JUSTIFY)
S["IT"] = ParagraphStyle("it", parent=B, fontName="Helvetica-Bold", fontSize=14, textColor=C_DB, alignment=TA_CENTER, spaceAfter=4)
S["IS"] = ParagraphStyle("is", parent=B, fontName="Helvetica", fontSize=9, textColor=C_GR, alignment=TA_CENTER, spaceAfter=6)
S["NO"] = ParagraphStyle("no", parent=B, fontSize=7, textColor=C_GR, fontName="Helvetica-Oblique")

def P(text, style="N"):
    return Paragraph(text, S[style])

def Pcn(text, font_name=None):
    fn = font_name or CN_FONT
    return Paragraph(text, ParagraphStyle("cn", fontName=fn, fontSize=8, textColor=C_DT))

def translator_footer(story):
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BR))
    story.append(P("Translated by: Zhang San | Self-translated for visa application", "TL"))

def hs(label):
    """Helper: section header"""
    return Paragraph(label, S["SH"])

# ═══════════════════════════════════════════════
# 01 - Passport
# ═══════════════════════════════════════════════
def gen_01_passport():
    out = os.path.join(OUTDIR, "01_passport_护照.pdf")
    files = ["护照中文.JPG"] + [f"签证页{i}.JPG" for i in range(1, 8)]
    pdf = fitz.open()
    for f in files:
        fp = os.path.join(SRCDIR, f)
        if os.path.exists(fp):
            pil = proc_img(fp, max_s=1200)
            buf = io.BytesIO()
            pil.save(buf, format='JPEG', quality=92)
            buf.seek(0)
            idoc = fitz.open("jpg", buf.read())
            pb = idoc.convert_to_pdf()
            idoc.close()
            ipdf = fitz.open("pdf", pb)
            pdf.insert_pdf(ipdf)
    pdf.save(out); pdf.close()
    print(f"[OK] 01_passport_护照.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 02 - ID Card
# ═══════════════════════════════════════════════
def gen_02_id():
    out = os.path.join(OUTDIR, "02_national_id_身份证.pdf")
    doc = SimpleDocTemplate(out, pagesize=landscape(A4),
        leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=15*mm)
    story = []

    # Page 1 - Front
    story.append(hs("Page 1 — Front Side (正面)"))
    story.append(Spacer(1, 3*mm))

    front = [
        ("Name", "Zhang San"),
        ("Gender", "Male"),
        ("Ethnic Group", "Han"),
        ("Date of Birth", "May 25, 1995"),
        ("Address", INFO["address_en"]),
        ("Citizen ID No.", INFO["id_num"]),
    ]
    left1 = img_keep_ratio(os.path.join(SRCDIR, "身份证1.jpg"))
    data1 = [["Field", "English Translation"]]
    for f, v in front:
        data1.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    t1 = Table(data1, colWidths=[52*mm, 52*mm], repeatRows=1)
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB),
        ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    lay1 = Table([[left1, t1]], colWidths=[130*mm, 110*mm])
    lay1.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(lay1)
    story.append(PageBreak())

    # Page 2 - Back
    story.append(hs("Page 2 — Back Side (背面)"))
    story.append(Spacer(1, 3*mm))

    back = [
        ("Document Title", "People's Republic of China Resident Identity Card"),
        ("Issuing Authority", "Shenzhen Public Security Bureau Nanshan Branch"),
        ("Valid Period", "Apr 3, 2019 – Apr 3, 2029"),
    ]
    left2 = img_keep_ratio(os.path.join(SRCDIR, "身份证2.jpg"))
    data2 = [["Field", "English Translation"]]
    for f, v in back:
        data2.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    t2 = Table(data2, colWidths=[52*mm, 52*mm], repeatRows=1)
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB),
        ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    lay2 = Table([[left2, t2]], colWidths=[130*mm, 110*mm])
    lay2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(lay2)
    doc.build(story)
    print(f"[OK] 02_national_id_身份证.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 03 - Employment + Business License
# ═══════════════════════════════════════════════
def gen_03_employment():
    out = os.path.join(OUTDIR, "03_employment_verification_在职证明.pdf")
    doc = SimpleDocTemplate(out, pagesize=landscape(A4),
        leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=15*mm)
    story = []

    # Part 1
    story.append(hs("Part 1: Employment Verification Letter (在职证明)"))
    story.append(Spacer(1, 3*mm))

    emp_fields = [
        ("Name", INFO["name_en"]),
        ("Gender", "Male"),
        ("Date of Birth", "May 25, 1995"),
        ("Passport No.", INFO["passport"]),
        ("Employer", INFO["employer_en"]),
        ("Position", "HR Manager"),
        ("Employment Start Date", "June 2022"),
        ("Monthly Salary", "CNY 45,000"),
    ]
    left_e = img_keep_ratio(os.path.join(SRCDIR, "在职证明.JPG"))
    ed = [["Field", "English Translation"]]
    for f, v in emp_fields:
        ed.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    et = Table(ed, colWidths=[45*mm, 60*mm], repeatRows=1)
    et.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB),
        ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    el = Table([[left_e, et]], colWidths=[130*mm, 110*mm])
    el.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(el)

    story.append(Spacer(1, 4*mm))

    # Part 2 - new page
    story.append(PageBreak())
    story.append(hs("Part 2: Business License (营业执照)"))
    story.append(Spacer(1, 3*mm))

    biz_fields = [
        ("Unified Social Credit Code", "914403005825792400"),
        ("Enterprise Name", "Xuda Network Technology (Shenzhen) Co., Ltd."),
        ("Enterprise Type", "Limited Liability Company (Wholly HK-owned)"),
        ("Legal Representative", "Li Hua"),
        ("Date of Establishment", "[See Original Document]"),
        ("Address", "[See Original Document - relates to Futu Group]"),
        ("Registration Authority", "Shenzhen Market Supervision Administration"),
    ]
    left_b = img_keep_ratio(os.path.join(SRCDIR, "营业执照.JPG"))
    bd = [["Field", "English Translation"]]
    for f, v in biz_fields:
        bd.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    bt = Table(bd, colWidths=[45*mm, 60*mm], repeatRows=1)
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB),
        ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    bl = Table([[left_b, bt]], colWidths=[130*mm, 110*mm])
    bl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(bl)
    doc.build(story)
    print(f"[OK] 03_employment_verification_在职证明.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 04 - Household Register
# ═══════════════════════════════════════════════
def gen_04_household():
    out = os.path.join(OUTDIR, "04_household_register_户口本.pdf")
    doc = SimpleDocTemplate(out, pagesize=landscape(A4),
        leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=15*mm)
    story = []

    # Page 1
    story.append(hs("Page 1 — Household Register Cover (户口本封面)"))
    story.append(Spacer(1, 3*mm))
    left1 = img_keep_ratio(os.path.join(SRCDIR, "户口本1.JPG"))
    cf = [
        ("Document Title", "Household Register (户口簿)"),
        ("Issuing Authority", "Shenzhen PSB Futian Branch"),
        ("Region", "Futian District, Shenzhen, Guangdong"),
        ("Address", "Shangmeilin Yicun, Meilin Street, Futian, Shenzhen"),
        ("Head of Household", INFO["name_en"]),
        ("Household No.", "504028504"),
    ]
    cd = [["Field", "English Translation"]]
    for f, v in cf:
        cd.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    ct = Table(cd, colWidths=[45*mm, 60*mm], repeatRows=1)
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB),
        ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    l1 = Table([[left1, ct]], colWidths=[130*mm, 110*mm])
    l1.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(l1)
    story.append(PageBreak())

    # Page 2
    story.append(hs("Page 2 — Personal Information (户口本个人信息页)"))
    story.append(Spacer(1, 3*mm))
    left2 = img_keep_ratio(os.path.join(SRCDIR, "户口本2.JPG"))
    hf = [
        ("Name", INFO["name_en"]), ("Gender", "Male"),
        ("Ethnic Group", "Han"), ("Place of Birth", "Raohe, Heilongjiang"),
        ("Native Place", "Xinjin, Liaoning"),
        ("Date of Birth", "May 25, 1995"),
        ("ID Card No.", INFO["id_num"]),
        ("Height", "173 cm"), ("Blood Type", "Type O"),
        ("Education", "Bachelor's Degree"), ("Marital Status", "Single"),
        ("Military Service", "Not Served"),
        ("Workplace", INFO["employer_en"]),
        ("Religion", "None"),
        ("Address", "Shangmeilin Yicun, Futian, Shenzhen"),
    ]
    hd2 = [["Field", "English Translation"]]
    for f, v in hf:
        hd2.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    ht = Table(hd2, colWidths=[45*mm, 60*mm], repeatRows=1)
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB),
        ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    l2 = Table([[left2, ht]], colWidths=[130*mm, 110*mm])
    l2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(l2)
    doc.build(story)
    print(f"[OK] 04_household_register_户口本.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 05 - Bank Statement
# ═══════════════════════════════════════════════
# Chinese-to-English transaction type lookup
TX_CN_EN = {
    # Payment types
    "快捷支付": "Quick Debit", "银联快捷支付": "UnionPay Quick Debit",
    "支付宝": "Alipay", "微信支付": "WeChat Pay",
    "云闪付": "Cloud QuickPass", "Apple Pay": "Apple Pay",
    "银联": "UnionPay", "网联": "NetsUnion",
    "快捷": "Quick Pay", "支付": "Payment",
    "快E付": "Quick E-Pay", "扫码": "Scan Code",
    # Transfer types
    "跨行转账": "Inter-bank Transfer",
    "转账": "Transfer", "网银转账": "Online Transfer",
    "转入": "Transfer In", "转出": "Transfer Out",
    "收入": "Income", "支出": "Expense",
    "汇入": "Inward Remittance", "汇出": "Outward Remittance",
    "代发工资": "Salary Payroll",
    # Transaction categories
    "消费": "Purchase", "商户消费": "Merchant Purchase",
    "取款": "Withdrawal", "存款": "Deposit",
    "利息": "Interest", "手续费": "Service Fee",
    "理财": "Wealth Management", "基金": "Fund Investment",
    "缴费": "Bill Payment", "水费": "Water Bill",
    "电费": "Electric Bill", "燃气费": "Gas Bill",
    "工资": "Salary", "奖金": "Bonus",
    "还款": "Repayment", "贷款": "Loan",
    "保险": "Insurance", "退款": "Refund",
    "结汇": "FX Settlement", "购汇": "FX Purchase",
    # Income/Expense
    "收入": "Income", "支出": "Expense",
    # Transaction specific
    "个贷交易": "Personal Loan Transaction",
    "ATM取款": "ATM Withdrawal",
    "POS消费": "POS Purchase",
    "网上支付": "Online Payment",
    "手机支付": "Mobile Payment",
    "代收": "Agency Collection",
    "代付": "Agency Payment",
    "批量": "Batch",
    "佣金": "Commission",
    # Common bank terms
    "收款": "Collection", "付款": "Payment",
    "储蓄": "Savings", "活期": "Current",
    "定期": "Time Deposit", "通知存款": "Call Deposit",
    "余额": "Balance", "明细": "Details",
    # Counterparty related
    "有限公司": "Co., Ltd.", "股份": "Holdings",
    "银行": "Bank", "证券": "Securities",
    "基金销售": "Fund Distribution",
    "蚂蚁": "Ant Group",
    "招商银行": "CMB China",
    "网络科技": "Network Technology",
    "保险": "Insurance",
    "快递": "Express",
    # Common substrings
    "服务": "Service", "科技": "Technology", "网络": "Network",
    "有限公司": "Co., Ltd.", "股份有限公司": "Co., Ltd.", "有限": "Limited",
    "（杭州）": "(Hangzhou)", "（深圳）": "(Shenzhen)",
    "（广州）": "(Guangzhou)", "（北京）": "(Beijing)",
    "（上海）": "(Shanghai)", "（中国）": "(China)",
    "服务费": "Service Fee", "费": "Fee",
    "还款": "Repayment", "贷款": "Loan",
    "代发": "Payroll", "工资": "Salary", "奖金": "Bonus",
    "佣金": "Commission", "利息": "Interest",
    "手续费": "Processing Fee",
    "理财": "Wealth Mgmt", "基金": "Fund",
    "缴费": "Bill Pay", "退款": "Refund",
    "购物": "Shopping", "餐饮": "Dining",
    "交通": "Transport", "娱乐": "Entertainment",
    # Bank-specific
    "支行": "Sub-branch", "分行": "Branch",
    "开户行": "Account Branch",
    "个人贷款结清证明": "Personal Loan Settlement Certificate",
    "个人贷款": "Personal Loan",
    "结清证明": "Settlement Certificate",
    "互联网": "Internet", "信息": "Information",
    "技术": "Technology", "开发": "Development",
    "咨询": "Consulting", "管理": "Management",
    "经营": "Operations", "进出口": "Import/Export",
    "实业": "Industry", "集团": "Group",
    "企业": "Enterprise", "贸易": "Trade",
    "投资": "Investment", "控股": "Holding",
    "商贸": "Commerce", "食品": "Food",
    "生物": "Bio", "医疗": "Medical",
    "文化": "Culture", "传媒": "Media",
    "通信": "Telecom", "电子": "Electronics",
}

def cn2en(text):
    """Translate Chinese bank text to English"""
    if not text:
        return text
    # Check if already English (no Chinese chars)
    if not re.search(r'[\u4e00-\u9fff]', text):
        return text
    result = text
    # Sort by length descending to match longer terms first
    items = sorted(TX_CN_EN.items(), key=lambda x: -len(x[0]))
    for cn, en in items:
        result = result.replace(cn, en)
    # If still has Chinese characters that weren't matched
    if re.search(r'[\u4e00-\u9fff]', result):
        # Return partially translated + [see original] note
        return result + " [orig]"
    return result

def parse_bank():
    path = os.path.join(SRCDIR, "交易流水中文.pdf")
    doc = fitz.open(path)
    all_pages = []
    for p in range(len(doc)):
        lines = [l.strip() for l in doc[p].get_text().split('\n') if l.strip()]
        tx = []
        i = 0
        while i < len(lines):
            l = lines[i]
            if re.match(r'^\d{4}-\d{2}-\d{2}$', l):
                d = l
                c = lines[i+1] if i+1 < len(lines) else ''
                a = lines[i+2] if i+2 < len(lines) else ''
                b = lines[i+3] if i+3 < len(lines) else ''
                s = lines[i+4] if i+4 < len(lines) else ''
                cp = lines[i+5] if i+5 < len(lines) else ''
                # Translate
                s_en = cn2en(s)
                cp_en = cn2en(cp)
                tx.append((d, c, a, b, s_en, cp_en))
                i += 6
            else:
                i += 1
        all_pages.append(tx)
    doc.close()
    return all_pages

def gen_05_bank():
    out = os.path.join(OUTDIR, "05_bank_statements_银行证明.pdf")
    doc = SimpleDocTemplate(out, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm, topMargin=12*mm, bottomMargin=15*mm)
    story = []

    story.append(hs("Bank Statement — China Merchants Bank (招商银行交易流水)"))
    story.append(Spacer(1, 3*mm))

    # Account summary
    sd = [
        [Pcn("<b>Account Holder:</b>"), Pcn(INFO["name_en"]),
         Pcn("<b>Account No.:</b>"), Pcn("6214********0525")],
        [Pcn("<b>Period:</b>"), Pcn("Apr 12, 2025 – Apr 12, 2026"),
         Pcn("<b>Currency:</b>"), Pcn("CNY")],
    ]
    st = Table(sd, colWidths=[30*mm, 40*mm, 25*mm, 40*mm])
    st.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("BACKGROUND", (0,0), (-1,-1), C_LB),
        ("GRID", (0,0), (-1,-1), 0.3, C_BR),
        ("TOPPADDING", (0,0), (-1,-1), 2), ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(st)
    story.append(Spacer(1, 3*mm))

    all_p = parse_bank()
    total = sum(len(p) for p in all_p)
    print(f"  Bank: {len(all_p)} pages, {total} txns")

    # Available width: 297mm - 20mm margins = 277mm
    # Left image ~135mm, right table ~140mm (with gap)
    CW = [20*mm, 12*mm, 22*mm, 22*mm, 30*mm, 28*mm]  # total = 134mm for right table

    for pi, page_tx in enumerate(all_p):
        if pi > 0:
            story.append(PageBreak())
            story.append(hs(f"Bank Statement — Page {pi+1} (Continued)"))
            story.append(Spacer(1, 2*mm))

        # Left: original page image
        left_img = img_from_pdf_page(os.path.join(SRCDIR, "交易流水中文.pdf"), pi, 135, 75, dpi=1.5)

        # Right: translated table
        hdr = [["Date", "Curr", "Amount", "Balance", "Summary", "Counter Party"]]
        rows = hdr + [
            [d, c, a, b,
             (s[:18]+"...") if len(s)>18 else (s if s else "-"),
             (cp[:18]+"...") if len(cp)>18 else (cp if cp else "-")]
            for d, c, a, b, s, cp in page_tx
        ]
        display = rows[:12]  # limit to 12 rows

        # Convert all cells to Paragraph with CN font (for Chinese-safe rendering)
        pd = []
        for row in display:
            pd.append([Pcn(cell) for cell in row])

        tt = Table(pd, colWidths=CW, repeatRows=1)
        tstyle = [
            ("BACKGROUND", (0,0), (-1,0), C_DB),
            ("TEXTCOLOR", (0,0), (-1,0), C_WH),
            ("FONTSIZE", (0,0), (-1,0), 6),
            ("ALIGN", (0,0), (-1,0), "CENTER"),
            ("FONTSIZE", (0,1), (-1,-1), 5.5),
            ("ALIGN", (0,1), (1,-1), "CENTER"),
            ("ALIGN", (2,1), (3,-1), "RIGHT"),
            ("GRID", (0,0), (-1,-1), 0.3, C_BR),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 1.5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
            ("LEFTPADDING", (0,0), (-1,-1), 1),
            ("RIGHTPADDING", (0,0), (-1,-1), 1),
        ]
        # Color amounts
        for ri in range(1, len(pd)):
            amt = str(page_tx[ri-1][2]) if ri-1 < len(page_tx) else ""
            if amt.startswith('-'):
                tstyle.append(("TEXTCOLOR", (2,ri), (2,ri), C_RD))
            else:
                tstyle.append(("TEXTCOLOR", (2,ri), (2,ri), C_GN))

        tt.setStyle(TableStyle(tstyle))

        # Left-right layout
        lay = Table([[left_img, tt]], colWidths=[135*mm, sum(CW)])
        lay.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                                  ("LEFTPADDING", (1,0), (1,0), 4)]))
        story.append(lay)
        story.append(Spacer(1, 1*mm))
        story.append(P(f"<i>Page {pi+1}/{len(all_p)} — Original on left, English translation on right</i>", "NO"))

    doc.build(story)
    print(f"[OK] 05_bank_statements_银行证明.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 06 - Trip Itinerary
# ═══════════════════════════════════════════════
def gen_06_itinerary():
    out = os.path.join(OUTDIR, "06_travel_itinerary_旅行计划.pdf")
    doc = SimpleDocTemplate(out, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm, topMargin=12*mm, bottomMargin=12*mm)
    story = []

    story.append(P("Trip Itinerary — New Zealand South Island (10 Days)", "IT"))
    story.append(P("Departing Shenzhen • November 10–19, 2026 • Self-Drive & Tour", "IS"))
    story.append(HRFlowable(width="100%", thickness=1, color=C_MB, spaceAfter=6))

    it = [
        ("1", "Nov 10 Tue", "Shenzhen → Christchurch", "Flight SZX→CHC (via AKL, ~13h). Arrive evening. Collect rental car. Check into city hotel.", "Christchurch", "Flight CX124"),
        ("2", "Nov 11 Wed", "Christchurch", "Christchurch Botanic Gardens (free entry, 2h). Punting on Avon River (NZ$35). Cathedral Square. New Regent St shops. Riverside Market dinner.", "Christchurch", "Walk / Tram"),
        ("3", "Nov 12 Thu", "CHC → Lake Tekapo (230km)", "Drive via Geraldine (pie stop). Arrive Tekapo noon. Church of the Good Shepherd. Mt John Observatory walk (1h). Night: Dark Sky Reserve stargazing.", "Lake Tekapo", "Car Rental"),
        ("4", "Nov 13 Fri", "Tekapo → Mt Cook (105km)", "Hooker Valley Track (3h, easy). Tasman Glacier Lake. Kea Point walk (1h). White Horse Hill picnic. Drive to Wanaka evening.", "Wanaka", "Car Rental"),
        ("5", "Nov 14 Sat", "Wanaka", "Roys Peak Track (6h, stunning summit views). Or relax: Lake Wanaka cruise, Puzzling World (NZ$22). That Wanaka Tree photo. Cinema Paradiso dinner.", "Wanaka", "Walk / Car"),
        ("6", "Nov 15 Sun", "Wanaka → Queenstown (70km)", "Scenic drive over Crown Range (highest main road). Arrive Queenstown noon. Skyline Gondola + Luge (NZ$59). Lake Wakatipu walk. Fergburger dinner.", "Queenstown", "Car Rental"),
        ("7", "Nov 16 Mon", "Milford Sound Day Trip", "Early departure (6:30am). Drive via Te Anau. Milford Road scenic stops: Mirror Lakes, Homer Tunnel. Milford Sound cruise (2h, NZ$85). Return Queenstown 7pm.", "Queenstown", "Day Tour Bus"),
        ("8", "Nov 17 Tue", "Queenstown", "Glenorchy & Paradise half-day drive (45min each way, LOTR filming locations). Afternoon: Kawarau Bungy (NZ$205) or Onsen Hot Pools. Evening: Skyline dinner.", "Queenstown", "Car Rental"),
        ("9", "Nov 18 Wed", "Queenstown → Dunedin (280km)", "Drive via Kawarau Gorge, Cromwell fruitlands. Alexandra lunch. Arrive Dunedin 3pm. Larnach Castle tour (NZ$45). Otago Peninsula wildlife: albatross, seals.", "Dunedin", "Car Rental"),
        ("10", "Nov 19 Thu", "Dunedin → CHC → Shenzhen", "Morning: Otago Museum (free), Dunedin Railway Station (photo). Drive to CHC (360km, 4h). Return car. Flight CHC→SZX departs ~8pm.", "N/A", "Flight CZ618"),
    ]

    cw = [9*mm, 22*mm, 30*mm, 62*mm, 22*mm, 20*mm]  # total ~165mm
    hdr = [["Day", "Date", "Route", "Activities & Sightseeing", "Hotel", "Transport"]]
    # Convert all cells to Paragraph
    pd = []
    for row in (hdr + it):
        pd.append([Pcn(cell) for cell in row])

    t = Table(pd, colWidths=cw, repeatRows=1)
    ts = [
        ("BACKGROUND", (0,0), (-1,0), C_DB),
        ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 7),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("FONTSIZE", (0,1), (-1,-1), 5.5),
        ("ALIGN", (0,1), (1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.3, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("TOPPADDING", (0,0), (-1,-1), 1.5), ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
        ("LEFTPADDING", (0,0), (-1,-1), 1.5), ("RIGHTPADDING", (0,0), (-1,-1), 1.5),
        ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#E8F4FD")),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#E8F4FD")),
    ]
    t.setStyle(TableStyle(ts))
    story.append(t)

    story.append(Spacer(1, 3*mm))
    story.append(P("Accommodation & flight costs estimated. All prices in NZD unless noted. Flights: Shenzhen→Christchurch via Cathay Pacific or China Southern.", "NO"))

    doc.build(story)
    print(f"[OK] 06_travel_itinerary_旅行计划.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 07 - Statement (Multiple Entry)
# ═══════════════════════════════════════════════
def gen_07_statement():
    out = os.path.join(OUTDIR, "07_statement_multiple_journeys_入境陈述.pdf")
    doc = SimpleDocTemplate(out, pagesize=A4,
        leftMargin=60, rightMargin=60, topMargin=50, bottomMargin=50)
    story = []

    story.append(P("STATEMENT OF INTENDED MULTIPLE JOURNEYS TO NEW ZEALAND", "LT"))
    story.append(P("To Whom It May Concern,", "LB"))
    story.append(Spacer(1, 2))

    body = f"""
<b>Re: Statement of Intended Multiple Journeys to New Zealand</b>

<b>1. Purpose</b><br/>
I am applying for a multiple-entry visitor visa to New Zealand to explore both the North and South Islands over multiple trips between 2026 and 2028.

<b>2. Applicant Information</b><br/>
<b>Name:</b> {INFO["name_en"]}<br/>
<b>Passport:</b> {INFO["passport"]}<br/>
<b>Nationality:</b> People's Republic of China<br/>
<b>National ID:</b> {INFO["id_num"]}<br/>
<b>DOB:</b> {INFO["dob"]}<br/>
<b>Employer:</b> {INFO["employer_en"]} — HR Manager<br/>
<b>Salary:</b> {INFO["salary"]}/month

<b>3. Reasons for Multiple Visits</b><br/>
New Zealand offers vastly different experiences across regions and seasons. I plan to:
<ul>
<li><b>Trip 1 (Nov 2026):</b> South Island self-drive — Christchurch, Lake Tekapo, Mt Cook, Wanaka, Queenstown, Milford Sound, Dunedin (10 days)</li>
<li><b>Trip 2 (Mar 2028):</b> Return South Island — Queenstown, Milford Sound, Dunedin, Lake Tekapo (7 days)</li>
</ul>
One trip is not enough to properly experience New Zealand's diverse landscapes.

<b>4. Financial Capacity</b><br/>
My stable employment ({INFO["employer_en"]}, {INFO["salary"]}/month) and savings demonstrate full financial capability. I have also settled a mortgage loan of RMB 3,020,000, showing responsible financial management.

<b>5. Return Ties</b><br/>
<ul>
<li>Permanent full-time employment in Shenzhen</li>
<li>Bachelor's degree, registered residence in Shenzhen</li>
<li>Family and social network across China</li>
<li>Proven travel history to 8+ countries with full compliance</li>
</ul>

<b>6. Declaration</b><br/>
I, {INFO["name_en"]}, declare that all information in this statement is true. I will comply with all NZ immigration conditions and depart before each authorized stay expires.

Sincerely,<br/><br/>
{INFO["name_en"]}<br/>
HR Manager, {INFO["employer_en"]}<br/>
{INFO["phone"]} | {INFO["email"]}<br/>
{date.today().strftime("%B %d, %Y")}
"""
    for para in body.split("\n\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(para.replace("\n", "<br/>"), S["LB"]))
            story.append(Spacer(1, 2))

    doc.build(story)
    print(f"[OK] 07_statement_multiple_journeys_入境陈述.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 08 - Subsequent Journey Plan
# ═══════════════════════════════════════════════
def gen_08_subsequent():
    out = os.path.join(OUTDIR, "08_subsequent_journey_plan_后续旅行计划.pdf")
    doc = SimpleDocTemplate(out, pagesize=landscape(A4),
        leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=15*mm)
    story = []

    trip1 = [
        ("1", "Nov 10", "Shenzhen → Christchurch", "Flight, rental car, city check-in", "Christchurch", "Flight CX124"),
        ("2", "Nov 11", "Christchurch", "Botanic Gardens, punting, Cathedral Square", "Christchurch", "Walk / Tram"),
        ("3", "Nov 12", "CHC → Lake Tekapo", "Geraldine, Church of Good Shepherd, stargazing", "Lake Tekapo", "Car"),
        ("4", "Nov 13", "Tekapo → Mt Cook → Wanaka", "Hooker Valley Track, Tasman Glacier", "Wanaka", "Car"),
        ("5", "Nov 14", "Wanaka", "Roys Peak or Lake walk, Puzzling World", "Wanaka", "Walk / Car"),
        ("6", "Nov 15", "Wanaka → Queenstown", "Crown Range, Skyline Gondola, Luge", "Queenstown", "Car"),
        ("7", "Nov 16", "Milford Sound", "Full day cruise (Te Anau, Mirror Lakes)", "Queenstown", "Tour Bus"),
        ("8", "Nov 17", "Queenstown", "Glenorchy, Paradise, Kawarau Bungy", "Queenstown", "Car"),
        ("9", "Nov 18", "Queenstown → Dunedin", "Cromwell, Larnach Castle, Otago Peninsula", "Dunedin", "Car"),
        ("10", "Nov 19", "Dunedin → CHC → Shenzhen", "Otago Museum, drive to CHC, flight home", "N/A", "Flight CZ618"),
    ]
    trip2 = [
        ("1", "Mar 10 2028", "Shenzhen → Queenstown", "Flight arrival, town walk", "Queenstown", "Flight"),
        ("2", "Mar 11", "Queenstown", "Skyline Gondola, Bob's Peak hike", "Queenstown", "Walk"),
        ("3", "Mar 12", "Queenstown → Milford Sound", "Milford Road scenic drive", "Te Anau", "Car"),
        ("4", "Mar 13", "Milford → Dunedin", "Scenic coastal drive", "Dunedin", "Car"),
        ("5", "Mar 14", "Dunedin", "Larnach Castle, Otago Museum, Railway Station", "Dunedin", "Bus"),
        ("6", "Mar 15", "Dunedin → Lake Tekapo", "Church of Good Shepherd, stargazing", "Lake Tekapo", "Car"),
        ("7", "Mar 16", "Tekapo → CHC → Shenzhen", "Morning drive, return flight", "N/A", "Flight"),
    ]

    cw = [10*mm, 22*mm, 35*mm, 50*mm, 22*mm, 22*mm]
    hdr = [["Day", "Date", "Route", "Activities", "Accommodation", "Transportation"]]

    for ti, (tname, tdata) in enumerate([
        ("Trip 1 — November 2026 (South Island)", trip1),
        ("Trip 2 — March 2028 (South Island)", trip2),
    ]):
        story.append(P(f"Multiple Journey Plan — {tname}", "IT"))
        story.append(P("New Zealand", "IS"))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_MB, spaceAfter=4))
        pd = []
        for row in (hdr + tdata):
            pd.append([Pcn(cell) for cell in row])
        t = Table(pd, colWidths=cw, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_DB),
            ("TEXTCOLOR", (0,0), (-1,0), C_WH),
            ("FONTSIZE", (0,0), (-1,0), 7.5),
            ("ALIGN", (0,0), (-1,0), "CENTER"),
            ("FONTSIZE", (0,1), (-1,-1), 7),
            ("ALIGN", (0,1), (1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("GRID", (0,0), (-1,-1), 0.4, C_BR),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
            ("TOPPADDING", (0,0), (-1,-1), 2.5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2.5),
            ("LEFTPADDING", (0,0), (-1,-1), 2), ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ]))
        story.append(t)
        if ti < 1: story.append(PageBreak())

    doc.build(story)
    print(f"[OK] 08_subsequent_journey_plan_后续旅行计划.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# 10 - Assets (Loan Certificate only)
# ═══════════════════════════════════════════════
def gen_10_assets():
    out = os.path.join(OUTDIR, "10_proof_of_assets_资产证明.pdf")
    doc = SimpleDocTemplate(out, pagesize=landscape(A4),
        leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=15*mm)
    story = []

    # ═══ Part 1: Property Certificate (房产证2) ═══
    story.append(hs("Part 1: Property Ownership Certificate (房产证)"))
    story.append(Spacer(1, 3*mm))

    prop_path = os.path.join(SRCDIR, "房产证2.JPG")
    prop_img = None
    if os.path.exists(prop_path):
        pil = Image.open(prop_path)
        pil = ImageOps.exif_transpose(pil)
        if max(pil.size) > 2000:
            pil.thumbnail((2000, 2000), Image.LANCZOS)
        w, h = pil.size
        tmp_path = tmpf(pil)
        mw, mh = 130*mm, 85*mm
        s = min(mw/w, mh/h, 1.0)
        prop_img = RLImage(tmp_path, width=w*s, height=h*s)

    prop_fields = [
        ("Certificate No.", "Shenzhen Real Estate Cert. No. 0107862"),
        ("Property Address", "Huahai Jinguan, Block C Unit 2903, Xixiang St., Bao'an Dist., Shenzhen"),
        ("Owner Name", INFO["name_en"]),
        ("Title Type", "Certificate of Real Estate Ownership (不动产权证书)"),
        ("Land Type", "State-owned Construction Land Use Rights / Commodity Housing"),
        ("Usage", "Residential / Housing"),
        ("Area", "87.44 sqm"),
        ("Land Use Period", "Aug 29, 1992 – Aug 28, 2062 (70 years)"),
    ]
    pd = [["Field", "English Translation"]]
    for f, v in prop_fields:
        pd.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    pt = Table(pd, colWidths=[40*mm, 65*mm], repeatRows=1)
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB), ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    lay1 = Table([[prop_img, pt]], colWidths=[130*mm, 110*mm])
    lay1.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(lay1)

    story.append(PageBreak())

    # ═══ Part 2: Loan Certificate ═══
    story.append(hs("Part 2: Loan Settlement Certificate (个人贷款结清证明)"))
    story.append(Spacer(1, 3*mm))

    left_img = img_from_pdf_page(os.path.join(SRCDIR, "个人贷款结清证明.pdf"), 0, 130, 85, dpi=3.0)

    lf = [
        ("Certificate Type", "Certificate of Loan Settlement"),
        ("Borrower", INFO["name_en"]),
        ("ID Number", INFO["id_num"]),
        ("Loan Institution", "China Merchants Bank"),
        ("Loan Amount", "RMB 3,020,000.00"),
        ("Settlement Date", "July 2, 2025"),
        ("Outstanding Balance", "0.00 (Fully Settled)"),
        ("Contract No.", "8190423680050"),
    ]
    ld = [["Field", "English Translation"]]
    for f, v in lf:
        ld.append([Pcn(f"<b>{f}</b>"), Pcn(v)])
    lt = Table(ld, colWidths=[40*mm, 65*mm], repeatRows=1)
    lt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_MB), ("TEXTCOLOR", (0,0), (-1,0), C_WH),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.4, C_BR),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WH, C_AR]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    lay2 = Table([[left_img, lt]], colWidths=[130*mm, 110*mm])
    lay2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (1,0), (1,0), 6)]))
    story.append(lay2)

    doc.build(story)
    print(f"[OK] 10_proof_of_assets_资产证明.pdf ({os.path.getsize(out)//1024} KB)")
    return out

# ═══════════════════════════════════════════════
# Manifest
# ═══════════════════════════════════════════════
def gen_manifest(files):
    path = os.path.join(OUTDIR, "_MANIFEST.txt")
    lines = [
        "="*60,
        "NZ Visa Documents — 张三 (Zhang San)",
        f"Passport: {INFO['passport']} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "Type: Multiple Entry | Destination: South Island",
        "="*60, "",
    ]
    for fpath in files:
        base = os.path.basename(fpath)
        size = os.path.getsize(fpath)//1024
        lines.append(f"  {base:<55} {size:>5} KB")
    lines += [
        "", "="*60,
        "Note: All translations left-original/right-English. Passport = originals merged.",
        "="*60,
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] _MANIFEST.txt")

# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    print(f"Generating NZ Visa PDFs for {INFO['name_cn']} ({INFO['name_en']})...\n")
    gen = []
    gen.append(gen_01_passport())
    gen.append(gen_02_id())
    gen.append(gen_03_employment())
    gen.append(gen_04_household())
    gen.append(gen_05_bank())
    gen.append(gen_06_itinerary())
    gen.append(gen_07_statement())
    gen.append(gen_08_subsequent())
    gen.append(gen_10_assets())
    gen_manifest(gen)
    print(f"\nDone! {len(gen)} PDFs → {OUTDIR}")
