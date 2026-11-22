# 信息图绘制指南

给摘要页加一张"一图看懂"。**这是可选增强, 不是必填项。**

这里的"信息图"指 HTML 页面内部用内联 SVG 绘制的网页图表, 不是交付给用户的独立图片文件。
图上文字全部由转录内容精确填写, 不交给生图工具猜字——生图工具写中文容易出错字, 一旦出错就是内容失真。

---

## 一、什么时候画

**画**: 视频里有明确的结构, 用图比用文字更清楚。符合以下任一条件:

- 有顺序的步骤或流程 ("第一步…第二步…")
- 明确的并列要点 (3-5 个, 彼此独立)
- 两方对比 (A vs B、前后、优缺点)
- 清晰的时间线或发展阶段
- 关键数字指标 (且数字来自视频原话)

**不画**:

- 视频是叙事型、观点散乱、没有清晰结构 → 删掉模板里整个 `<section class="infographic-block">`
- 只有 1-2 个要点 → 不值得画图
- 要点超过 6 个 → 砍到 3-5 个再画, 砍不下来就不画
- 图上必须有数字但视频没给准数 → 不画

**宁可不画, 不要硬凑。** 空着比放一张正确的废图强。

---

## 二、先定文字, 再画图

按 handdrawn-infographic 的内容纪律, 先把图上要出现的每个字写下来:

1. 一句主标题: 这张图让人记住什么 (≤14 字, 直接取自核心结论)
2. 3-5 个信息块: 每块 "标题 ≤10 字 + 说明 ≤18 字"
3. 底部一句总结: 可省略, 不写就删掉

**红线**: 每个字都必须能在转录稿里找到出处。数字、专名逐字核对。
写不出文字清单, 说明还没读懂视频, 回去重看转录稿, 不要硬编。

---

## 三、选版式

| 内容结构 | 版式 | SVG 骨架 |
|---|---|---|
| 有先后顺序 | 横向流程 | 下方 "流程" |
| 并列要点 3-5 个 | 编号卡片 | 下方 "编号卡片" |
| 两方对照 | 左右对比 | 下方 "对比" |
| 时间发展 | 横向时间线 | 下方 "时间线" |

一页只放一张图, 只讲一个结论。两个以上独立主题就别塞一张图里。

---

## 四、SVG 骨架

所有骨架都放在模板的 `{{INFOGRAPHIC_BLOCK}}` 位置。
用 `viewBox="0 0 720 240"` 让图随容器缩放; 颜色用 `var(--accent)` / `var(--accent-soft)` / `var(--ink)` / `var(--rule)` / `var(--field)`,
与页面主题自动一致。文字用 `font-family="var(--font-body)"`, 标题可用 `var(--font-body)`。

### 流程 (横向三步)

```html
<svg viewBox="0 0 720 200" role="img" aria-label="三步流程示意图">
  <g fill="none" stroke="var(--rule)" stroke-width="1.5">
    <line x1="150" y1="80" x2="230" y2="80"/><path d="M226 74 l8 6 -8 6"/>
    <line x1="370" y1="80" x2="450" y2="80"/><path d="M446 74 l8 6 -8 6"/>
  </g>
  <g font-family="var(--font-body)" font-size="15" font-weight="600" fill="var(--accent)" text-anchor="middle">
    <text x="75" y="45">01</text><text x="300" y="45">02</text><text x="525" y="45">03</text>
  </g>
  <g font-family="var(--font-body)" font-size="16" fill="var(--ink)" text-anchor="middle">
    <text x="75" y="112">步骤一</text><text x="300" y="112">步骤二</text><text x="525" y="112">步骤三</text>
  </g>
  <g font-family="var(--font-body)" font-size="12" fill="var(--ink-soft)" text-anchor="middle">
    <text x="75" y="138">说明≤18字</text><text x="300" y="138">说明≤18字</text><text x="525" y="138">说明≤18字</text>
  </g>
  <text x="360" y="185" font-family="var(--font-body)" font-size="17" fill="var(--accent)" text-anchor="middle">底部结论（可省略）</text>
</svg>
```

### 编号卡片 (三列并列)

