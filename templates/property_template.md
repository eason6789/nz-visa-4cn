# 房产证翻译表格模板 / Property Ownership Certificate Translation Template

## 格式说明
- A4横向，左侧50%放置房产证原件图片，右侧50%放置两列对照表 [Field | English]
- 字段逐项对照，保持行数与原文件一致
- 右下角添加翻译者标注

## ⚠️ 图片旋转方向（关键！）
- **必须用 `ImageOps.exif_transpose()` 修正图片方向**
- 修正后图片里的文字必须**正着可读**（阅读方向）
- 不要拘泥于位置和尺寸，**方向最重要**！
```python
from PIL import Image, ImageOps
pil_img = Image.open(path)
pil_img = ImageOps.exif_transpose(pil_img)  # 这步不能省！
```

## 主要字段（中英对照）

```markdown
| Field (English) | English Translation |
|-----------------|---------------------|
| Certificate Number | [PROPERTY_CERT_NUMBER] |
| Property Address | [PROPERTY_ADDRESS] |
| Owner Name | [OWNER_NAME] |
| Document Type | Certificate of Real Estate Ownership |
| Land Type | State-owned Construction Land Use Rights |
| Building Area | Approximately XX.XX sqm |
| Usage | Residential |
| Rights Holder | [OWNER_NAME] |
| Issuing Authority | [AUTHORITY] |
| Issue Date | [DATE] |
```

## 贷款结清证明字段

```markdown
| Field (English) | English Translation |
|-----------------|---------------------|
| Certificate Type | Certificate of Loan Settlement |
| Borrower Name | [BORROWER_NAME] |
| ID Number | [ID_NUMBER] |
| Loan Institution | [BANK_NAME] |
| Loan Amount | RMB XX,000 |
| Settlement Date | [DATE] |
| Outstanding Balance | 0.00 (Fully Paid) |
| Issuing Authority | [BANK_NAME] |
```

## 翻译者标注格式
```
Translated by: [TRANSLATOR_NAME]
[TRANSLATOR_CERTIFICATION]
```

## 布局示意
```
┌─────────────────────────────┬─────────────────────────────┐
│                             │  English Translation        │
│   [房产证原件照片]          ├─────────────────────────────┤
│   (正向旋转)                 │ Field    │ English           │
│                             │ Cert No. │ [[CERT_NO]]       │
│                             │ Address  │ [[ADDR]]          │
│                             │ Owner    │ [[OWNER]]         │
│                             │ ...      │ ...               │
├─────────────────────────────┴─────────────────────────────┤
│                     Translated by: [Name] | [Certification] │
└─────────────────────────────────────────────────────────────┘
```

## reportlab生成参考

```python
def generate_property_table(fields, output_path):
    data = [["Field (English)", "English Translation"]]
    for en, tr in fields:
        data.append([en, tr])

    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4),
                            leftMargin=10*mm, rightMargin=10*mm,
                            topMargin=10*mm, bottomMargin=15*mm)

    col_widths = [80*mm, 60*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5F8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
```

## 虚构数据占位符

| 真实数据 | 虚构数据 |
|---------|---------|
| 证书编号 | 京(2020)朝阳区不动产权第XXXXXXXX号 |
| 地址 | 北京市朝阳区建国路88号1号楼1001室 |
| 持有人姓名 | Zhang San |