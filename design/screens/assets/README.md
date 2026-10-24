# 画面原型 v2 · 组件手册（给制作画面的人/AI）

参考实现：`../01-today.html`（先读它）。样式 `cp2.css`，壳与交互 `cp2.js`，插画 `art.js`，图表 `charts.js`。页面结构固定：

```html
<!doctype html><html lang="zh-CN"><head>…<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap"><link rel="stylesheet" href="assets/cp2.css"></head>
<body data-page="candidates" data-crumb="流水线 / 选品">
<template id="main-tpl"> …主区… </template>
<template id="detail-tpl"> …右栏默认内容（可选）… </template>
<script src="assets/art.js"></script><script src="assets/charts.js"></script><script src="assets/cp2.js"></script>
</body></html>
```

`data-page` 取值：today direction candidates sourcing assets listing approvals grants audit settings。

## 设计语言（不得改变）
- 一个颜色一个意思：**青**=可点/选中；**琥珀(wait)**=等你决定/数据待补；**红(block)**=被拦/不可做/不一致；**绿(ok)**=已通过且已核对；**蓝灰(info)**=AI 在做。
- 图表系列色只用 `s1`蓝 `s2`橙 `s3`青绿 `s4`紫（已校验）；单系列用 `primary`；状态色只表状态，不当系列色。
- 数字用 tabular（已全局），ID/时间/编号用 `.mono`；日文内容容器加 `lang="ja"`；中文界面。
- 每屏一个主按钮（`.btn.primary`）在页首右侧；解释性文字少；缺数据写“不可算/数据待补/未录入”，**绝不用 0 或“正常”代替**。
- 卡片靠阴影分层，不要单边彩色竖线装饰；强调靠整块浅底 + 文字色。
- 不出现 `ACT-`/`RULE-` 编号（合规报告里的 G2-001 这类规则号可以出现）、哈希（审计页详情除外）、Phase/本期、机制解释。

## 版式
`.page-head`（内含 `<span class="eyebrow">…</span><h1>…</h1><p>…</p>` 与 `.actions`）· `.g2 .g3 .g4`（等分）· `.g-main`（主 1.7 : 辅 1）· `.g-main-r` · `.stack` `.stack.sm` · `.row` `.row.wrap` `.row.between` · `.right`（推到最右）。
卡片：`.card`（`.flush` 无内边距，用于带表格；`.tint` 浅底）+ `.card-head`（`h2` + `.meta` + `.tools`）；深色面板：`.dark-panel`（首屏英雄区，每屏最多一个）。

## 组件
- 指标：`.stat`（`.k` 标签 `.v` 数值 `.n` 说明 `.d.up/.down/.flat` 增量，`.spark.chart[data-chart=spark]` 迷你趋势；`.stat.wait/.block/.ok` 给数值上色）。
- 徽标：`.badge` + `.wait/.block/.ok/.info/.primary`（自带圆点）· `.grade.A/.B/.C`（数据来源等级）· `.tag`（等宽小标签）· `.chip[aria-pressed]`（筛选，点击自动切换）· `.seg > button[aria-pressed]`（分段）· `.switch[role=switch][aria-checked]`。
- 表格：`table.tbl`（`.dense`）；行点击换右栏：`<tr data-detail="模板id">` + `<template id="模板id">`；数字列 `.num`；副行 `.sub`；商品单元格 `.prod`（`.thumb[data-art=名称]` + `.t` `.s`）。
- 商品插画：`<span class="thumb [sm|lg|xl]" data-art="box|spoons|cable|brush|cup|rack|divider|hooks|whisk|basket|earbuds|serum|powerbank|mask|snack"></span>`；大图用 `<div class="ph" data-art="…">`（正方形）。
- 航线（流水线）：`.route > a.wp[.done|.now|.wait|.block] > .node + b + .s`（深色面板内自动换色）；步骤条：`.steps > .st[.done|.now|.wait|.block] > i + 文字`。
- 进度：`.meter > i[style=width:60%]`（`.wait/.ok/.block`）。
- 时间线：`ul.timeline > li > .pt[.ok|.wait|.block|.human] + .when + .what`；活动流：`ul.feed > li > .dot + div`。
- Tab：`.tabs > button[role=tab][data-tab=x][aria-selected]` + 外层 `data-tabs` 容器内 `[data-pane=x]`。分段视图：`button[data-view=a][data-group=g]` + `[data-pane-view=a][data-group=g]`。
- 证据折叠：`details.ev[data-ev] > summary + .body`，`summary` 里放 `<span class="viewed badge wait">必看</span>`；放在带 `data-approval` 的容器里，展开全部后 `[data-approve]` 按钮启用，`[data-approve-hint]` 显示提示。
- 决定区：`.decision`（`.law` 固定文案 + 按钮），吸底。
- 手机预览：`.phone > .screen > .bar>i + 图 + .p-price + .p-title + .p-row`。
- 其他：`.alert(.wait/.block/.ok/.info)` `.lede`（“必须先看这一句”）`.kv`（dl 键值）`.cost`（成本表）`.legend` `.divider`。
- 交互：任何按钮 `data-toast="…（演示）"`；复制 `data-copy="…"`；勾选计数 `input[data-count="#id"][data-max]`；提示 `data-tip="…"`。

