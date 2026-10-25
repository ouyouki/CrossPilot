// 行详情模板:原样取自 06-approvals.html。
export const approvalsTemplatesHtml = String.raw`<template id="d-c1">
  <h3>同意 1 · 前置条件</h3>
  <ul class="pc">
    <li><span class="ck">✓</span><span>汇率偏离</span><span class="cv">1.2%（≤3%）</span></li>
    <li><span class="ck">✓</span><span>5 行毛利 ≥ 底线</span><span class="cv">最低 28.4%</span></li>
    <li><span class="ck">✓</span><span>G0 全部通过</span><span class="cv">5 / 5</span></li>
    <li><span class="ck">✓</span><span>方向卡未变</span><span class="cv">v7</span></li>
    <li><span class="ck" style="background:var(--wait-bg);color:var(--wait)">!</span><span>数据完整</span><span class="cv" style="color:var(--wait)">4 / 5（1 行待补）</span></li>
  </ul>
  <h3>审批单时间线</h3>
  <ul class="timeline">
    <li><span class="pt"></span><div class="when">03:10 · SCOUT</div><div class="what">夜间选品：24 个候选入库</div></li>
    <li><span class="pt"></span><div class="when">08:30 · PILOT</div><div class="what">打包同意 1：5 个品，通知你</div></li>
    <li><span class="pt wait"></span><div class="when">09:30 · 提醒</div><div class="what">+1 小时提醒（仅提醒）</div></li>
    <li><span class="pt wait"></span><div class="when">12:30 · 升级</div><div class="what">+4 小时升级通知 Owner（仅提醒，不改变状态）</div></li>
    <li><span class="pt" style="border-color:var(--border-strong)"></span><div class="when">明日 08:30 · 预定</div><div class="what faint">每 24 小时再提醒</div></li>
  </ul>
  <h3>代批记录</h3>
  <p class="small muted" style="margin:0">现有授权「家居收纳/厨房小工具 · 毛利 ≥28%」已用 2/10；本单含数据不全的行，超出授权，回到你手里。</p>
</template>
<template id="d-held">
  <h3>挂起 · 说明</h3>
  <p class="small muted">挂起是等你，不是倒计时。期间系统不会替你放行，也不会替你放弃。</p>
  <h3>折叠収納ボックス · 经过</h3>
  <ul class="timeline">
    <li><span class="pt human"></span><div class="when">10-19 18:40 · 林薇</div><div class="what">批准同意 2 · ¥2,480</div></li>
    <li><span class="pt"></span><div class="when">10-19 18:41 · LISTER</div><div class="what">生成执行清单</div></li>
    <li><span class="pt human"></span><div class="when">11:20 · 林薇</div><div class="what">回填后台实际值（自批自执）</div></li>
    <li><span class="pt block"></span><div class="when">11:20 · 读回</div><div class="what">価格 ¥2,680 ≠ ¥2,480 → 挂起</div></li>
  </ul>
</template>
<template id="d-void">
  <h3>作废 · 说明</h3>
  <p class="small muted">原批准作废后，商品回到流水线重新判定；结果仍需人批时才生成后继单。系统不会“按批准的精神”调参数继续执行。</p>
  <h3>差异</h3>
  <dl class="kv"><dt>失效前置</dt><dd>汇率偏离 &gt;3%</dd><dt>汇率</dt><dd>20.80 → 21.55</dd><dt>到岸成本</dt><dd>¥1,090 → ¥1,128</dd><dt>毛利</dt><dd>28.4% → 26.9%</dd></dl>
</template>`;
