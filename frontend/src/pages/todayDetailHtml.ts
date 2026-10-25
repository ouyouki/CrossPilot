// 原样取自 design/screens/01-today.html 的 <template id="detail-tpl">(右栏详情)。
export const todayDetailHtml = String.raw`  <h3>Pilot 的今日简报</h3>
  <p class="muted" style="margin:0 0 14px;font-size:15px">早上好。夜里选出 12 个可选候选，其中 5 个进入了同意 1。素材线有 3 个品通过检查，等你批准；折叠収納ボックス 在后台价格被改成 ¥2,680，已挂起。</p>
  <div class="alert info"><span><b>建议先处理挂起项</b>：它已在平台上提交，价格不一致会影响毛利。</span></div>
  <h3>岗位员工状态</h3>
  <ul class="feed">
    <li><span class="dot ok"></span><div><b>Pilot</b> 项目经理<div class="t">待命 · 今日派活 14 次</div></div></li>
    <li><span class="dot ok"></span><div><b>Scout</b> 选品员<div class="t">夜间完成 · 03:10</div></div></li>
    <li><span class="dot ok"></span><div><b>Sourcer</b> 采集员<div class="t">等你确认货源</div></div></li>
    <li><span class="dot"></span><div><b>Creator</b> 素材员<div class="t">工作中 · 预算 21%</div></div></li>
    <li><span class="dot ok"></span><div><b>Lister</b> 上架员<div class="t">2 张清单已发放</div></div></li>
    <li><span class="dot ok"></span><div><b>Checker</b> 质检员<div class="t">复核完成 10:42</div></div></li>
  </ul>
  <h3>红线提醒</h3>
  <p class="small muted" style="margin:0">未批准绝不执行；未决期间挂起等待，不自动放行也不自动放弃。Agent 默认无批准权。</p>`;
