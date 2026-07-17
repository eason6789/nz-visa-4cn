# 户口本翻译模板 / Household Register Translation Template

## 格式说明
- A4横向（landscape，842x595pt）
- Page 1 = 首页（Cover），Page 2 = 个人信息页（Member Info）
- 两列表格：Field | English

## ⚠️ 图片旋转方向（关键！）
- **必须用 `ImageOps.exif_transpose()` 修正图片方向**
- 修正后图片里的文字必须**正着可读**（阅读方向）
- 不要拘泥于位置和尺寸，**方向最重要**！

## PDF样式
- **Page 1标题**：深蓝底白字 section header "Page 1 - Household Register Cover (首页)"
- **Page 2标题**：深蓝底白字 section header "Page 2 - Household Member Information (个人信息页)"
- **表格**：深蓝底白字表头，交替白/浅灰行底色，灰色细网格线
- **底部**：灰色分隔线 + 斜体翻译者标注

## 首页字段（两列：Field | English）

| Field | English |
|-------|---------|
| Document Title | Household Register |
| Issuing Authority | [[Local Police Station]] |
| Region | [[Province/City/District]] |
| Address | [[Registered Address]] |
| Head of Household | [[Name of First Person]] |
| Total Population | [[Number of People]] |

## 个人信息页字段（两列：Field | English）

| Field | English |
|-------|---------|
| Name | [[Member Name]] |
| Relationship to Head | [[Relation]] |
| Gender | [[Male/Female]] |
| Birth Date | [[YYYY-MM-DD]] |
| Birth Place | [[Place]] |
| Native Place | [[Place]] |
| Ethnic Group | [[Ethnicity]] |
| Religion | [[Religion]] |
| ID Card No. | [[ID Number]] |
| Education | [[Education]] |
| Marital Status | [[Status]] |
| Military Service | [[Status]] |
| Workplace | [[Workplace]] |
| Occupation | [[Occupation]] |
| Address | [[Address]] |

## 布局示意（两列：Field | English）

```
┌─────────────────────────────────────────────────────────────┐
│  Page 1 - Household Register Cover (首页)                    │  ← 深蓝底白字
├─────────────────────────────────────────────────────────────┤
│  Field                     │ English                         │
│  Document Title            │ Household Register             │
│  Issuing Authority         │ [[Local Police Station]]       │
│  ...                       │ ...                             │
├─────────────────────────────────────────────────────────────┤
│                              Translated by: [Name] | [Cert] │
└─────────────────────────────────────────────────────────────┘

（分页符）

┌─────────────────────────────────────────────────────────────┐
│  Page 2 - Household Member Information (个人信息页)          │  ← 深蓝底白字
├─────────────────────────────────────────────────────────────┤
│  Field                     │ English                         │
│  Name                      │ [[Member Name]]                 │
│  Gender                    │ [[Male/Female]]                 │
│  ...                       │ ...                             │
└─────────────────────────────────────────────────────────────┘
```
