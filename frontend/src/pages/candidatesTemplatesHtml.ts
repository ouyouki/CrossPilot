// 行详情模板:原样取自 03-candidates.html 的 <template id="d-...">。
// 点行时由外壳按 id 取内容填进右栏(原型 cp2.js 的行为)。
export const candidatesTemplatesHtml = String.raw`<template id="d-1">
  <div class="dhead"><div class="ph" data-art="box"></div><div><span class="badge primary">候选 #1 · 可选</span><h2 lang="ja" style="margin-top:6px">折叠収納ボックス3個セット</h2><div class="small faint">折叠收纳箱三件套 · 家居收纳</div></div></div>
  <div class="kpis"><div><small>售价（税込）</small><b>¥2,480</b></div><div><small>毛利</small><b>31.7%</b></div><div><small>分数</small><b>82</b></div></div>
  <div class="why1">类目榜第 7 位，同类在架少，毛利 31.7% 接近目标 32%。</div>
  <h3>成本瀑布 · 利润 ¥785</h3>
  <div class="chart" data-chart="waterfall" data-cfg='{"w":340,"lw":84,"rowH":24,"items":[{"label":"营收","value":2480,"type":"revenue"},{"label":"c1 采购","value":666,"type":"cost","color":"s1","tip":"c1 采购价 ¥666 = 32 CNY × 20.8 · 已确认"},{"label":"c2 国内运费","value":62,"type":"cost","color":"s1"},{"label":"c3 国际运费","value":520,"type":"cost","color":"s1","tip":"c3 ¥520 · 费率卡运费表 · 估算"},{"label":"c6 通関费","value":30,"type":"cost","color":"s1"},{"label":"c7 包材","value":25,"type":"cost","color":"s1"},{"label":"c8 佣金 10%","value":248,"type":"cost","color":"s4"},{"label":"c9 手续费 3%","value":74,"type":"cost","color":"s4"},{"label":"c10 退货损耗","value":70,"type":"cost","color":"s2"},{"label":"利润","value":785,"type":"profit"}],"legend":[{"label":"到岸成本 c1–c7","color":"s1"},{"label":"佣金手续费","color":"s4"},{"label":"退货损耗","color":"s2"}]}'></div>
  <details class="ev" style="margin-top:10px"><summary><span class="small"><b>成本分项与来源</b> · c4 c5 c11–13 = ¥0</span></summary><div class="body">
    <table class="ctab">
      <tr><td>c1 采购价<span class="sub">货源录入 · 10-19 · 已确认</span></td><td>¥666</td></tr>
      <tr><td>c2 国内段运费<span class="sub">货源录入 · 10-19 · 已确认</span></td><td>¥62</td></tr>
      <tr><td>c3 国际运费<span class="sub">费率卡运费表 · 10-15 · <span class="badge wait" style="height:18px">估算</span></span></td><td>¥520</td></tr>
      <tr><td>c4 关税 / c5 输入消费税<span class="sub">费率卡税口径 · 10-15 · 已确认</span></td><td>¥0</td></tr>
      <tr><td>c6 通関费 / c7 包材<span class="sub">费率卡 · 10-15 · 已确认</span></td><td>¥55</td></tr>
      <tr class="tot"><td>到岸小计 c1–c7</td><td>¥1,303</td></tr>
      <tr><td>c8 佣金 / c9 手续费 / c10 退货损耗<span class="sub">费率卡 · 10-15 · 已确认</span></td><td>¥392</td></tr>
      <tr class="tot"><td>总成本 · 利润</td><td>¥1,695 · ¥785</td></tr>
    </table><p class="small faint" style="margin:6px 0 0">测算，非申报依据。</p></div></details>
  <h3>打分分解</h3>
  <div class="row top" style="gap:6px">
    <div class="chart" data-chart="radar" data-cfg='{"size":170,"axes":[{"label":"需求","value":0.98},{"label":"利润","value":0.99},{"label":"竞争空档","value":0.94},{"label":"低风险","value":0.92}]}'></div>
    <table class="ctab" style="flex:1"><tr><td>需求 98×.35</td><td>+34.3</td></tr><tr><td>利润 99×.35</td><td>+34.5</td></tr><tr><td>竞争 94×.15</td><td>+14.1</td></tr><tr><td>风险 8×.15</td><td>−1.2</td></tr><tr class="tot"><td>总分</td><td>82</td></tr></table>
  </div>
  <h3>近 14 天类目榜名次</h3>
  <div class="row"><div class="chart" data-chart="spark" data-cfg='{"values":[11,12,13,13,15,16,16,18,19,20,21,22,22,23],"color":"primary","w":200,"h":40}'></div><div class="right" style="text-align:right"><b style="font-size:20px">#7</b><div class="small" style="color:var(--ok)">▲ 12 位</div></div></div>
  <div class="small faint">来源 <span class="grade A">A</span> 卖家后台榜单导出 · <span class="src m">手动 CSV</span> · 2026-10-19 22:10</div>
  <h3>G0 品类准入</h3>
  <ul class="g0">
    <li><span class="ic y">✓</span><span>类目白名单：家居收纳</span><span class="src">类目规则截图 · 10-12 · 林薇</span></li>
    <li><span class="ic y">✓</span><span>电池 · 无线 · 食品接触 · 儿童用品：无</span><span class="src">风险词库 10-20 版</span></li>
    <li><span class="ic y">✓</span><span>强磁 · 刃物 · 承运商禁运：无</span><span class="src">承运商清单 10-15</span></li>
    <li><span class="ic y">✓</span><span>品牌 / IP 疑似：未命中</span><span class="src">避开项 v6</span></li>
  </ul>
  <h3>方向卡</h3>
  <p class="small muted" style="margin:0">按方向 v6 生成（底线 15%，目标 32%）。之后的版本不改变这条候选。</p>
</template>
<template id="d-2">
  <div class="dhead"><div class="ph" data-art="spoons"></div><div><span class="badge primary">候选 #2 · 可选</span><h2 lang="ja" style="margin-top:6px">シリコン調理スプーン5点セット</h2><div class="small faint">硅胶厨具五件套 · 厨房小工具</div></div></div>
  <div class="kpis"><div><small>售价（税込）</small><b>¥1,980</b></div><div><small>毛利</small><b>34.2%</b></div><div><small>分数</small><b>79</b></div></div>
  <div class="why1">近 7 日榜单上升 12 位，毛利 34.2% 为今日最高，竞争中等。</div>
  <h3>成本瀑布 · 利润 ¥677</h3>
  <div class="chart" data-chart="waterfall" data-cfg='{"w":340,"lw":84,"rowH":24,"items":[{"label":"营收","value":1980,"type":"revenue"},{"label":"c1 采购","value":499,"type":"cost","color":"s1","tip":"c1 ¥499 = 24 CNY × 20.8"},{"label":"c2 国内运费","value":62,"type":"cost","color":"s1"},{"label":"c3 国际运费","value":380,"type":"cost","color":"s1"},{"label":"c6 通関费","value":30,"type":"cost","color":"s1"},{"label":"c7 包材","value":22,"type":"cost","color":"s1"},{"label":"c8 佣金 10%","value":198,"type":"cost","color":"s4"},{"label":"c9 手续费 3%","value":59,"type":"cost","color":"s4"},{"label":"c10 退货损耗","value":53,"type":"cost","color":"s2"},{"label":"利润","value":677,"type":"profit"}],"legend":[{"label":"到岸成本 c1–c7","color":"s1"},{"label":"佣金手续费","color":"s4"},{"label":"退货损耗","color":"s2"}]}'></div>
  <h3>打分分解</h3>
  <div class="row top" style="gap:6px">
    <div class="chart" data-chart="radar" data-cfg='{"size":170,"axes":[{"label":"需求","value":0.94},{"label":"利润","value":1},{"label":"竞争空档","value":0.78},{"label":"低风险","value":0.95}]}'></div>
    <table class="ctab" style="flex:1"><tr><td>需求 94×.35</td><td>+32.9</td></tr><tr><td>利润 100×.35</td><td>+35.0</td></tr><tr><td>竞争 78×.15</td><td>+11.7</td></tr><tr><td>风险 5×.15</td><td>−0.8</td></tr><tr class="tot"><td>总分</td><td>79</td></tr></table>
  </div>
  <h3>近 14 天类目榜名次</h3>
  <div class="row"><div class="chart" data-chart="spark" data-cfg='{"values":[6,6,7,6,8,9,9,10,12,13,15,16,17,18],"color":"primary","w":200,"h":40}'></div><div class="right" style="text-align:right"><b style="font-size:20px">#12</b><div class="small" style="color:var(--ok)">▲ 12 位</div></div></div>
  <h3>G0 品类准入</h3>
  <ul class="g0">
    <li><span class="ic y">✓</span><span>类目白名单：厨房小工具</span><span class="src">类目规则截图 · 10-12 · 林薇</span></li>
    <li><span class="ic y">✓</span><span>食品接触：有 · 白名单条目允许，附检测报告</span><span class="src">检测报告 · 10-12</span></li>
    <li><span class="ic y">✓</span><span>电池 · 无线 · 儿童用品 · 强磁 · 刃物 · 承运商禁运：无</span><span class="src">风险词库 10-20 版</span></li>
    <li><span class="ic y">✓</span><span>品牌 / IP 疑似：未命中</span><span class="src">避开项 v6</span></li>
  </ul>
  <h3>方向卡</h3>
  <p class="small muted" style="margin:0">按方向 v6 生成。</p>
</template>
<template id="d-5">
  <div class="dhead"><div class="ph" data-art="cup"></div><div><span class="badge wait">候选 #5 · 数据不全</span><h2 lang="ja" style="margin-top:6px">折りたたみシリコンカップ</h2><div class="small faint">折叠硅胶杯 · 厨房小工具</div></div></div>
  <div class="kpis"><div><small>售价（税込）</small><b>¥1,480</b></div><div><small>毛利</small><b>28.4%</b></div><div><small>分数</small><b>71</b></div></div>
  <div class="alert wait" style="margin:8px 0"><span><b>数据不全，勾选前需你确认</b><br>季节标注缺失；需求信号只有截图识别（C），未经榜单导出核对。分数可排序，但可信度较低。</span></div>
  <label class="chk" style="background:var(--surface-2);border-radius:10px;padding:10px 12px;width:100%"><input type="checkbox" id="ack5"> 我已逐项看过缺口，同意带着缺口进入同意 1</label>
  <h3>成本瀑布 · 利润 ¥420</h3>
  <div class="chart" data-chart="waterfall" data-cfg='{"w":340,"lw":84,"rowH":24,"items":[{"label":"营收","value":1480,"type":"revenue"},{"label":"c1 采购","value":374,"type":"cost","color":"s1","tip":"c1 ¥374 = 18 CNY × 20.8"},{"label":"c2 国内运费","value":62,"type":"cost","color":"s1"},{"label":"c3 国际运费","value":320,"type":"cost","color":"s1","tip":"c3 按类目典型重量估算；货源阶段需填实重"},{"label":"c6 通関费","value":30,"type":"cost","color":"s1"},{"label":"c7 包材","value":20,"type":"cost","color":"s1"},{"label":"c8 佣金 10%","value":148,"type":"cost","color":"s4"},{"label":"c9 手续费 3%","value":44,"type":"cost","color":"s4"},{"label":"c10 退货损耗","value":62,"type":"cost","color":"s2"},{"label":"利润","value":420,"type":"profit"}],"legend":[{"label":"到岸成本 c1–c7","color":"s1"},{"label":"佣金手续费","color":"s4"},{"label":"退货损耗","color":"s2"}]}'></div>
  <h3>打分分解</h3>
  <div class="row top" style="gap:6px">
    <div class="chart" data-chart="radar" data-cfg='{"size":170,"axes":[{"label":"需求","value":0.9},{"label":"利润","value":0.82},{"label":"竞争空档","value":0.8},{"label":"低风险","value":0.94}]}'></div>
    <table class="ctab" style="flex:1"><tr><td>需求 90×.35<span class="sub">仅 C 级信号</span></td><td>+31.5</td></tr><tr><td>利润 82×.35</td><td>+28.7</td></tr><tr><td>竞争 80×.15</td><td>+12.0</td></tr><tr><td>风险 6×.15</td><td>−0.9</td></tr><tr class="miss"><td>季节标注</td><td>缺</td></tr><tr class="tot"><td>总分</td><td>71</td></tr></table>
  </div>
  <h3>近 14 天榜单名次</h3>
  <div class="alert" style="font-size:14px"><span>只有 10-19 一次截图识别（第 23 位），无法画趋势。导入榜单 CSV 后补齐。</span></div>
  <h3>G0 品类准入</h3>
  <ul class="g0">
    <li><span class="ic y">✓</span><span>类目白名单：厨房小工具</span><span class="src">类目规则截图 · 10-12</span></li>
    <li><span class="ic y">✓</span><span>食品接触：有 · 白名单允许，附检测报告</span><span class="src">检测报告 · 10-12</span></li>
    <li><span class="ic y">✓</span><span>其余 6 项旗标：无</span><span class="src">风险词库 10-20 版</span></li>
  </ul>
  <h3>方向卡</h3>
  <p class="small muted" style="margin:0">按方向 v6 生成。</p>
</template>
<template id="d-gen">
  <h3>候选详情</h3>
  <p class="small muted">演示数据只为 #1、#2、#5 准备了完整的成本、打分与准入记录。</p>
  <div class="row wrap"><button class="btn sm" data-open="d-1">看 #1</button><button class="btn sm" data-open="d-2">看 #2</button><button class="btn sm" data-open="d-5">看 #5（数据不全）</button></div>
</template>
<template id="d-nd1">
  <div class="dhead"><div class="ph" data-art="whisk"></div><div><span class="badge wait">数据待补</span><h2 lang="ja" style="margin-top:6px">シリコン泡立て器</h2><div class="small faint">硅胶打蛋器 · 厨房小工具 · 售价 ¥1,280</div></div></div>
  <div class="bigna"><b>利润不可算</b><span class="small">缺 c3 国际运费：货源页未填重量，查不到运费档位。补齐前不显示毛利与分数。</span></div>
  <h3>成本分项</h3>
  <div class="mcost">
    <div class="r"><span>营收</span><span class="bar rev" style="width:100%"></span><b>¥1,280</b></div>
    <div class="r"><span>c1 采购</span><span class="bar" style="width:24%"></span><b>¥312</b></div>
    <div class="r"><span>c2 国内运费</span><span class="bar" style="width:5%"></span><b>¥62</b></div>
    <div class="r m"><span>c3 国际运费</span><span class="bar miss" style="width:40%"></span><b>缺</b></div>
    <div class="r"><span>c6–c7</span><span class="bar" style="width:4%"></span><b>¥48</b></div>
    <div class="r"><span>c8–c9</span><span class="bar fee" style="width:13%"></span><b>¥166</b></div>
    <div class="r m"><span>c10 退货损耗</span><span class="bar miss" style="width:5%"></span><b>缺</b></div>
    <div class="r m"><span>利润</span><span class="bar miss" style="width:20%"></span><b>不可算</b></div>
  </div>
  <p class="small faint" style="margin:8px 0 0">c10 依赖 c3 所在的退运费估算，一并待补。不会用默认值代替。</p>
  <h3>去补</h3>
  <div class="row wrap"><a class="btn sm primary" href="04-sourcing.html">去货源页补重量</a><span class="small faint">同类缺口还有 2 个，补完一起解锁</span></div>
  <h3>G0 品类准入</h3>
  <ul class="g0"><li><span class="ic y">✓</span><span>类目白名单：厨房小工具</span><span class="src">10-12</span></li><li><span class="ic y">✓</span><span>旗标：食品接触 有（白名单允许）；其余无</span><span class="src">风险词库</span></li></ul>
</template>
<template id="d-nd2">
  <div class="dhead"><div class="ph" data-art="basket"></div><div><span class="badge wait">数据待补</span><h2 lang="ja" style="margin-top:6px">折りたたみ洗濯かご</h2><div class="small faint">折叠洗衣篮 · 家居收纳 · 售价 ¥1,980</div></div></div>
  <div class="bigna"><b>利润不可算</b><span class="small">缺税口径：c4 关税与 c5 输入消费税不可算。补齐前不显示毛利与分数。</span></div>
  <h3>成本分项</h3>
  <div class="mcost">
    <div class="r"><span>营收</span><span class="bar rev" style="width:100%"></span><b>¥1,980</b></div>
    <div class="r"><span>c1–c3</span><span class="bar" style="width:46%"></span><b>¥910</b></div>
    <div class="r m"><span>c4 关税</span><span class="bar miss" style="width:8%"></span><b>缺</b></div>
    <div class="r m"><span>c5 输入消费税</span><span class="bar miss" style="width:8%"></span><b>缺</b></div>
    <div class="r"><span>c6–c10</span><span class="bar fee" style="width:18%"></span><b>¥360</b></div>
    <div class="r m"><span>利润</span><span class="bar miss" style="width:20%"></span><b>不可算</b></div>
  </div>
  <h3>去补</h3>
  <a class="btn sm primary" href="10-settings.html">去设置补税口径</a>
</template>
<template id="d-bk1">
  <div class="dhead dimhead"><div class="ph" data-art="earbuds"></div><div><span class="badge block">不可售</span><h2 lang="ja" style="margin-top:6px">Bluetoothイヤホン</h2><div class="small faint">蓝牙耳机 · 数码配件</div></div></div>
  <div class="alert block"><span><b>命中品类准入规则，不能选</b><br>不显示分数与毛利。</span></div>
  <h3>命中原因</h3>
  <div class="reasons"><span class="badge block">类目「数码配件」未登记</span><span class="badge block">含无线</span><span class="badge block">含电池</span></div>
  <h3>G0 品类准入</h3>
  <ul class="g0">
    <li><span class="ic n">✗</span><span>类目白名单：数码配件 未登记</span><span class="src">品类白名单 10-20</span></li>
    <li><span class="ic n">✗</span><span>无线：有（标题含 Bluetooth）</span><span class="src">风险词库 10-20 版</span></li>
    <li><span class="ic n">✗</span><span>电池：有（充電ケース）</span><span class="src">风险词库 10-20 版</span></li>
    <li><span class="ic y">✓</span><span>品牌 / IP 疑似：未命中</span><span class="src">避开项 v6</span></li>
  </ul>
  <p class="small muted" style="margin-top:12px">带电池 / 无线的电器在跨境直邮下是否可售尚未核实，默认不可售。要改变它，需要先在 <a href="10-settings.html">设置</a> 登记类目并附出处。</p>
</template>`;
