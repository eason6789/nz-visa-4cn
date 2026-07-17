#!/usr/bin/env python3
"""
make_table_auto.py — 自动列宽表格生成器
根据单元格内容自动计算最佳列宽，避免长文本被截断或空间浪费。

适用场景: 银行流水交易明细、在职证明字段、户口本信息、营业执照等

Usage:
    from make_table_auto import make_table_auto
    table = make_table_auto(data, header=True, min_col_width=25*mm, max_col_width=80*mm)
"""

from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics


def make_table_auto(
    data,
    header=True,
    min_col_width=30 * mm,
    max_col_width=None,
    padding=8,
    cn_font_name="CN",
    color_dark_text="#1A1A1A",
    color_dark_blue="#1A3A5C",
    color_alt_row="#F5F7FA",
    color_border="#CCCCCC",
):
    """
    自动列宽表格生成 — 根据内容自动调整列宽

    Args:
        data: 表格数据，二维列表（每行一个列表）
        header: 第一行是否为表头
        min_col_width: 最小列宽 (pt)
        max_col_width: 最大列宽 (pt)，可选
        padding: 单元格内边距 (pt)
        cn_font_name: 中文字体名称
        color_dark_text: 正文文字颜色
        color_dark_blue: 表头背景色
        color_alt_row: 交替行背景色
        color_border: 网格线颜色

    Returns:
        reportlab.platypus.Table 实例
    """
    if not data or len(data) < 2:
        fallback_w = [50 * mm] * (len(data[0]) if data else 1)
        return Table(data, colWidths=fallback_w)

    num_cols = len(data[0])
    col_widths = []

    for col_idx in range(num_cols):
        max_width = min_col_width

        for row_idx, row in enumerate(data):
            if col_idx < len(row):
                cell_text = str(row[col_idx]) if row[col_idx] is not None else ""
                estimated_width = 0
                for char in cell_text:
                    if "一" <= char <= "鿿":
                        estimated_width += 9 * 1.2  # 中文字符略宽
                    else:
                        estimated_width += 5  # 英文/数字
                estimated_width += padding * 2
                max_width = max(max_width, estimated_width)

        if max_col_width:
            max_width = min(max_width, max_col_width)
        col_widths.append(max_width)

    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)

    # 构建表样式命令列表
    style_commands = [
        # 网格线
        ("GRID", (0, 0), (-1, -1), 0.4, color_border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    if header:
        # 表头样式
        style_commands += [
            ("BACKGROUND", (0, 0), (-1, 0), color_dark_blue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), cn_font_name),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ]

    # 交替行背景
    for row_idx in range(1 if header else 0, len(data)):
        if row_idx % 2 == 0:
            style_commands.append(
                ("BACKGROUND", (0, row_idx), (-1, row_idx), color_alt_row)
            )

    t.setStyle(TableStyle(style_commands))
    return t
