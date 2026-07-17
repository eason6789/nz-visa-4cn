---
name: visa-docs
description: 多国签证申请材料生成器。目前支持新西兰(NZ)和澳洲(AU)。接收证件照片自动识别、中译英、排版合并，输出符合对应国家移民局标准的PDF文件。
triggers:
  - 签证材料
  - 签证申请
  - visa documents
  - visa application
  - 新西兰签证
  - New Zealand visa
  - NZ visa
  - 澳洲签证
  - 澳大利亚签证
  - Australia visa
  - AU visa
  - Subclass 600
inputs:
  country: 目标国家 (nz / au)，根据触发词自动判断，必要时询问用户
  photos: 用户上传的原始证件照片
  trip_type: 单次/多次入境
outputs:
  output_dir: output/ 子目录
  PDFs: 一套完整的签证申请PDF（含解释信 + 按序号命名的子附件）
requirements:
  python_packages: pymupdf, reportlab, Pillow, openpyxl
  tools: macOS sips (HEIC格式转换)
  api: zhipu (智谱GLM-4V / GLM-4V-Flash，用于OCR图像识别)
---

# 多国签证材料生成器 / Multi-Country Visa Document Generator

## 支持国家 / Supported Countries

| Country | Key | Visa Type | Authority |
|---------|-----|-----------|-----------|
| New Zealand | `nz` | Visitor Visa (Tourism) | Immigration New Zealand (INZ) |
| Australia | `au` | Visitor Visa (Subclass 600) | Department of Home Affairs |

## 国家识别 / Country Detection

根据用户触发词自动判断，模糊时主动询问：
- **NZ**: 新西兰, New Zealand, NZ, INZ
- **AU**: 澳洲, 澳大利亚, Australia, AU, Subclass 600

---

## 一、通用前置询问 / Universal Pre-Flight

### 1.1 基本信息 / Personal Info
- 中文姓名 + 英文拼音姓名
- 护照号 / 身份证号 / 出生日期
- 当前住址 / 联系电话 / 邮箱

### 1.2 职业与收入 / Employment & Income
- 当前状态：在职 / 离职休整 / 创业 / 自由职业
- 最近雇主、职位、工作年限
- 如当前无工资收入 → 请说明原因 + 提供替代财务证明
- 年收入水平（可从纳税记录交叉验证）

### 1.3 旅行计划 / Travel Plan
- 出发/返回日期、同行人数
- 主要目的地城市/区域
- 过去3年国际旅行经历（国家列表）

### 1.4 回国约束力 / Ties to Home Country
- 房产情况（城市、面积、贷款状态）
- 车辆情况
- 家庭关系（配偶、父母、子女、宠物）

### 1.5 材料完整性检查 / Document Checklist

**身份证明：** □护照 □身份证正反面 □户口本
**职业证明：** □在职证明 □营业执照(如有) □离职证明(如已离职)
**财务证明：** □银行流水(12个月) □银行存款/理财 □纳税记录 □证券持仓(如有)
**资产证明：** □房产证 □车辆登记证+行驶证
**旅行相关：** □行程计划 □社交媒体记录(可选) □多次入境陈述信(如需)

---

## 二、新西兰路线 / New Zealand Route (NZ)

### 输出文件 / Output Files

| # | 文件名 | 格式 |
|---|--------|------|
| 01 | `01_passport_护照.pdf` | 图片合并，不翻译 |
| 02 | `02_national_id_身份证.pdf` | A4横版 左原/右译 |
| 03 | `03_employment_verification_在职证明.pdf` | A4横版 左原/右译 |
| 04 | `04_household_register_户口本.pdf` | A4横版 左原/右译 |
| 05 | `05_bank_statements_银行证明.pdf` | A4横版 左原/右译 |
| 06 | `06_travel_itinerary_旅行计划.pdf` | A4横版 英文表格 |
| 07 | `07_statement_multiple_journeys_入境陈述.pdf` | A4纵版（仅多次入境） |
| 08 | `08_subsequent_journey_plan_后续旅行计划.pdf` | A4横版（仅多次入境） |
| 09 | `09_travel_history_旅行记录.pdf` | 可选 |
| 10 | `10_proof_of_assets_资产证明.pdf` | A4横版 左原/右译 |

### NZ规则 / NZ Rules
- 文件名：下划线分隔 + 中文后缀（如 `05_bank_statements_银行证明.pdf`）
- 单文件 ≤ 10MB
- 旅行计划按南北岛自动规划（5-7天南岛经典/8-10天深度/10+天南北岛）
- 翻译者信息标注在右下角（如有）
- 多次入境需：入境陈述 + 后续旅行计划

---

## 三、澳洲路线 / Australia Route (AU)

### 输出文件 / Output Files

| # | 文件名 | 格式 |
|---|--------|------|
| 00 | `00_COVER_LETTER.pdf` | A4纵版 英文解释信（≤2页） |
| A | `A_Passport.pdf` | 图片合并 + 标题栏 |
| B | `B_Employment_Verification.pdf` | A4横版 左原/右译 |
| C | `C_Bank_Deposit_and_Wealth_Management.pdf` | A4横版 |
| D | `D_Tax_Payment_Records.pdf` | A4横版 多列逐行翻译 |
| E | `E_Securities_Holdings.pdf` | A4横版 左原/右译 |
| F | `F_Property_Ownership_Certificate.pdf` | A4横版 左原/右译 |
| G | `G_Vehicle_Registration.pdf` | A4横版 左原/右译 |
| H | `H_Travel_Itinerary.pdf` | A4横版 英文表格 |
| I | `I_Bank_Statements.pdf` | A4横版 左原/右译 |

