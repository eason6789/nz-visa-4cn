#!/usr/bin/env python3
"""
generate_nz_visa_pdfs.py
新西兰签证材料PDF生成器 - 主程序

Usage:
    python generate_nz_visa_pdfs.py --output-dir ./output \
        --name "[APPLICANT_NAME]" --passport "[PASSPORT_NUMBER]" \
        --id "[NATIONAL_ID_NUMBER]" --dob "[DATE_OF_BIRTH]" \
        --phone "[PHONE_NUMBER]" --email "[EMAIL_ADDRESS]" \
        --address "[CURRENT_ADDRESS]" --employer "[EMPLOYER_NAME]" \
        --job-title "[JOB_TITLE]" \
        --trip-type multiple \
        --island south \
        --translator-name "Professional Translation Services" \
        --translator-cert "Certified Translator"

    # 最小可用：
    python generate_nz_visa_pdfs.py --output-dir ./output
"""
import os
import sys
import json
import argparse
from datetime import datetime, date
from typing import List, Dict, Optional

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                  Paragraph, Spacer, HRFlowable, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics

# ─────────────────────────────────────────────────────────────
# 颜色常量
# ─────────────────────────────────────────────────────────────
COLOR_DARK_BLUE   = colors.HexColor("#1A3A5C")
COLOR_MID_BLUE    = colors.HexColor("#2C5F8A")
COLOR_LIGHT_BLUE  = colors.HexColor("#EEF3F8")
COLOR_ALT_ROW     = colors.HexColor("#F5F7FA")
COLOR_BORDER     = colors.HexColor("#CCCCCC")
COLOR_DARK_TEXT  = colors.HexColor("#1A1A1A")
COLOR_GREY_TEXT  = colors.HexColor("#555555")
COLOR_WHITE      = colors.white
COLOR_TRANSLATOR  = colors.HexColor("#888888")


# ─────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────
def make_styles():
    """创建全局样式"""
    styles = {}
    base = ParagraphStyle(
        "base", fontName="Helvetica", fontSize=9, textColor=COLOR_DARK_TEXT
    )
    styles["Normal"] = base

    styles["title"] = ParagraphStyle(
        "title", parent=base,
        fontName="Helvetica-Bold", fontSize=14,
        textColor=COLOR_DARK_BLUE, alignment=TA_CENTER, spaceAfter=6
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", parent=base,
        fontName="Helvetica", fontSize=10,
        textColor=COLOR_GREY_TEXT, alignment=TA_CENTER, spaceAfter=12
    )
    styles["section"] = ParagraphStyle(
        "section", parent=base,
        fontName="Helvetica-Bold", fontSize=11,
        textColor=COLOR_WHITE, backColor=COLOR_MID_BLUE,
        leftIndent=5, rightIndent=5, spaceBefore=8, spaceAfter=4,
        leading=14
    )
    styles["field_label"] = ParagraphStyle(
        "field_label", parent=base,
        fontName="Helvetica-Bold", fontSize=8.5,
        textColor=COLOR_DARK_TEXT
    )
    styles["field_value"] = ParagraphStyle(
        "field_value", parent=base,
        fontName="Helvetica", fontSize=8.5,
        textColor=COLOR_DARK_TEXT
    )
    styles["translator"] = ParagraphStyle(
        "translator", parent=base,
        fontName="Helvetica-Oblique", fontSize=7,
        textColor=COLOR_TRANSLATOR, alignment=TA_RIGHT
    )
    styles["itinerary_header"] = ParagraphStyle(
        "itinerary_header", parent=base,
        fontName="Helvetica-Bold", fontSize=16,
        textColor=COLOR_DARK_BLUE, alignment=TA_CENTER, spaceAfter=4
    )
    styles["itinerary_sub"] = ParagraphStyle(
        "itinerary_sub", parent=base,
        fontName="Helvetica", fontSize=9,
        textColor=COLOR_GREY_TEXT, alignment=TA_CENTER, spaceAfter=8
    )
    return styles


