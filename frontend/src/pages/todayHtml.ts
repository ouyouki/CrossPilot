// 原样取自 design/screens/01-today.html 的 <template id="main-tpl">。
// 为什么原样搬:这一步的目标是「和原型一模一样」;数据绑定在后续 Issue 里逐个区块做。
// 先改结构会同时引入「长得不一样」和「数据和原型不一致」两类问题,分不清是谁的错。
export const todayHtml = String.raw`  <div class="dark-panel" style="margin-bottom:16px">
    <div class="row top" style="gap:28px;flex-wrap:wrap">
      <div style="flex:1;min-width:320px;position:relative;z-index:1">
        <span class="eyebrow" style="color:var(--accent-on-dark)">TODAY · 2026-10-20 周二</span>
        <h1 style="font-size:32px;letter-spacing:-.02em">今天有 5 件事等你</h1>
        <p class="muted" style="margin:6px 0 18px;font-size:16px">预计 25 分钟。夜间选品已完成，Pilot 已把 3 个品的素材和 1 份选品清单打包好了。</p>
        <div class="row wrap">
          <a class="btn primary lg" href="06-approvals.html">去处理第一件</a>
          <a class="btn lg" style="background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.18);color:#fff" href="06-approvals.html">查看全部待批</a>
        </div>
      </div>
      <div class="row" style="gap:22px;position:relative;z-index:1">
        <div class="chart" data-chart="ring" data-cfg='{"pct":11,"size":112,"stroke":11,"label":"4m20s","sub":"决策用时","color":"primary","fs":19,"tip":"今日已决定 3 次，合计 4 分 20 秒；日预算 40 分钟"}'></div>
        <div style="font-size:15px;line-height:1.9">
          <div class="faint">今日已决定</div><div style="font-size:24px;font-weight:600;color:#fff">3 次</div>
          <div class="faint" style="margin-top:6px">日预算</div><div style="color:#DCEBEA">40 分钟 · 已用 11%</div>
        </div>
      </div>
    </div>
    <div style="margin-top:26px;position:relative;z-index:1">
      <div class="route">
        <a class="wp done" href="03-candidates.html"><span class="node">24</span><b>候选</b><span class="s">可选 12 · 待补 7<br>不可售 5</span></a>
        <a class="wp wait" href="06-approvals.html"><span class="node">5</span><b>同意 1</b><span class="s">等你批<br>6 小时</span></a>
        <a class="wp done" href="04-sourcing.html"><span class="node">4</span><b>采集</b><span class="s">货源确认中<br>1 个缺重量</span></a>
        <a class="wp done" href="05-assets.html"><span class="node">3</span><b>素材</b><span class="s">已通过检查<br>1 条 WARN</span></a>
        <a class="wp wait" href="06-approvals.html"><span class="node">3</span><b>同意 2</b><span class="s">等你批<br>最久 1 小时</span></a>
        <a class="wp now" href="07-listing.html"><span class="node">2</span><b>上架</b><span class="s">执行清单<br>1 个读回不一致</span></a>
        <a class="wp" href="07-listing.html"><span class="node">1</span><b>LIVE</b><span class="s">平台审核通过<br>本周共 7 个</span></a>
      </div>
    </div>
  </div>

  <div class="card" style="margin-bottom:16px;padding:14px 20px">
    <div class="row wrap" style="gap:10px 18px">
      <b style="font-size:16px">起飞前检查</b><span class="badge ok">6 / 6 就绪</span>
      <span class="small muted row" style="gap:16px;flex-wrap:wrap">
        <span>✓ 方向卡 v7</span><span>✓ 费率卡 v12</span><span>✓ 品类白名单 4 项</span><span>✓ 店铺档案已确认</span><span>✓ 规则库 10-20 版</span><span>✓ 模型预算 ¥1,500/日</span>
      </span>
      <a class="right small" href="10-settings.html">查看设置</a>
    </div>
  </div>

  <a class="card conn-card" href="10-settings.html#conn" aria-label="数据连接：7 个连接器，1 项待你确认。进入设置的数据连接">
    <div class="row wrap" style="gap:10px 18px">
      <b style="font-size:16px">数据连接</b><span class="badge wait">1 项待确认</span>
      <span class="small muted">汇率 09:00 已更新；1 项待你确认（汇率突变）</span>
      <span class="right small" style="color:var(--primary)">进入数据连接 →</span>
    </div>
    <ul class="cdots" style="margin-top:10px">
      <li data-tip="欧洲央行参考汇率 · 09:00 成功 · 备源 21.55（+3.6%）暂存待确认"><i class="wait"></i>汇率</li>
      <li data-tip="日本海关税率表 · 2026 年 10 月版"><i></i>关税率</li>
      <li data-tip="内阁府 CSV · 覆盖至 2027-12-31"><i></i>节假日</li>
      <li data-tip="报价表 v3 · 有效期至 2026-12-31"><i></i>国际运费</li>
      <li data-tip="未配置 · 手工 CSV 兜底"><i class="off"></i>榜单与竞品</li>
      <li data-tip="授权采集工具 · 今日 08:40 · 1 条缺重量"><i></i>货源采集</li>
      <li data-tip="每日检测 · 近 7 日无变化"><i></i>费率页提醒</li>
      <li class="faint small" style="margin-left:auto">绿 = 新鲜 · 琥珀 = 待确认 / 将过期 · 灰 = 未配置</li>
    </ul>
  </a>

  <div class="g4" style="margin-bottom:16px">
    <div class="stat wait"><div class="k">待你批</div><div class="v">4</div><div class="n">同意 1 ×1 · 同意 2 ×3</div>
      <div class="spark chart" data-chart="spark" data-cfg='{"values":[2,3,5,4,6,5,4],"color":"wait"}'></div></div>
    <div class="stat block"><div class="k">挂起（需你处理）</div><div class="v">1</div><div class="n">读回不一致 · 已 3 小时</div>
      <div class="spark chart" data-chart="spark" data-cfg='{"values":[0,0,1,0,0,2,1],"color":"block"}'></div></div>
    <div class="stat"><div class="k">本周上架（LIVE）</div><div class="v">7 <small>个</small></div><div class="d up">▲ 2 比上周</div>
      <div class="spark chart" data-chart="spark" data-cfg='{"values":[1,0,2,1,3,2,4],"color":"primary"}'></div></div>
    <div class="stat"><div class="k">在制品平均毛利</div><div class="v">31.4<small>%</small></div><div class="d up">▲ 1.2 点 · 底线 12%</div>
      <div class="spark chart" data-chart="spark" data-cfg='{"values":[28.4,29,30.1,29.6,30.8,31,31.4],"color":"ok"}'></div></div>
  </div>

  <div class="g-main" style="margin-bottom:16px">
    <div class="card flush">
      <div class="card-head"><h2>等你拍板</h2><span class="meta">按风险与挂起时长排序，高风险不折叠</span><div class="tools"><a class="btn sm" href="06-approvals.html">打开待批</a></div></div>
      <div class="tblwrap"><table class="tbl">
        <thead><tr><th>对象</th><th>类型</th><th>影响</th><th class="num">已挂起</th></tr></thead>
        <tbody>
          <tr><td><div class="prod"><span class="thumb" data-art="box"></span><div><div class="t"><a href="07-listing.html" lang="ja">折叠収納ボックス3個セット</a></div><div class="s">后台价格 ¥2,680 ≠ 批准价 ¥2,480 · 去后台改价或下架</div></div></div></td><td><span class="badge block">读回不一致</span></td><td class="small">已在后台提交</td><td class="num">3 小时</td></tr>
          <tr><td><div class="prod"><span class="thumb" data-art="spoons"></span><div><div class="t"><a href="06-approvals.html" lang="ja">シリコン調理スプーン5点セット</a></div><div class="s">对外可见 · 不可撤回 · 毛利 34.2%</div></div></div></td><td><span class="badge wait">同意 2</span></td><td class="small">售价 ¥1,980</td><td class="num">1 小时</td></tr>
          <tr><td><div class="prod"><span class="thumb" data-art="cable"></span><div><div class="t"><a href="06-approvals.html" lang="ja">デスクケーブルオーガナイザー</a></div><div class="s">2 条 WARN 待确认 · 毛利 29.8%</div></div></div></td><td><span class="badge wait">同意 2</span></td><td class="small">售价 ¥1,680</td><td class="num">1 小时</td></tr>
          <tr><td><div class="prod"><span class="thumb" data-art="brush"></span><div><div class="t"><a href="06-approvals.html" lang="ja">ペット用ブラシ 抜け毛クリーナー</a></div><div class="s">毛利 33.0%</div></div></div></td><td><span class="badge wait">同意 2</span></td><td class="small">售价 ¥1,880</td><td class="num">45 分钟</td></tr>
          <tr><td><div class="prod"><span class="thumb" style="background:var(--surface-3);display:grid;place-items:center;font-weight:600;color:var(--text-2)">×5</span><div><div class="t"><a href="06-approvals.html">选 5 个品进入采集</a></div><div class="s">1 行数据不全，需逐行展开确认</div></div></div></td><td><span class="badge wait">同意 1</span></td><td class="small">预计毛利 28.4%–34.2%</td><td class="num">6 小时</td></tr>
        </tbody>
      </table></div>
    </div>

    <div class="stack">
      <div class="card">
        <div class="card-head"><h2>今日漏斗</h2><span class="meta">候选 → LIVE</span></div>
        <div class="chart" data-chart="hbars" data-cfg='{"lw":70,"color":"primary","items":[{"label":"候选","value":24,"text":"24"},{"label":"可选","value":12,"text":"12"},{"label":"已选","value":5,"text":"5"},{"label":"采集","value":4,"text":"4"},{"label":"素材","value":3,"text":"3"},{"label":"上架","value":2,"text":"2"},{"label":"LIVE","value":1,"text":"1","color":"ok"}]}'></div>
        <p class="small faint" style="margin:12px 0 0">7 个候选在“数据待补”，补 c3 国际运费可解锁 3 个。<a href="03-candidates.html">去补</a></p>
      </div>
      <div class="card">
        <div class="card-head"><h2>可选候选的毛利分布</h2></div>
        <div class="chart" data-chart="hist" data-cfg='{"w":320,"h":110,"values":[0,1,2,4,3,2,1,0,0],"labels":["10%","15%","20%","25%","30%","35%","40%","45%","50%"],"highlight":[2,6],"color":"primary","unit":" 个","marks":[{"at":0.1,"label":"底线 12%","color":"block"}]}'></div>
      </div>
    </div>
  </div>

  <div class="g2" style="margin-bottom:16px">
    <div class="card">
      <div class="card-head"><h2>AI 干活，人只批</h2><span class="meta">近 14 天 · 每日动作数</span></div>
      <div class="chart" data-chart="line" data-cfg='{"w":520,"h":190,"labels":["10-07","10-08","10-09","10-10","10-11","10-12","10-13","10-14","10-15","10-16","10-17","10-18","10-19","10-20"],"unit":"","series":[{"name":"自动完成","color":"s1","values":[46,52,48,60,58,44,50,66,72,70,78,82,80,86]},{"name":"人工决定","color":"s2","values":[8,7,6,9,7,5,6,8,7,6,5,6,5,3],"dash":false}]}'></div>
      <div class="g3" style="margin-top:14px">
        <div><div class="small faint">今日人工决定</div><b style="font-size:20px">3 次</b></div>
        <div><div class="small faint">7 日均</div><b style="font-size:20px">5.1 次</b></div>
        <div><div class="small faint">自动 / 人工</div><b style="font-size:20px">28 : 1</b></div>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><h2>去后台处理</h2><span class="meta">一条提醒 + 一个跳转</span></div>
      <ul class="feed">
        <li><span class="dot wait"></span><div>已上架的 1 个商品，后台价格低于你的毛利底线<div class="t"><a href="#" data-toast="跳转：TikTok Shop 卖家后台（演示）">去后台改价 →</a></div></div></li>
        <li><span class="dot wait"></span><div>保证金可用余额需在后台确认（预警线 ¥150,000）<div class="t"><a href="#" data-toast="跳转：TikTok Shop 卖家后台（演示）">去后台查看 →</a></div></div></li>
        <li><span class="dot"></span><div>联盟公开计划：本周上架的 3 个品尚未确认佣金率<div class="t"><a href="07-listing.html">去上架清单确认 →</a></div></div></li>
      </ul>
      <div class="alert wait" style="margin-top:12px"><span><b>本周体检未录入（盲区）</b><br>本期不自动读取履约指标（迟发率、取消率等）；请每周在后台查看并录入。</span><button class="btn sm right" data-toast="打开体检录入（演示）">录入</button></div>
    </div>
  </div>

  <div class="card">
    <div class="card-head"><h2>Agent 刚刚做了什么</h2><span class="meta">来自审计的只读视图 · 含被拒绝的尝试</span><div class="tools"><a class="btn sm" href="09-audit.html">全部</a></div></div>
    <ul class="timeline">
      <li><span class="pt ok"></span><div class="when">10:42 · CHECKER</div><div class="what">复核完成：3 套素材，成本与 G0–G4 复算一致</div></li>
      <li><span class="pt block"></span><div class="when">10:31 · CREATOR · 被拒绝</div><div class="what">尝试使用 license_type=none 的图 → 被 G3-001 拦截，已改用供应商授权图</div></li>
      <li><span class="pt"></span><div class="when">10:12 · CREATOR</div><div class="what">生成 シリコン調理スプーン 的标题/卖点/9 图/视频 · 预算已用 ¥312/¥1,500</div></li>
      <li><span class="pt wait"></span><div class="when">08:30 · PILOT</div><div class="what">打包同意 1：5 个品，等你批（已挂起 6 小时，不会过期）</div></li>
      <li><span class="pt"></span><div class="when">03:10 · SCOUT</div><div class="what">解析导入的榜单 40 行，24 个候选入库，7 个缺数据，5 个被 G0 拦截</div></li>
    </ul>
  </div>`;
