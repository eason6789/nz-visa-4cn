# 旅行计划模板 / Travel Itinerary Template

## 格式说明
- A4横向（landscape，842x595pt）
- 全英文行程表，无中文
- 6列：Day | Date | City / Route | Activities | Accommodation | Transport

## PDF样式
- **大标题**：深蓝色（#1A3A5C），16号 Helvetica-Bold，居中
  - 格式：`Trip Itinerary — New Zealand ([[Region]], [[Days]] Days)`
- **副标题**：灰色（#555555），9号 Helvetica，居中
  - 格式：`Departing from [[City]] ([[Airport Code]])`
- **分隔线**：蓝色（#2C5F8A）1pt 横线
- **表格表头**：深蓝（#1A3A5C）底白字，7号 Helvetica-Bold
- **数据行**：6.5号 Helvetica，交替白/浅灰底色
- **特殊高亮**：首日（Day 1）和末日最后一天用浅蓝（#E8F4FD）背景
- **表格列宽参考**：10mm | 18mm | 15mm | 32mm | 58mm | 30mm | 22mm

## 表格格式

| Day | Date | City / Route | Activities | Accommodation | Transport |
|-----|------|--------------|------------|---------------|-----------|
| 1 | Oct 1 | Shenzhen to Christchurch | Flight, arrival check-in | Christchurch Hotel | Flight CX124 |
| 2 | Oct 2 | Christchurch | Botanic Gardens, punting | Christchurch Hotel | Walk / Bus |
| ... | ... | ... | ... | ... | ... |

## 行程路线（按天数自动选择）

| 天数 | 路线 | 途经 |
|------|------|------|
| 5-7天 | 南岛经典 | Christchurch → Franz Josef → Queenstown → Lake Tekapo |
| 8-10天 | 南岛深度 | + Mount Cook, Wanaka 等 |
| 10天+ | 南北岛 | 北岛 Auckland, Rotorua, Wellington + 南岛 |

## 布局示意

```
┌─────────────────────────────────────────────────────────────┐
│  Trip Itinerary — New Zealand (South Island, 8 Days)        │  ← 深蓝大号居中
│  Departing from Hong Kong (HKG)                              │  ← 灰色副标题
├─────────────────────────────────────────────────────────────┤
│  ──────────────── 蓝色分隔线 ────────────────              │
├─────────────────────────────────────────────────────────────┤
│ Day │ Date     │ City / Route   │ Activities  │ Accomm │ Tpt│  ← 深蓝表头
├─────────────────────────────────────────────────────────────┤
│ 1   │ Oct 1    │ HKG→CHC        │ Flight...   │ Hotel  │ CX  │  ← 浅蓝高亮首日
│ 2   │ Oct 2    │ Christchurch   │ Gardens...  │ Hotel  │ Walk│  ← 白灰交替
│ ...  │ ...      │ ...            │ ...         │ ...    │ ... │
│ 8   │ Oct 8    │ CHC→HKG        │ Depart...   │ N/A    │ CZ  │  ← 浅蓝高亮末日
└─────────────────────────────────────────────────────────────┘
```

## 重要提醒
- Transport 列不要只写"Flight"，可以是 Bus / Car / Walk / Shuttle 等
- 不要用 Flight 作为列名，列名统一为 Transport
- 出发城市和航班号要根据实际路线合理选择