def format_date(date_str: str) -> str:
    """将 YYYY-MM-DD 转为 'Month DD, YYYY' 格式"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%B %d, %Y")
    except:
        return date_str


def escape_text(text: str) -> str:
    """转义reportlab特殊字符"""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def make_translation_table(
    fields: List[tuple],
    col_widths: List[float],
    styles,
    header_row: bool = True
) -> Table:
    """
    fields: list of (field_en, text_cn, translation_en)
            第一行可以是表头 (field_en, text_cn, translation_en)
    """
    if header_row:
        data = [["Field (English)", "中文原文", "English Translation"]]
        start_row = 0
    else:
        data = []
        start_row = -1

    for item in fields:
        if header_row and len(data) == 1 and len(item) == 3:
            # items are (en, cn, tr) tuples
            pass
        data.append(list(item))

    table = Table(data, colWidths=col_widths, repeatRows=1 if header_row else 0)
    ts = [
        # 表头样式
        ("BACKGROUND", (0, 0), (-1, 0 if header_row else -1), COLOR_MID_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0 if header_row else -1), COLOR_WHITE),
        ("FONTNAME", (0, 0), (-1, 0 if header_row else -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0 if header_row else -1), 8),
        ("ALIGN", (0, 0), (-1, 0 if header_row else -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # 数据行样式
        ("FONTNAME", (0, 1 if header_row else 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1 if header_row else 0), (-1, -1), 8),
        ("ALIGN", (0, 1 if header_row else 0), (0, -1), "CENTER"),
        ("ALIGN", (1, 1 if header_row else 0), (-1, -1), "LEFT"),
        # 中文原文列
        ("FONTNAME", (1, 1 if header_row else 0), (1, -1), "Helvetica-Bold"),
        # 边框
        ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("ROWBACKGROUNDS",
         (0, 1 if header_row else 0), (-1, -1),
         [COLOR_WHITE, COLOR_ALT_ROW]),
        # 垂直对齐
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    table.setStyle(TableStyle(ts))
    return table


def add_translator_footer(story, styles):
    """在story末尾添加翻译者标注"""
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER))
    story.append(Paragraph(
        f"Translated by: {styles['_translator_name']} | {styles['_translator_cert']}",
        styles["translator"]
    ))


# ─────────────────────────────────────────────────────────────
# 文档生成函数
# ─────────────────────────────────────────────────────────────

def doc_national_id_card(args, styles, output_dir) -> str:
    """身份证翻译件"""
    output_path = os.path.join(output_dir, "02_national_id_身份证.pdf")

    # 虚构示例数据 - 不得使用真实个人信息
    # 字段：(英文标签, 中文原文, 英文翻译)
    # 使用占位符，用户生成后自行替换
    fields = [
        ("Name", "[姓名]", "[APPLICANT_NAME]"),
        ("Gender", "男", "Male"),
        ("Ethnic Group", "汉", "Han"),
        ("Date of Birth", "[出生日期]", "[DATE_OF_BIRTH]"),
        ("Address", "[住址]", "[CURRENT_ADDRESS]"),
        ("Citizen ID No.", "[身份证号]", "[NATIONAL_ID_NUMBER]"),
        ("Issuing Authority", "北京市公安局XX分局",
         "XX Branch of Beijing Municipal Public Security Bureau"),
        ("Valid Period", "2019.04.03—2029.04.03",
         "From April 03, 2019 to April 03, 2029"),
    ]

    # 分组：正面(前6项) + 背面(后2项)
    front_fields = fields[:6]
    back_fields = fields[6:]

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=20*mm
    )

    story = []
    # 正面
    story.append(Paragraph("Page 1 — Front Side (正面)", styles["section"]))
    story.append(Spacer(1, 4*mm))

    # 左侧占位提示 + 右侧表格
    # A4横向布局用表格模拟：左=图片区，右=表格区
    # 这里因为没有实际图片，用表格占位
    col_w = [95*mm, 100*mm]  # 左原文区，右译本区
    front_data = [["Original Document (原件)", "English Translation (英文译本)"]]
    for en, cn, tr in front_fields:
        front_data.append([cn, tr])

    front_table = Table(front_data, colWidths=col_w)
    front_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MID_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ALT_ROW]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    # 右侧说明：实际使用时左侧应为原件图片
    right_note = Table(
        [["← Please attach original ID card photo here"]],
        colWidths=[100*mm]
    )
    right_note.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_ALT_ROW),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_GREY_TEXT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 40),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 40),
    ]))

    # 组合左右布局
    layout_table = Table([[front_table, right_note]], colWidths=[95*mm, 100*mm])
    layout_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
    ]))
    story.append(layout_table)

    story.append(PageBreak())

    # 背面
    story.append(Paragraph("Page 2 — Back Side (背面)", styles["section"]))
    story.append(Spacer(1, 4*mm))

    back_data = [["Original Document (原件)", "English Translation (英文译本)"]]
    for en, cn, tr in back_fields:
        back_data.append([cn, tr])

    back_table = Table(back_data, colWidths=col_w)
    back_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MID_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ALT_ROW]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(back_table)

    add_translator_footer(story, styles)

    doc.build(story)
    print(f"[OK] 02_national_id_身份证.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_household_registration(args, styles, output_dir) -> str:
    """户口本翻译件"""
    output_path = os.path.join(output_dir, "04_household_register_户口本.pdf")

    # 虚构示例数据
    fields = [
        ("Name", "[姓名]", "[APPLICANT_NAME]"),
        ("Place of Birth", "北京市", "Beijing"),
        ("Gender", "男", "Male"),
        ("Native Place", "北京市朝阳区", "Chaoyang District, Beijing"),
        ("Ethnic Group", "汉", "Han"),
        ("Date of Birth", "[出生日期]", "[DATE_OF_BIRTH]"),
        ("Religion", "无", "None"),
        ("ID Card No.", "[身份证号]", "[NATIONAL_ID_NUMBER]"),
        ("Height", "175cm", "175cm"),
        ("Education", "大学本科", "Bachelor's Degree"),
        ("Marital Status", "未婚", "Single"),
        ("Military Status", "未服兵役", "Not Served"),
        ("Place of Work", "[工作单位]", "[EMPLOYER_NAME]"),
        ("Occupation", "[职业]", "[JOB_TITLE]"),
        ("Blood Type", "O型", "Type O"),
        ("Household Type", "集体户", "Collective Household"),
        ("Head of Household", "[户主姓名]", "[HEAD_OF_HOUSEHOLD]"),
        ("Address", "[住址]", "[CURRENT_ADDRESS]"),
    ]

    col_widths = [55*mm, 65*mm, 65*mm]

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=20*mm
    )

    story = []
    story.append(Paragraph("Household Register Translation (户口本翻译件)", styles["section"]))
    story.append(Spacer(1, 4*mm))
    table = make_translation_table(fields, col_widths, styles)
    story.append(table)
    add_translator_footer(story, styles)
    doc.build(story)

    print(f"[OK] 04_household_register_户口本.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_employment_verification(args, styles, output_dir) -> str:
    """在职证明及营业执照"""
    output_path = os.path.join(output_dir, "03_employment_verification_在职证明.pdf")

    # 虚构示例数据 - 营业执照字段
    biz_fields = [
        ("Unified Social Credit Code", "[统一社会信用代码]", "[UNIFIED_SOCIAL_CREDIT_CODE]"),
        ("Enterprise Name", "[企业名称]",
         "[COMPANY_NAME]"),
        ("Enterprise Type", "有限责任公司",
         "Limited Liability Company"),
        ("Legal Representative", "[法人代表]", "[LEGAL_REPRESENTATIVE]"),
        ("Date of Establishment", "[成立日期]", "[DATE]"),
        ("Address", "[企业地址]",
         "[COMPANY_ADDRESS]"),
        ("Registration Authority", "[登记机关]",
         "[REGISTRATION_AUTHORITY]"),
        ("Date of Issue", "[签发日期]", "[DATE]"),
    ]

    # 虚构示例数据 - 在职证明字段
    emp_fields = [
        ("Employee Name", "[姓名]", "[APPLICANT_NAME]"),
        ("Gender", "男", "Male"),
        ("Date of Birth", "[出生日期]", "[DATE_OF_BIRTH]"),
        ("ID Number", "[身份证号]", "[NATIONAL_ID_NUMBER]"),
        ("Employer", "[工作单位]", "[EMPLOYER_NAME]"),
        ("Department", "[部门]", "[DEPARTMENT]"),
        ("Position", "[职位]", "[JOB_TITLE]"),
        ("Employment Start Date", "[入职日期]", "[DATE]"),
        ("Leave Approved",
         "是，确认请假前往新西兰旅游",
         "Yes, leave approved for travel to New Zealand"),
        ("Employer Contact", "[联系电话] / [联系邮箱]",
         "[PHONE] / [EMAIL]"),
    ]

    col_widths = [55*mm, 65*mm, 65*mm]

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=20*mm
    )

    story = []

    # Section 1: Employment Certificate (在职证明在前)
    story.append(Paragraph("Part 1: Employment Verification Letter (在职证明)", styles["section"]))
    story.append(Spacer(1, 4*mm))
    story.append(make_translation_table(emp_fields, col_widths, styles))

    story.append(Spacer(1, 8*mm))

    # Section 2: Business License (营业执照在后)
    story.append(Paragraph("Part 2: Business License (营业执照)", styles["section"]))
    story.append(Spacer(1, 4*mm))
    story.append(make_translation_table(biz_fields, col_widths, styles))

    add_translator_footer(story, styles)
    doc.build(story)

    print(f"[OK] 03_employment_verification_在职证明.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_bank_statement(args, styles, output_dir) -> str:
    """银行流水（示意版，实际需要用户提供真实流水）"""
    output_path = os.path.join(output_dir, "05_bank_statements_银行证明.pdf")

    # 示例数据（示意）
    sample_transactions = [
        ("15 Jan 2024", "Salary / Payroll", "+50,000.00", "52,345.67"),
        ("16 Jan 2024", "Shopping / Purchase", "-1,200.00", "51,145.67"),
        ("18 Jan 2024", "Dining", "-350.00", "50,795.67"),
        ("20 Jan 2024", "Transportation", "-120.00", "50,675.67"),
        ("22 Jan 2024", "Online Payment", "-2,500.00", "48,175.67"),
        ("25 Jan 2024", "Transfer In", "+5,000.00", "53,175.67"),
        ("28 Jan 2024", "Utility Bill", "-480.00", "52,695.67"),
    ]

    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=15*mm, bottomMargin=20*mm
    )

    story = []
    story.append(Paragraph("Bank Statement — China Merchants Bank (招商银行流水)", styles["section"]))
    story.append(Spacer(1, 3*mm))

    # 摘要行
    summary_data = [
        ["Account Holder:", "[APPLICANT_NAME]", "Account No.:", "6225 **** **** 1234"],
        ["Statement Period:", "Jan 1, 2024 – Jan 31, 2024", "Currency:", "CNY"],
    ]
    summary_table = Table(summary_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_DARK_TEXT),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4*mm))

    # 交易明细表
    trans_data = [["Date", "Transaction Description", "Amount (CNY)", "Balance (CNY)"]]
    for row in sample_transactions:
        trans_data.append(list(row))

    col_widths = [35*mm, 80*mm, 35*mm, 35*mm]
    trans_table = Table(trans_data, colWidths=col_widths, repeatRows=1)
    trans_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ALT_ROW]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # 金额正负颜色
        ("TEXTCOLOR", (2, 1), (2, -1), colors.HexColor("#1A7A1A")),
        ("TEXTCOLOR", (2, 2), (2, 2), colors.HexColor("#CC0000")),
    ]))
    story.append(trans_table)

    story.append(Spacer(1, 5*mm))

    # 统计行
    stats_data = [
        ["Total Credits:", "+55,000.00", "Total Debits:", "-4,650.00"],
        ["Ending Balance:", "52,695.67", "", ""],
    ]
    stats_table = Table(stats_data, colWidths=[40*mm, 40*mm, 40*mm, 60*mm])
    stats_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("SPAN", (1, 1), (3, 1)),
    ]))
    story.append(stats_table)

    story.append(Spacer(1, 4*mm))
    note = Paragraph(
        "<i>Note: This is a sample bank statement. Please replace with your actual bank statements. "
        "The original Chinese bank statement should be placed on the LEFT side of each page, "
        "with this English translation on the RIGHT side.</i>",
        ParagraphStyle("note", parent=styles["Normal"], fontSize=7,
                      textColor=COLOR_GREY_TEXT, fontName="Helvetica-Oblique")
    )
    story.append(note)
    add_translator_footer(story, styles)

    doc.build(story)
    print(f"[OK] 05_bank_statements_银行证明.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_travel_itinerary(args, styles, output_dir) -> str:
    """单次旅行计划 - 香港出发，使用真实航班号"""
    output_path = os.path.join(output_dir, "06_travel_itinerary_旅行计划.pdf")

    # 香港出发真实航班信息
    # CX120: 香港→奥克兰 (Cathay Pacific, 约11小时)
    # CZ601: 香港→奥克兰 (China Southern, 约11小时)
    # NZ555: 奥克兰→基督城 (Air New Zealand, 约1小时25分)
    # CX124: 奥克兰→基督城 (Cathay Pacific)
    # CZ618: 奥克兰→广州 (China Southern)
    # 返回航班使用 CX111/CZ618 等

    # 南岛8日行程 (香港出发)
    south_island = [
        ("1", "Oct 1", "08:30", "HKG → CHC",
         "CX124 departs HKG 08:30 → Arrive CHC 19:30 (via AKL)",
         "Christchurch Hotel Sudomo ★★★", "Cathay Pacific CX124"),
        ("2", "Oct 2", "09:00", "Christchurch",
         "Christchurch Botanic Gardens, punting on Avon River, Cathedral Square",
         "Christchurch Hotel Sudomo ★★★", "Walk / Local Bus"),
        ("3", "Oct 3", "08:30", "CHC → FJ",
         "Drive via Arthur's Pass, Otira Gorge, Punakaiki Pancake Rocks",
         "Scenic Hotel Franz Josef Glacier ★★★", "InterCity Bus"),
        ("4", "Oct 4", "09:00", "Franz Josef",
         "Franz Josef Glacier guided walk, Glacier hot pools evening",
         "Scenic Hotel Franz Josef Glacier ★★★", "Shuttle Bus"),
        ("5", "Oct 5", "08:00", "FJ → Queenstown",
         "Via Wanaka, Blue Pools, Lake Hawea scenic stop",
         "Copthorne Hotel & Apartments ★★★", "InterCity Bus"),
        ("6", "Oct 6", "09:00", "Queenstown",
         "Skyline Gondola, Bob's Peak, Ferg Burger, Lake Wakatipu walk",
         "Copthorne Hotel & Apartments ★★★", "Walk / Taxi"),
        ("7", "Oct 7", "09:00", "Queenstown",
         "Milford Sound day trip (Te Anau, Mirror Lakes, Fjordland)",
         "Copthorne Hotel & Apartments ★★★", "Day Tour Bus"),
        ("8", "Oct 8", "10:00", "CHC → HKG",
         "Morning drive to CHC, CZ618 departs CHC 13:30 → Arrive HKG 19:00",
         "N/A", "China Southern CZ618"),
    ]

    # 北岛8日行程 (香港出发)
    north_island = [
        ("1", "Oct 1", "08:30", "HKG → AKL",
         "CX120 departs HKG 08:30 → Arrive AKL 19:30",
         "Auckland City Hotel ★★★★", "Cathay Pacific CX120"),
        ("2", "Oct 2", "09:00", "Auckland",
         "Sky Tower, Viaduct Harbour, Queen Street shopping, Auckland Museum",
         "Auckland City Hotel ★★★★", "Walk / Local Bus"),
        ("3", "Oct 3", "08:00", "AKL → Rotorua",
         "Scenic drive via Cambridge, Hobbiton movie set optional stop",
         "Sudima Lake Rotorua ★★★★", "InterCity Bus"),
        ("4", "Oct 4", "09:00", "Rotorua",
         "Te Puia Geothermal Park, Redwood Forest walk, Polynesian Spa evening",
         "Sudima Lake Rotorua ★★★★", "Taxi / Walk"),
        ("5", "Oct 5", "08:30", "Rotorua → Taupo",
         "Huka Falls, Aratiatia Dam, Lake Taupo sunset cruise",
         "The Lake Hotel Taupo ★★★", "InterCity Bus"),
        ("6", "Oct 6", "09:00", "Taupo → Wellington",
         "Via Tongariro National Park viewpoint, scenic mountain drive",
         "Travelodge Wellington ★★★", "InterCity Bus"),
        ("7", "Oct 7", "09:00", "Wellington",
         "Te Papa Museum, Botanic Gardens, Oriental Parade, Cuba Street",
         "Travelodge Wellington ★★★", "Walk / Local Bus"),
        ("8", "Oct 8", "10:00", "AKL → HKG",
         "Transfer to AKL, CX111 departs AKL 14:00 → Arrive HKG 19:30",
         "N/A", "Cathay Pacific CX111"),
    ]

    # 南北岛12日行程
    both_island = [
        ("1", "Oct 1", "08:30", "HKG → AKL",
         "CX120 departs HKG 08:30 → Arrive AKL 19:30",
         "Auckland City Hotel ★★★★", "Cathay Pacific CX120"),
        ("2", "Oct 2", "09:00", "Auckland",
         "Sky Tower, Viaduct Harbour, Kelly Tarlton's Aquarium",
         "Auckland City Hotel ★★★★", "Walk / Bus"),
        ("3", "Oct 3", "08:00", "AKL → Rotorua",
         "Te Puia Geothermal Park, Maori cultural experience",
         "Sudima Lake Rotorua ★★★★", "InterCity Bus"),
        ("4", "Oct 4", "09:00", "Rotorua → Wellington",
         "Drive via National Park, arrive Wellington evening",
         "Travelodge Wellington ★★★", "InterCity Bus"),
        ("5", "Oct 5", "09:00", "Wellington",
         "Te Papa Museum, Cable Car, Botanic Gardens",
         "Travelodge Wellington ★★★", "Walk / Bus"),
        ("6", "Oct 6", "07:00", "WLG → CHC",
         "NZ247 departs WLG 07:30 → Arrive CHC 08:55",
         "Christchurch Hotel Sudomo ★★★", "Air New Zealand NZ247"),
        ("7", "Oct 7", "09:00", "Christchurch",
         "Botanic Gardens, punting on Avon, Christchurch Cathedral",
         "Christchurch Hotel Sudomo ★★★", "Walk"),
        ("8", "Oct 8", "08:00", "CHC → FJ",
         "Arthur's Pass, Otira Gorge, Punakaiki Pancake Rocks",
         "Scenic Hotel Franz Josef Glacier ★★★", "InterCity Bus"),
        ("9", "Oct 9", "09:00", "Franz Josef",
         "Franz Josef Glacier walk, hot pools evening",
         "Scenic Hotel Franz Josef Glacier ★★★", "Shuttle"),
        ("10", "Oct 10", "08:00", "FJ → Queenstown",
         "Wanaka, Blue Pools, Lake Hawea",
         "Copthorne Hotel & Apartments ★★★", "InterCity Bus"),
        ("11", "Oct 11", "09:00", "Queenstown",
         "Skyline Gondola, Milford Sound optional",
         "Copthorne Hotel & Apartments ★★★", "Walk / Tour"),
        ("12", "Oct 12", "10:00", "CHC → HKG",
         "Morning drive to CHC, CX124 departs CHC 14:00 → Arrive HKG 19:30",
         "N/A", "Cathay Pacific CX124"),
    ]

    island_data = {"south": south_island, "north": north_island, "both": both_island}
    island_names = {"south": "South Island (8 Days)", "north": "North Island (8 Days)", "both": "North & South Island (12 Days)"}
    itinerary = island_data.get(args.island, south_island)

    island_name = island_names.get(args.island, "South Island")

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    story = []
    story.append(Paragraph("Trip Itinerary — New Zealand (香港出发)", styles["itinerary_header"]))
    story.append(Paragraph(f"{island_name}", styles["itinerary_sub"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_MID_BLUE, spaceAfter=6))

    # 添加航班信息说明
    flight_note = Paragraph(
        "<b>Flight Information / 航班信息:</b> CX120/CX124 (HKG→AKL/CHC), CZ618 (CHC→HKG), NZ247 (WLG→CHC) | "
        "All flights depart from Hong Kong International Airport (HKG)",
        ParagraphStyle("flight_note", parent=styles["Normal"], fontSize=7,
                      textColor=COLOR_GREY_TEXT, spaceAfter=6)
    )
    story.append(flight_note)

    header = [["Day", "Date", "Time", "City / Route", "Activities & Sightseeing", "Accommodation", "Transport"]]
    col_widths = [10*mm, 18*mm, 15*mm, 32*mm, 58*mm, 30*mm, 22*mm]

    table_data = header + itinerary
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 6.5),
        ("ALIGN", (0, 1), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ALT_ROW]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        # 航班行高亮
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#E8F4FD")),  # Day 1
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F4FD")),  # Last day
    ]))
    story.append(table)

    doc.build(story)
    print(f"[OK] 06_travel_itinerary_旅行计划.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_statement_multiple_journeys(args, styles, output_dir) -> str:
    """多次入境说明信"""
    output_path = os.path.join(output_dir, "07_statement_multiple_journeys_入境陈述.pdf")

    applicant_name = args.name or "[APPLICANT_NAME]"
    passport = args.passport or "[PASSPORT_NUMBER]"
    national_id = args.id_num or "[NATIONAL_ID_NUMBER]"
    phone = args.phone or "[PHONE_NUMBER]"
    email = args.email or "[EMAIL_ADDRESS]"
    job_title = args.job_title or "[JOB_TITLE]"
    employer = args.employer or "[EMPLOYER_NAME]"

    content = f"""
