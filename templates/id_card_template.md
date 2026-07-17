# 身份证翻译表格模板 / National ID Card Translation Template

## 格式说明
- A4横向（landscape，842x595pt）
- 左侧50%放置身份证原件图片，右侧50%放置两列对照表 [Field | English]

## ⚠️ 图片旋转方向（关键！）
- **必须用 `ImageOps.exif_transpose()` 修正图片方向**
- 修正后图片里的文字必须**正着可读**（阅读方向）
- 不要拘泥于位置和尺寸，**方向最重要**！
```python
from PIL import Image, ImageOps
pil_img = Image.open(path)
pil_img = ImageOps.exif_transpose(pil_img)  # 这步不能省！
```

## PDF样式
- **页面1标题**：深蓝底白字 section header "Page 1 — Front Side (正面)"
- **页面2标题**：深蓝底白字 section header "Page 2 — Back Side (背面)"
- **左区表头**：深蓝底白字 "Original Document (原件)"
- **右区表头**：深蓝底白字 "English Translation (英文译本)"
- **数据行**：交替白/浅灰底色，灰色细网格线（0.4pt）
- **底部**：灰色横线（HRFlowable, 100%宽度, 0.5pt）+ 斜体灰色小字 "Translated by: [Name] | [Certification]"（右下对齐，7号字）
- **注意：背面必须有字段 "Document Title: People's Republic of China Resident Identity Card"**
- 表格只有两列：Field 和 English

## 正面字段对照表

| Field | English |
|-------|---------|
| Name | [[English Name]] |
| Gender | [[Gender]] |
| Ethnic Group | [[Ethnicity]] |
| Date of Birth | [[YYYY-MM-DD]] |
| Address | [[Full Address]] |
| Citizen ID No. | [[ID Number]] |

## 背面字段对照表

| Field | English |
|-------|---------|
| Document Title | People's Republic of China Resident Identity Card |
| Issuing Authority | [[Authority]] |
| Valid Period | [[YYYY-MM-DD to YYYY-MM-DD]] |

## 布局示意

```
┌─────────────────────────────────────────────────────────────┐
│  Page 1 — Front Side (正面)                                  │  ← 深蓝底白字
├─────────────────────────────┬───────────────────────────────┤
│                             │  Field    │ English            │  ← 深蓝底白字表头
│   [身份证原件照片]          ├───────────────────────────────┤
│   (正向旋转)                 │  Name     │ [[Name]]          │  ← 白灰交替底纹
│                             │  Gender   │ [[Male/Female]]   │
│                             │  ...      │ ...               │
├─────────────────────────────┴───────────────────────────────┤
│                                          Translated by: ...  │  ← 灰色斜体，右下
└─────────────────────────────────────────────────────────────┘
```

## 重要提醒
- 背面有 "Document Title: People's Republic of China Resident Identity Card"
- 表格只有两列：Field 和 English（不得有中文列）
- 所有图片必须用 `ImageOps.exif_transpose()` 修正方向