### AU规则 / AU Rules
- 文件名：纯英文 + 字母前缀 + 下划线（如 `C_Bank_Deposit_and_Wealth_Management.pdf`）
- 单附件 ≤ 5MB
- 必须包含解释信，涵盖 5 个必要章节：
  1. Personal Background（个人背景 + 离职说明如适用）
  2. Travel Motivation & Itinerary（旅行动机 + 行程概要）
  3. Source of Funds（资金来源，引用附件文件名为证据）
  4. Strong Ties to China（回国约束力）
  5. Request for Multiple-Entry Visa（多次入境理由，如适用）
- 解释信中资产估值需标注 CNY + AUD 双币种（汇率 ≈ 4.75）
- 如申请3年多次入境：需说明本次未覆盖的区域 + 未来旅行计划
- 每个附件PDF第一页标题栏需与文件名一致
- 不需要翻译者标注

---

## 四、共享组件 / Shared Components (NZ + AU)

### 4.1 中文字体（绝对关键）
```python
pdfmetrics.registerFont(TTFont("CN", '/System/Library/Fonts/STHeiti Light.ttc', subfontIndex=0))
```
- 所有含中文的文本：fontName='CN'
- **禁止使用 CNBold**（STHeiti Medium.ttc 会导致 PDF 损坏）
- 表格内 Paragraph 自带样式会覆盖 TableStyle → ParagraphStyle 也必须设 CN
- 仅纯英文标题可用 Helvetica-Bold

### 4.2 图片方向修正（绝对不能省略）
```python
from PIL import Image, ImageOps
pil = Image.open(path)
pil = ImageOps.exif_transpose(pil)  # 必须在所有处理之前
```
- HEIC 先转换：`sips -s format jpeg input.HEIC --out output.jpg`

### 4.3 DPI 与像素/Points 转换（高频出错点）
- `fitz.Matrix(dpi, dpi)` → 像素 = 原尺寸(pts) × dpi
- RLImage 需要 **points**，不是像素
- 公式：`display_pts = pixels / dpi`
- 例：Matrix(2.0) 渲染 → 宽度 842×2.0=1684px → 1684/2.0=842pts 显示

### 4.4 页面溢出防止（空白页根因）
- 可用高度 = 页面总高 - 边距 - 标题栏 - 间距 - 页脚
- 图片 max_h ≤ 可用高度 - 安全余量（10-20pt）
- A4竖版PDF渲染到横版时缩放比 ≈ 0.67，高度 ≈ 566pt，需收紧到 ~500pt
- 验证：fitz 检查每页文本量 > 20 字符

### 4.5 GLM OCR（通用）
- `glm-4v` → 图片OCR（中文证件识别），首选
- `glm-4v-flash` → 免费版OCR，备用
- `glm-4-flash` → 纯文本批量翻译
- `glm-5.1` → 不支持图片，**禁止用于OCR**
- 批量翻译 ≤ 30条/批

### 4.6 银行流水解析（通用）
- `page.get_text()` 提取文本 → 逐行解析
- 日期行 (YYYY-MM-DD) 识别为数据行
- 招行格式：6行一组 (date, currency, amount, balance, summary, counterparty)
- 校验：每页 ≥ 3行数据，否则降级 GLM-4V 读图

---

## 🚨 致命陷阱汇总 / Critical Pitfalls

| # | 问题 | 症状 | 解决 |
|---|------|------|------|
| 1 | 中文字体 | 黑框/方块/"I" | fontName='CN'，Paragraph和TableStyle都要设 |
| 2 | CNBold | PDF损坏/乱码 | 只用STHeiti Light.ttc，不用Medium.ttc |
| 3 | DPI转换 | 图片巨大或溢出 | pixels/dpi = points |
| 4 | 页面溢出 | 标题页+空白内容页 | max_h收紧，可用高度公式计算 |
| 5 | 方向旋转 | 图片倒置/侧放 | `exif_transpose()` 不可省略 |
| 6 | 列数不匹配 | 翻译行数与原件不同 | 多列表格逐列提取+翻译，保持列数一致 |
| 7 | 编造信息 | 签证官质疑真实性 | 只写实际材料能证明的内容 |
| 8 | 竖版PDF横放 | 高度566pt溢出 | max_h=UH-60 |
| 9 | 两端对齐 | 英文词间距巨大 | 使用 TA_LEFT |
| 10 | 个人信息泄露 | 代码含真实数据 | 脚本和模板只用虚构/占位数据 |

---

## 五、生成后验证 / Post-Generation

- [ ] fitz 检查每页文本 > 20 字符（无空白页）
- [ ] 中文字符正常（无方块/"I"）
- [ ] 图片方向已修正
- [ ] 标题与文件名一致
- [ ] 翻译列数/行数 = 原件列数/行数
- [ ] 文件大小：NZ<10MB, AU<5MB
- [ ] 解释信/陈述信 ≤ 2-3 页
- [ ] 输出目录无临时文件残留

---

## 六、参考资料

- `templates/` — 各类材料翻译模板
- `scripts/` — PDF生成与信息提取脚本
- `examples/` — NZ签证示例输出
- `references/` — 自定义生成模式参考代码

---

**Version:** 2.0.0 (Unified NZ + AU)
**Last Updated:** 2026-07-17