To Whom It May Concern,

Re: Statement of Intended Multiple Journeys to New Zealand

1. Purpose
This statement explains my intention to make multiple journeys to New Zealand over the next three years
(2026–2028) as supporting evidence for my multiple-entry visitor visa application.

2. Applicant Information
  Full Name:          {applicant_name}
  Passport Number:    {passport}
  Nationality:        People's Republic of China
  National ID No.:    {national_id}
  Contact:            {phone} | {email}

3. Reasons for Multiple Visits
3.1 Distinct North Island & South Island Experiences
New Zealand's two islands offer dramatically different landscapes. The North Island features volcanic
plateaus, geothermal areas, and rich Maori cultural heritage (Auckland, Rotorua, Wellington), while
the South Island is celebrated for its Southern Alps, glaciers, fjords, and pristine wilderness
(Queenstown, Milford Sound, Christchurch). Multiple trips allow thorough and relaxed exploration
of each region.

3.2 Seasonal Travel Plans
Rather than rushing through many attractions in a single trip, I prefer unhurried journeys that allow
for deeper cultural immersion and genuine rest. Multiple shorter trips are far more enjoyable and
meaningful than a single rushed visit.

3.3 Proven International Travel Experience
I have previously traveled to Italy, Switzerland, Singapore, South Korea, Egypt, Indonesia, and
Thailand. These experiences demonstrate my understanding of international travel, visa compliance,
and cultural awareness.