```html
<svg viewBox="0 0 720 210" role="img" aria-label="三个要点并列示意图">
  <g>
    <rect x="10"  y="20" width="220" height="150" fill="var(--sheet)" stroke="var(--rule)"/>
    <rect x="250" y="20" width="220" height="150" fill="var(--sheet)" stroke="var(--rule)"/>
    <rect x="490" y="20" width="220" height="150" fill="var(--sheet)" stroke="var(--rule)"/>
  </g>
  <g font-family="var(--font-body)" font-size="34" font-weight="600" fill="var(--accent)">
    <text x="28" y="62">01</text><text x="268" y="62">02</text><text x="508" y="62">03</text>
  </g>
  <g font-family="var(--font-body)" font-size="16" font-weight="600" fill="var(--ink)">
    <text x="28" y="98">要点一</text><text x="268" y="98">要点二</text><text x="508" y="98">要点三</text>
  </g>
  <g font-family="var(--font-body)" font-size="12" fill="var(--ink-soft)">
    <text x="28" y="128">说明≤18字</text><text x="268" y="128">说明≤18字</text><text x="508" y="128">说明≤18字</text>
  </g>
  <text x="360" y="200" font-family="var(--font-body)" font-size="16" fill="var(--accent)" text-anchor="middle">底部结论（可省略）</text>
</svg>
```

### 左右对比

```html
<svg viewBox="0 0 720 230" role="img" aria-label="两方对比示意图">
  <line x1="360" y1="20" x2="360" y2="190" stroke="var(--ink)" stroke-width="2"/>
  <g font-family="var(--font-body)" font-size="20" font-weight="600" text-anchor="middle">
    <text x="180" y="48" fill="var(--accent)">A 方</text>
    <text x="540" y="48" fill="var(--accent)">B 方</text>
  </g>
  <g font-family="var(--font-body)" font-size="15" fill="var(--ink)" text-anchor="middle">
    <text x="180" y="92">要点一</text><text x="180" y="126">要点二</text>
    <text x="540" y="92">要点一</text><text x="540" y="126">要点二</text>
  </g>
  <text x="360" y="218" font-family="var(--font-body)" font-size="16" fill="var(--ink-soft)" text-anchor="middle">底部结论（可省略）</text>
</svg>
```

### 横向时间线

```html
<svg viewBox="0 0 720 180" role="img" aria-label="时间线示意图">
  <line x1="40" y1="80" x2="680" y2="80" stroke="var(--ink)" stroke-width="2"/>
  <g fill="var(--accent)">
    <circle cx="110" cy="80" r="6"/><circle cx="360" cy="80" r="6"/><circle cx="610" cy="80" r="6"/>
  </g>
  <g font-family="var(--font-mono)" font-size="12" fill="var(--accent)" text-anchor="middle">
    <text x="110" y="58">阶段一</text><text x="360" y="58">阶段二</text><text x="610" y="58">阶段三</text>
  </g>
  <g font-family="var(--font-body)" font-size="15" fill="var(--ink)" text-anchor="middle">
    <text x="110" y="115">说明一</text><text x="360" y="115">说明二</text><text x="610" y="115">说明三</text>
  </g>
  <g font-family="var(--font-body)" font-size="12" fill="var(--ink-soft)" text-anchor="middle">
    <text x="110" y="138">≤18字</text><text x="360" y="138">≤18字</text><text x="610" y="138">≤18字</text>
  </g>
</svg>
```

---

## 五、出图纪律

- 骨架里的 "步骤一/说明≤18字" 全部替换成真实内容。**留一个占位文字就是事故。**
- 中文长度超过骨架格子, 就缩短文字, **不要靠缩小字号硬塞** (小于 12px 不可读)。
- 信息块数量变化时, 改 `viewBox` 宽度和元素坐标, 不要拉伸变形。
- 图里每个字都要在文字清单里出现过; 清单里没有的字, 一个都不许加。
- 装饰只用直线、圆、矩形。`aria-label` 写清楚图在讲什么, 保证读屏可用。
- 信息图不算配图, 不替代关键帧。有图也要保留视频真实画面。

---

## 六、验收清单

- [ ] 图上每个字都有转录稿出处, 无编造
- [ ] 主标题一句, 信息块 3-5 个, 每块标题≤10字、说明≤18字
- [ ] 版式匹配内容结构 (顺序/并列/对比/时间)
- [ ] 无占位文字残留, 无字号小于 12px
- [ ] 颜色全部走页面 CSS 变量, 与主题一致
- [ ] `aria-label` 写清图意
- [ ] 窄屏下 SVG 等比缩放, 不溢出、不裁字
