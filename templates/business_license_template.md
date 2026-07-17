# 在职证明+营业执照翻译模板 / Employment Verification Template

## 格式说明
- A4横向（landscape，842x595pt）
- **顺序必须：Part 1（在职证明）→ Part 2（营业执照），不能反过来！**
- 每部分使用深蓝底白字 section header
- 两列表格：Field | English（去掉中文原文列）

## PDF样式
- **Part 1标题**：深蓝底白字 "Part 1: Employment Verification Letter (在职证明)"
- **Part 2标题**：深蓝底白字 "Part 2: Business License (营业执照)"
- **表格**：深蓝底白字表头，交替白/浅灰行底色，灰色细网格线（0.4pt）
- **底部**：灰色分隔线 + 斜体灰色翻译者标注（右下对齐）

## 在职证明字段（Part 1，8项，必须在前！）

| Field | English |
|-------|---------|
| Name | [[English Name]] |
| Gender | [[Male/Female]] |
| Date of Birth | [[YYYY-MM-DD]] |
| Passport No. | [[Passport Number]] |
| Employer | [[Company Name]] |
| Position | [[Job Title]] |
| Employment Start Date | [[YYYY-MM-DD]] |
| Monthly Salary | [[Amount CNY]] |

## 营业执照字段（Part 2，8项，必须在后！）

| Field | English |
|-------|---------|
| Unified Social Credit Code | [[Code]] |
| Enterprise Name | [[Company Name]] |
| Enterprise Type | [[Limited Liability Company]] |
| Legal Representative | [[Name]] |
| Date of Establishment | [[YYYY-MM-DD]] |
| Address | [[Registered Address]] |
| Registration Authority | [[Issuing Authority]] |
| Date of Issue | [[YYYY-MM-DD]] |

## 布局示意（两列：Field | English）

```
┌─────────────────────────────────────────────────────────────┐
│  Part 1: Employment Verification Letter (在职证明)            │  ← 深蓝底白字
├─────────────────────────────────────────────────────────────┤
│  Field                     │ English                         │
│  Name                      │ [[English Name]]                │
│  Gender                    │ [[Male/Female]]                 │
│  ...                       │ ...                             │
├─────────────────────────────────────────────────────────────┤
│                                          Translated by: ...  │  ← 灰色斜体
└─────────────────────────────────────────────────────────────┘

                        ← PageBreak() 分页符 →

┌─────────────────────────────────────────────────────────────┐
│  Part 2: Business License (营业执照)                          │  ← 深蓝底白字
├─────────────────────────────────────────────────────────────┤
│  Field                     │ English                         │
│  Unified Social Credit... │ [[Code]]                        │
│  Enterprise Name           │ [[Company Name]]                │
│  ...                       │ ...                             │
├─────────────────────────────────────────────────────────────┤
│                                          Translated by: ...  │  ← 灰色斜体
└─────────────────────────────────────────────────────────────┘
```

## 重要提醒
- **顺序不能错**：Part 1 = 在职证明（Employment Verification），Part 2 = 营业执照（Business License）
- 如果 material 里没有营业执照，可以只生成在职证明
- **表格只有两列：Field | English（去掉中文原文列）**
