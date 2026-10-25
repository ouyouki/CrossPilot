// 原样取自 design/screens/06-approvals.html 的 <template id="detail-tpl">。
export const approvalsDetailHtml = String.raw`  <h3>同意 2 · 前置条件</h3>
  <p class="small muted" style="margin:0 0 10px">审批期间持续检查，执行前再检一遍；任一失效原单作废。</p>
  <div class="fxrow">
    <div class="chart" data-chart="gauge" data-cfg='{"pct":40,"w":120,"h":72,"stroke":9,"label":"1.2%","color":"ok","tip":"当前 21.05 · 快照 20.80 · 容忍 ≤3%"}'></div>
    <div class="small"><b>汇率偏离 1.2%</b><div class="faint">容忍 ≤3% · 用了 40%</div></div>
  </div>
  <ul class="pc">
    <li><span class="ck">✓</span><span>毛利 ≥ 底线</span><span class="cv">34.2% ≥ 12%</span><div class="meter ok"><i style="width:86%"></i></div></li>
    <li><span class="ck">✓</span><span>售价 &gt; 地板价</span><span class="cv">¥1,980 &gt; ¥1,178</span></li>
    <li><span class="ck">✓</span><span>货源价无变动</span><span class="cv">0.0%（≤5%）</span></li>
    <li><span class="ck">✓</span><span>规则库无新阻断</span><span class="cv">10-20 版</span></li>
    <li><span class="ck">✓</span><span>店铺档案无变更</span><span class="cv">10-12 确认</span></li>
    <li><span class="ck">✓</span><span>汇率取数未过期</span><span class="cv">5 小时前（≤24h）</span></li>
    <li><span class="ck">✓</span><span>货源确认未过期</span><span class="cv">2 天前（≤7 天）</span></li>
    <li><span class="ck">✓</span><span>素材未改动</span><span class="cv">v1 与批准内容一致</span></li>
  </ul>
  <h3>事实快照</h3>
  <dl class="kv"><dt>方向卡</dt><dd>v7</dd><dt>费率卡</dt><dd>v12 · 2026-10-19</dd><dt>汇率</dt><dd>20.80 · 10-20 09:00</dd><dt>规则库</dt><dd>2026-10-20 版</dd><dt>店铺档案</dt><dd>已确认 · 10-12</dd></dl>
  <h3>审批单时间线</h3>
  <ul class="timeline">
    <li><span class="pt ok"></span><div class="when">10:42 · CHECKER</div><div class="what">复核完成：成本与 G0–G4 复算一致</div></li>
    <li><span class="pt"></span><div class="when">13:30 · PILOT</div><div class="what">打包同意 2，通知你</div></li>
    <li><span class="pt wait"></span><div class="when">14:30 · 提醒</div><div class="what">+1 小时提醒（仅提醒，不改变状态）</div></li>
    <li><span class="pt" style="border-color:var(--border-strong)"></span><div class="when">17:30 · 预定</div><div class="what faint">+4 小时升级通知 Owner（仅提醒）</div></li>
  </ul>
  <h3>代批记录</h3>
  <p class="small muted" style="margin:0">无。同意 2 不可授权，永远由你本人批。</p>`;