4. Financial Resources
I am fully financially capable of supporting all travel expenses for multiple visits to New Zealand:
  • Real Estate Holdings: Full ownership of residential property in China, demonstrating long-term
    financial commitment and strong ties to my home country.
  • Stable Employment: {job_title} at {employer}, with stable income and long-term career prospects.
  • Bank Statements: Consistently sufficient balance in my personal accounts (see attached bank statements).

5. Strong Ties to Home Country
  • Full-time employment at a leading Chinese technology company
  • Ownership of residential property in Shenzhen
  • Extensive family and social connections in China
  • No intention to overstay or settle in New Zealand

6. Planned Visits
Please refer to the attached "Multiple Journey Plan" document for detailed itinerary of my planned
trips over the next three years.

7. Declaration
I, {applicant_name}, holder of Passport No. {passport}, hereby declare that all information provided
in this statement is true, accurate, and complete. I fully understand the conditions of a multiple-entry
visa and commit to complying with all New Zealand immigration laws. I undertake to depart New Zealand
before the expiry of each authorized stay and maintain sufficient financial resources for each visit.

Sincerely,

{applicant_name}
{job_title}
{format_date(date.today().strftime('%Y-%m-%d')) if hasattr(args, 'date') else '[DATE]'}

Contact: {phone} | {email}
"""

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=60, rightMargin=60,
        topMargin=60, bottomMargin=60
    )

    story = []
    styles_letter = ParagraphStyle(
        "letter", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10,
        leading=15, spaceAfter=8,
        alignment=TA_JUSTIFY
    )
    styles_letter_title = ParagraphStyle(
        "letter_title", parent=styles_letter,
        fontName="Helvetica-Bold", fontSize=12,
        alignment=TA_CENTER, spaceAfter=16
    )

    for para in content.strip().split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("To Whom"):
            # 标题
            story.append(Paragraph("STATEMENT OF INTENDED MULTIPLE JOURNEYS TO NEW ZEALAND",
                                   styles_letter_title))
            continue
        if para.startswith("Re:"):
            story.append(Paragraph(para.replace("Re:", "<b>Re:</b>"), styles_letter))
            continue
        # 数字标号标题
        import re as re2
        if re2.match(r"^\d+\.", para):
            lines = para.split("\n")
            title = lines[0]
            body = "\n".join(lines[1:]).strip()
            story.append(Paragraph(f"<b>{title}</b>", styles_letter))
            if body:
                story.append(Paragraph(body.replace("\n  ", "<br/>"), styles_letter))
        else:
            story.append(Paragraph(para.replace("\n", "<br/>"), styles_letter))
        story.append(Spacer(1, 4))

    doc.build(story)
    print(f"[OK] 07_statement_multiple_journeys_入境陈述.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_multiple_journey_plan(args, styles, output_dir) -> str:
    """多次旅行计划"""
    output_path = os.path.join(output_dir, "08_subsequent_journey_plan_后续旅行计划.pdf")

    # 2027 南岛 + 北岛
    trip_2027_north = [
        ("1", "May 1, 2027", "Shanghai → Auckland",
         "Flight to Auckland, arrival", "Auckland Airport", "Flight MU779"),
        ("2", "May 2, 2027", "Auckland",
         "Sky Tower, Viaduct Harbour, Auckland CBD", "Auckland", "Local Bus / Taxi"),
        ("3", "May 3, 2027", "Auckland → Rotorua",
         "Drive to Rotorua, Te Puia Geothermal Park", "Rotorua", "Intercity Bus"),
        ("4", "May 4, 2027", "Rotorua",
         "Redwoods Forest, Polynesian Spa, Lake Rotorua", "Rotorua", "Taxi / Walking"),
        ("5", "May 5, 2027", "Rotorua → Taupo",
         "Drive to Taupo, Huka Falls, Lake Taupo", "Taupo", "Intercity Bus"),
        ("6", "May 6, 2027", "Taupo → Wellington",
         "Drive to Wellington, waterfront walk", "Wellington", "Intercity Bus"),
        ("7", "May 7, 2027", "Wellington",
         "Te Papa Museum, Botanic Gardens, Oriental Parade", "Wellington", "Local Bus / Taxi"),
        ("8", "May 8, 2027", "Wellington → Christchurch",
         "Flight to Christchurch, departure", "N/A", "Flight NZ529"),
    ]

    # 2028 南岛
    trip_2028_south = [
        ("1", "Mar 10, 2028", "Shanghai → Queenstown",
         "Flight to Queenstown, arrival", "Queenstown", "Flight MU779"),
        ("2", "Mar 11, 2028", "Queenstown",
         "Skyline Gondola, Bob's Peak, town exploration", "Queenstown", "Walking / Taxi"),
        ("3", "Mar 12, 2028", "Queenstown → Milford Sound",
         "Drive to Milford Sound, scenic cruise", "Te Anau", "Intercity Bus"),
        ("4", "Mar 13, 2028", "Milford Sound → Dunedin",
         "Drive to Dunedin, Octagon, Otago Peninsula", "Dunedin", "Intercity Bus"),
        ("5", "Mar 14, 2028", "Dunedin",
         "Larnach Castle, Botanic Garden, Signal Hill", "Dunedin", "Local Bus / Taxi"),
        ("6", "Mar 15, 2028", "Dunedin → Lake Tekapo",
         "Drive to Lake Tekapo, Church of the Good Shepherd", "Lake Tekapo", "Intercity Bus"),
        ("7", "Mar 16, 2028", "Lake Tekapo → Christchurch → Shenzhen",
         "Drive to Christchurch, departure", "N/A", "Flight CZ618"),
    ]

    col_widths = [12*mm, 25*mm, 35*mm, 50*mm, 28*mm, 25*mm]

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    story = []

    for trip_name, trip_data in [
        ("Trip 1 — May 2027 (North Island + South Island)", trip_2027_north),
        ("Trip 2 — March 2028 (South Island)", trip_2028_south),
    ]:
        story.append(Paragraph(f"Multiple Journey Plan — {trip_name}",
                               styles["itinerary_header"]))
        story.append(Paragraph("New Zealand", styles["itinerary_sub"]))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=COLOR_MID_BLUE, spaceAfter=4))

        table_data = [["Day", "Date", "City", "Activities", "Accommodation", "Transportation"]]
        table_data.extend(trip_data)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 7.5),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ALT_ROW]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(table)
        if trip_name != "Trip 2 — March 2028 (South Island)":
            story.append(PageBreak())

    doc.build(story)
    print(f"[OK] 08_subsequent_journey_plan_后续旅行计划.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_proof_of_assets(args, styles, output_dir) -> str:
    """资产证明（房产证等）"""
    output_path = os.path.join(output_dir, "10_proof_of_assets_资产证明.pdf")

    property_fields = [
        ("Certificate Number", "[PROPERTY_CERT_NUMBER]", "[PROPERTY_CERT_NUMBER]"),
        ("Property Address", "[PROPERTY_ADDRESS]", "[PROPERTY_ADDRESS]"),
        ("Owner Name", "[APPLICANT_NAME]", "[APPLICANT_NAME]"),
        ("Document Type", "不动产权证书", "Certificate of Real Estate Ownership"),
        ("Land Type", "国有建设用地使用权", "State-owned Construction Land Use Rights"),
        ("Building Area", "约XX.XX平方米", "Approximately XX.XX sqm"),
        ("Usage", "住宅", "Residential"),
        ("Issuing Authority", "深圳市规划和自然资源局",
         "Shenzhen Municipal Bureau of Planning and Natural Resources"),
    ]

    loan_fields = [
        ("Certificate Type", "个人贷款结清证明", "Certificate of Loan Settlement"),
        ("Borrower Name", "[APPLICANT_NAME]", "[APPLICANT_NAME]"),
        ("ID Number", "[NATIONAL_ID_NUMBER]", "[NATIONAL_ID_NUMBER]"),
        ("Loan Institution", "[BANK_NAME]", "[BANK_NAME]"),
        ("Loan Amount", "人民币XX万元", "RMB XX,000"),
        ("Settlement Date", "[DATE]", "[DATE]"),
        ("Outstanding Balance", "0.00", "0.00"),
        ("Issuing Authority", "[BANK_NAME]", "[BANK_NAME]"),
    ]

    col_widths = [55*mm, 65*mm, 65*mm]

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=20*mm
    )

    story = []
    story.append(Paragraph("Part 1: Property Ownership Certificate (房产证)", styles["section"]))
    story.append(Spacer(1, 4*mm))
    story.append(make_translation_table(property_fields, col_widths, styles))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Part 2: Loan Settlement Certificate (贷款结清证明)", styles["section"]))
    story.append(Spacer(1, 4*mm))
    story.append(make_translation_table(loan_fields, col_widths, styles))

    add_translator_footer(story, styles)
    doc.build(story)

    print(f"[OK] 10_proof_of_assets_资产证明.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def doc_passport(args, styles, output_dir, image_dir: str = None) -> str:
    """
    护照 - 直接将护照图片合并为A4横向PDF

    每张图片一页，自动EXIF修正方向，压缩到最长边1200px。
    如果 image_dir 提供，扫描其中的护照图片合并。
    """
    from PIL import Image, ImageOps
    import io
    output_path = os.path.join(output_dir, "01_passport_护照.pdf")

    # 收集护照图片
    passport_images = []
    if image_dir and os.path.isdir(image_dir):
        img_exts = ('.jpg', '.jpeg', '.png', '.heic', '.JPG', '.JPEG', '.PNG', '.HEIC')
        for f in sorted(os.listdir(image_dir)):
            if f.lower().endswith(img_exts):
                # 匹配护照/签证文件
                passport_images.append(os.path.join(image_dir, f))

    if passport_images:
        # 有真实图片 → 生成图片PDF
        output_pdf = fitz.open()
        for img_path in passport_images:
            try:
                pil_img = Image.open(img_path)
                pil_img = ImageOps.exif_transpose(pil_img)  # 关键：EXIF方向修正
                # 缩放到最长边1200px
                w, h = pil_img.size
                max_s = 1200
                if max(w, h) > max_s:
                    ratio = max_s / max(w, h)
                    pil_img = pil_img.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)
                # 转为RGB（RGBA→RGB）
                if pil_img.mode == 'RGBA':
                    bg = Image.new('RGB', pil_img.size, (255,255,255))
                    bg.paste(pil_img, pil_img)
                    pil_img = bg
                elif pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                # 写入PDF页面（A4横向）
                buf = io.BytesIO()
                pil_img.save(buf, format='JPEG', quality=80)
                buf.seek(0)
                img_doc = fitz.open("jpg", buf.read())
                pdfbytes = img_doc.convert_to_pdf()
                img_doc.close()
                img_pdf = fitz.open("pdf", pdfbytes)
                # 旋转页面使其适应A4横向
                page = img_pdf[0]
                r = page.rect
                # 如果图片是竖版，不旋转；横向图片适应A4横向
                # A4横向 = 842x595
                output_pdf.insert_pdf(img_pdf)
            except Exception as e:
                print(f"  [WARN] Failed to process {img_path}: {e}")
        output_pdf.save(output_path)
        output_pdf.close()
    else:
        # 无图片 → 生成占位说明页（A4横向）
        doc = SimpleDocTemplate(
            output_path, pagesize=landscape(A4),
            leftMargin=10*mm, rightMargin=10*mm,
            topMargin=12*mm, bottomMargin=15*mm
        )
        story = []
        story.append(Paragraph("Passport — NZ Visa Application", styles["section"]))
        story.append(Spacer(1, 4*mm))

        left_placeholder = Paragraph(
            "<b>Place Passport Scan Here</b><br/><br/>"
            "Please scan your passport:<br/>"
            "- Page 1: Personal Information Page<br/>"
            "- Page 2+: All Visa Pages<br/><br/>"
            "Ensure clear, upright scans.",
            ParagraphStyle("placeholder", parent=styles["Normal"],
                          fontSize=10, alignment=TA_CENTER,
                          leading=15, textColor=COLOR_GREY_TEXT)
        )
        left_table = Table([[left_placeholder]], colWidths=[95*mm])
        left_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_ALT_ROW),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 30),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
        ]))

        passport_fields = [
            ("Passport Number", "护照号码"),
            ("Name (Chinese)", "姓名"),
            ("Name (English)", "姓名（英文）"),
            ("Nationality", "国籍"),
            ("Date of Birth", "出生日期"),
            ("Place of Birth", "出生地"),
            ("Sex / Gender", "性别"),
            ("Date of Issue", "签发日期"),
            ("Date of Expiry", "有效期至"),
            ("Issuing Authority", "签发机关"),
        ]
        header_row = [["Field / 字段", "Note / 说明"]]
        right_data = header_row + [[p[0], p[1]] for p in passport_fields]
        right_table = Table(right_data, colWidths=[40*mm, 55*mm])
        right_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_MID_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ALT_ROW]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        layout = Table([[left_table, right_table]], colWidths=[95*mm, 95*mm])
        layout.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (1, 0), (1, 0), 6),
        ]))
        story.append(layout)

        note = Paragraph(
            "<b>Note:</b> Passport does not require translation. Place clear passport scans (info page + all visa pages) on the left.",
            ParagraphStyle("note", parent=styles["Normal"], fontSize=7, textColor=COLOR_GREY_TEXT)
        )
        story.append(Spacer(1, 4*mm))
        story.append(note)
        doc.build(story)

    print(f"[OK] 01_passport_护照.pdf ({os.path.getsize(output_path)/1024:.1f} KB)")
    return output_path


def generate_manifest(output_dir: str, args, generated_files: List[str]):
    """生成材料清单"""
    manifest_path = os.path.join(output_dir, "_MANIFEST.txt")

    trip_type_str = "Multiple Entry" if args.trip_type == "multiple" else "Single Entry"
    island_str = {"south": "South Island", "north": "North Island", "both": "North & South Island"}.get(args.island, "South Island")

    lines = [
        "=" * 60,
        "新西兰签证材料清单 / New Zealand Visa Documents Checklist",
        "=" * 60,
        f"申请类型 / Application Type: {trip_type_str}",
        f"目的地 / Destination: {island_str}",
        f"生成日期 / Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
        "【必填材料 / Required Documents】",
        "",
        "# | 文件名(EN)                                         | 说明                                              |",
        "---|----------------------------------------------------|---------------------------------------------------|",
    ]

    required = [
        ("01_passport_护照.pdf", "护照个人信息页（直接上传原版，无需翻译）"),
        ("02_national_id_身份证.pdf", "身份证翻译件（左原件/右译本，A4横向）"),
        ("03_employment_verification_在职证明.pdf", "在职证明+营业执照翻译件（左原件/右译本）"),
        ("04_household_register_户口本.pdf", "户口本翻译件（左原件/右译本）"),
        ("05_bank_statements_银行证明.pdf", "银行流水翻译件（所有页面逐一对应合并为一个PDF）"),
        ("06_travel_itinerary_旅行计划.pdf", "单次旅行计划（全英文行程表）"),
    ]

    if args.trip_type == "multiple":
        required += [
            ("07_statement_multiple_journeys_入境陈述.pdf", "多次入境说明信（仅多次入境）"),
            ("08_subsequent_journey_plan_后续旅行计划.pdf", "多次旅行计划（仅多次入境）"),
        ]

    for i, (fname, desc) in enumerate(required, 1):
        path = os.path.join(output_dir, fname)
        size_kb = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
        lines.append(f"{i:02d} | {fname:<55} | {desc} [{size_kb:.0f}KB]")

    lines += [
        "",
        "【可选材料 / Optional Documents】",
        "",
        "# | 文件名(EN)                                                     | 说明                                              |",
        "---|--------------------------------------------------------------|---------------------------------------------------|",
    ]

    optional = [
        ("10_proof_of_assets_资产证明.pdf", "资产证明（房产证等，左原件/右译本）"),
        ("attachment_1.pdf", "附件1（如有其他材料）"),
    ]

    for i, (fname, desc) in enumerate(optional, len(required) + 1):
        path = os.path.join(output_dir, fname)
        size_kb = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
        lines.append(f"{i:02d} | {fname:<50} | {desc} [{size_kb:.0f}KB]")

    lines += [
        "",
        "=" * 60,
        "【重要提醒】",
        "1. 所有[PLACEHOLDER]请替换为您的真实信息",
        "2. 左原件/右译本格式：原件在左（保持原始方向），译本在右（A4横向）",
        "3. 每份翻译件右下角标注翻译者信息",
        "4. 单个PDF文件请确保小于2MB",
        "5. 登录 https://www.immigration.govt.nz/new-zealand-visas 上传材料",
        "=" * 60,
    ]

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[OK] _MANIFEST.txt")


# ─────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate New Zealand Visitor Visa application PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # 基本信息（使用虚构占位符）
    parser.add_argument("--output-dir", default="./nz_visa_output",
                        help="Output directory (default: ./nz_visa_output)")
    parser.add_argument("--name", default="[APPLICANT_NAME]")
    parser.add_argument("--passport", default="[PASSPORT_NUMBER]")
    parser.add_argument("--id", dest="id_num", default="[NATIONAL_ID_NUMBER]")
    parser.add_argument("--dob", default="[DATE_OF_BIRTH]")
    parser.add_argument("--phone", default="[PHONE_NUMBER]")
    parser.add_argument("--email", default="[EMAIL_ADDRESS]")
    parser.add_argument("--address", default="[CURRENT_ADDRESS]")
    parser.add_argument("--employer", default="[EMPLOYER_NAME]")
    parser.add_argument("--job-title", default="[JOB_TITLE]")
    parser.add_argument("--date", default=date.today().strftime("%Y-%m-%d"))

    # 申请类型
    parser.add_argument("--trip-type", choices=["single", "multiple"],
                        default="single", help="单次或多次入境 (default: single)")
    parser.add_argument("--island", choices=["south", "north", "both"],
                        default="south", help="南岛/北岛/南北岛 (default: south)")

    # 翻译者信息（虚构示例）
    parser.add_argument("--translator-name", default="Professional Translation Services")
    parser.add_argument("--translator-cert", default="Certified Translator")

    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 初始化样式（注入翻译者信息）
    styles = make_styles()
    styles["_translator_name"] = args.translator_name
    styles["_translator_cert"] = args.translator_cert

    print(f"\nGenerating New Zealand Visa PDFs...")
    print(f"Output: {os.path.abspath(args.output_dir)}")
    print(f"Trip type: {args.trip_type} | Island: {args.island}")
    print()

    generated = []

    # 生成护照（01）
    generated.append(("01", "01_passport_护照.pdf", doc_passport(args, styles, args.output_dir)))

    # 生成身份证（02）
    generated.append(("02", "02_national_id_身份证.pdf", doc_national_id_card(args, styles, args.output_dir)))

    # 生成在职证明+营业执照（03）
    generated.append(("03", "03_employment_verification_在职证明.pdf", doc_employment_verification(args, styles, args.output_dir)))

    # 生成户口本（04）
    generated.append(("04", "04_household_register_户口本.pdf", doc_household_registration(args, styles, args.output_dir)))

    # 生成银行证明（05）
    generated.append(("05", "05_bank_statements_银行证明.pdf", doc_bank_statement(args, styles, args.output_dir)))

    # 生成旅行计划（06）
    generated.append(("06", "06_travel_itinerary_旅行计划.pdf", doc_travel_itinerary(args, styles, args.output_dir)))

    # 多次入境特有
    if args.trip_type == "multiple":
        generated.append(("07", "07_statement_multiple_journeys_入境陈述.pdf",
                          doc_statement_multiple_journeys(args, styles, args.output_dir)))
        generated.append(("08", "08_subsequent_journey_plan_后续旅行计划.pdf",
                          doc_multiple_journey_plan(args, styles, args.output_dir)))

    # 资产证明（10）
    generated.append(("10", "10_proof_of_assets_资产证明.pdf", doc_proof_of_assets(args, styles, args.output_dir)))

    # 生成清单
    generate_manifest(args.output_dir, args, generated)

    print(f"\nDone! {len(generated)} PDFs generated in {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