## 图表（charts.js）
`<div class="chart" data-chart="类型" data-cfg='{JSON}'></div>`，单引号包 JSON。颜色名：`primary s1 s2 s3 s4 ok wait block info` 或 `#hex`。
- `spark` `{values,color,w,h}` · `ring` `{pct,size,stroke,label,sub,color,fs,tip}` · `gauge` `{pct,label,sub,color,w,h}` · `hbars` `{items:[{label,value,text,color,tip}],lw,color,max}` · `vbars` `{items:[{label,value,text,color}],w,h,labels:true}`
- `hist` `{values,labels,highlight:[i0,i1],color,unit,marks:[{at,label,color}],w,h}` · `scatter` `{points:[{x,y,r,label,show,color,hollow,tip}],xmin,xmax,ymin,ymax,xlabel,ylabel,yunit,hlines:[{y,label,color}],zone:{x0,x1,y0,y1,label},w,h}`
- `waterfall` `{items:[{label,value,type:'revenue'|'cost'|'profit',color,tip}],legend:[{label,color}],w,lw,rowH}`（成本瀑布：营收 → 逐项扣减 → 利润；`cost` 用 `s1`(到岸成本) / `s4`(佣金手续费) / `s2`(退货损耗)）
- `radar` `{axes:[{label,value 0-1}],series:[{values,color}],size}` · `stack` `{items:[{label,value,color,text}],h}` · `line` `{labels,series:[{name,values,color,dash}],unit,ymin,ymax,hlines,w,h}` · `heat` `{rows,cols,matrix,max,color,cw,ch,tip}` · `donut` `{items:[{label,value,color,text}],label,sub,size}`
图表规范：2px 表面色间隔、细标记、直接标注关键点、网格弱化；每张图配标题与一句话“读法”；悬停有提示（已内置）。

## 演示数据（必须保持跨页一致，见 `../../ai/08_画面规格.md` §7）
店铺 JP-01 日本站（跨境直邮）；用户林薇（Owner+Operator，单人运行）；日期 2026-10-20；候选 24（可选 12/待补 7/不可售 5）；
可选前 8：①折叠収納ボックス3個セット ¥2,480 31.7% 82（box）②シリコン調理スプーン5点セット ¥1,980 34.2% 79（spoons）③デスクケーブルオーガナイザー ¥1,680 29.8% 76（cable）④ペット用ブラシ 抜け毛クリーナー ¥1,880 33.0% 74（brush）⑤折りたたみシリコンカップ ¥1,480 28.4% 71（cup）⑥キッチン水切りラック ¥2,780 27.1% 68（rack）⑦引き出し仕切り板 ¥1,580 30.2% 66（divider）⑧マグネットフック6個入 ¥1,180 26.0% 63（hooks）。
不可售：Bluetoothイヤホン（含无线，earbuds）、美容液（化粧品，serum）、モバイルバッテリー（含电池，powerbank）、保湿マスク（化粧品，mask）、お菓子ギフト（食品，snack）。数据待补：シリコン泡立て器（缺 c3：未填重量，whisk）、折りたたみ洗濯かご（缺税口径，basket）。
成本 #1（售价 ¥2,480）：c1 ¥666（32 CNY×20.8）· c2 ¥62 · c3 ¥520 · c4 ¥0 · c5 ¥0 · c6 ¥30 · c7 ¥25 · 到岸小计 ¥1,303 · c8 佣金10% ¥248 · c9 3% ¥74 · c10 退货损耗 ¥70 · 总成本 ¥1,695 · 利润 ¥785 · 毛利 31.7%。
成本 #2（售价 ¥1,980）：c1 ¥499 · c2 ¥62 · c3 ¥380 · c6 ¥30 · c7 ¥22 · 到岸 ¥993 · c8 ¥198 · c9 ¥59 · c10 ¥53 · 利润 ¥677 · 毛利 34.2%。方向卡毛利底线 12%、目标 32%（授权示例下限 28%）。
今日待办 5 件：同意 1 ×1（5 个品）、同意 2 ×3（#2 #3 #4）、读回不一致 ×1（#1，后台价 ¥2,680≠批准价 ¥2,480，已挂起 3 小时）。授权示例：选品同意 · 家居收纳/厨房小工具 · 毛利≥28% · ≤3/日 · 到期 2026-11-12 · 已用 2/10 · 抽检 20%。
