# 银行流水翻译模板 / Bank Statement Translation Template

## 格式说明
- A4横向（landscape，842x595pt）
- **左图右表布局**：左侧50%放原件图片，右侧50%放英文译本
- 银行流水 + 资产证明（存款证明、基金等）合并在同一个PDF里

## ⚠️ 图片旋转方向（关键！两种失效模式！）

**必须处理两种情况，否则竖屏拍的文件（身份证、户口本等）全部歪着：**

**情况1 — 带 EXIF Orientation 标签的 JPG（相机直出）：**
- `ImageOps.exif_transpose()` 自动转正

**情况2 — iPhone HEIC→JPG 转换产物（最常踩坑）：**
- macOS 把 HEIC 转 JPG 时，像素已转正但 EXIF 被剥离
- `exif_transpose()` 找不到标签，什么都不做 → 竖版文件在 PDF 里是横的
- 判断条件：宽>高 AND 长边>3000 AND 无 EXIF Orientation 标签 → `pil.transpose(Image.ROTATE_90)`

```python
pil = ImageOps.exif_transpose(pil)
exif_tag = pil.get_ifd(0x010f) if hasattr(pil, 'get_ifd') else None
if pil.size[0] > pil.size[1] and max(pil.size) > 3000 and not exif_tag:
    pil = pil.transpose(Image.ROTATE_90)
```

修正后图片里的文字必须**正着可读**（阅读方向），不要拘泥于位置和尺寸！

## PDF样式
- **Part 1标题**：深蓝底白字 section header "Part 1: Bank Statement"
- **Part 2标题**：深蓝底白字 section header "Part 2: Certificate of Assets"
- **账户摘要行**：浅蓝底色表格，显示 Account Holder, Period, Currency
- **交易明细表**：深蓝底白字表头，交替白/浅灰底纹
  - 6列：Date | Currency | Transaction Amount | Balance | Transaction Summary | Counterparty
  - **全部翻译为英文**！摘要和对手方列中的中文必须全部转为英文
  - 金额正数绿色（#1A7A1A），负数红色（#CC0000）
- **底部统计行**：浅蓝底色 Total Credits, Total Debits, Ending Balance
- **备注**：斜体灰色小字 "Original Chinese bank statement on LEFT, English translation on RIGHT"

## 翻译字典要求
- 交易摘要（Summary 列）：常见中文类型全部覆盖（快捷支付、网联收款、代发款项、养老金缴存等）
- 对手方（Counterparty 列）：
  - 公司/机构名称 → 完整翻译（如"深圳市住房公积金管理中心" → "Shenzhen Housing Provident Fund Management Center"）
  - 个人姓名 → 直接填入原文拼音（无需翻译，如"杨秋燕" → "Yang Qiuyan"）
  - 内部账户标签（如"其它应收款"）→ 翻译为英文或视情况省略
- 通用词根（有限公司→Co., Ltd.、集团→Group 等）按长度降序替换，防止短词优先匹配
- **最终 PDF 中交易明细表不允许出现任何中文字符**

## 银行流水翻译表头

| Date | Currency | Transaction Amount | Balance | Transaction Summary | Counterparty |
|------|----------|-------------------|---------|-------------------|--------------|
| [[15 Jan 2024]] | CNY | [[+50,000.00]] | [[52,345.67]] | [[Salary/Payroll]] | [[Employer ABC]] |
| ... | ... | ... | ... | ... | ... |

## 资产证明表头

| Types of Assets | Currency & Amount | Value Date | Expiry Date |
|----------------|-------------------|------------|-------------|
| [[Weekly Fund A]] | CNY [[33,482.08]] | / | / |
| ... | ... | ... | ... |

## 布局示意

```
┌─────────────────────────────────────────────────────────────┐
│  Part 1: Bank Statement (银行流水)                          │  ← 深蓝底白字
├─────────────────────────────────────────────────────────────┤
│  Account Holder: [[Name]] | Period: [[Jan-Dec 2024]] | CNY │  ← 浅蓝摘要
├─────────────────────────────────────────────────────────────┤
│  Date  │ Currency│ Transaction│ Balance│ Summary │ Counter │
│  15Jan │ CNY     │ +50,000.00 │ 52,345 │ Salary  │ Employer│  ← 深蓝表头
│  16Jan │ CNY     │ -1,200.00  │ 51,145 │ Shopping│ Merchant│  ← 白灰交替
│  ...   │ ...     │ ...        │ ...    │ ...     │ ...     │
├─────────────────────────────────────────────────────────────┤
│  Total Credits: +55,000 | Total Debits: -4,650 | End: 52,6 │  ← 浅蓝统计
├─────────────────────────────────────────────────────────────┤
│  Part 2: Certificate of Assets (个人资产证明)               │  ← 深蓝底白字
├─────────────────────────────────────────────────────────────┤
│  Asset Type      │ Currency & Amount │ Value Date │ Expiry │
│  Weekly Fund A   │ CNY 33,482.08     │ /          │ /      │
│  ...             │ ...               │ ...        │ ...    │
├─────────────────────────────────────────────────────────────┤
│  Note: Original on LEFT, Translation on RIGHT               │
│                                          Translated by: ... │
└─────────────────────────────────────────────────────────────┘
```

## 重要提醒
- 每页流水逐页生成左原件/右译本（偶数页）
- 银行流水 + 资产证明合并在一个PDF
- 如果 `page.get_text()` 提取的行少于3行，降级用 GLM-4V 读图识别
