#!/usr/bin/env python3
"""
parse_bank_pdf.py — 银行流水PDF文字层解析器
解析招商银行等银行流水的文字层，按每列独占一行模式提取交易数据。

Usage:
    from parse_bank_pdf import parse_bank_pdf
    all_pages = parse_bank_pdf("boc_statement.pdf")
    for page_num, transactions in enumerate(all_pages):
        for date, currency, amount, balance, summary, counterparty in transactions:
            print(date, amount, summary)
"""

import re
import fitz


def parse_bank_pdf(pdf_path):
    """
    解析银行流水PDF的文字层，每列独占一行模式。

    银行流水PDF中，每列数据通常是独立的行（每个字段单独一行），
    而非同一行中空格/制表符分隔。例如：
      2025-04-12
      CNY
      -14,436.87
      45,230.15
      快捷支付
      支付宝（中国）网络技术有限公司

    返回: list[list[tuple]] — 每页一个列表，每页包含若干交易记录元组
          (date, currency, amount, balance, summary, counterparty)

    校验：19页流水约450笔交易，如果只解析出个位数说明逻辑有问题。
    """
    doc = fitz.open(pdf_path)
    all_pages_data = []

    for p in range(len(doc)):
        lines = doc[p].get_text().split("\n")
        lines = [l.strip() for l in lines]
        page_tx = []
        i = 0

        while i < len(lines):
            l = lines[i]
            if re.match(r"^\d{4}-\d{2}-\d{2}$", l):
                date = l
                currency = lines[i + 1] if i + 1 < len(lines) else ""
                amount = lines[i + 2] if i + 2 < len(lines) else ""
                balance = lines[i + 3] if i + 3 < len(lines) else ""
                summary = lines[i + 4] if i + 4 < len(lines) else ""
                counterparty = lines[i + 5] if i + 5 < len(lines) else ""
                page_tx.append(
                    (date, currency, amount, balance, summary, counterparty)
                )
                i += 6
            else:
                i += 1

        all_pages_data.append(page_tx)

    doc.close()
    return all_pages_data


def validate_extraction(all_pages_data):
    """校验提取结果是否合理（每页至少3行数据）"""
    total = sum(len(p) for p in all_pages_data)
    pages_with_few = [
        i for i, p in enumerate(all_pages_data) if len(p) < 3
    ]
    return {
        "total_transactions": total,
        "pages_with_few_data": pages_with_few,
        "needs_fallback": len(pages_with_few) > 0,
    }
