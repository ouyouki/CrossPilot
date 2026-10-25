// 原样取自 design/screens/06-approvals.html 的 <template id="main-tpl">。
export const approvalsHtml = String.raw`  <div class="page-head">
    <div>
      <span class="eyebrow">APPROVALS · 2026-10-20</span>
      <h1>待批：5 件在等你，预计 25 分钟</h1>
      <p>按风险、挂起时长、金额敞口与不可逆性排序（服务端优先级，不能改成按时间）</p>
    </div>
    <div class="actions">
      <div class="chart" data-chart="ring" data-cfg='{"pct":11,"size":52,"stroke":6,"label":"11%","color":"primary","fs":12,"tip":"今日已决定 3 次 · 4 分 20 秒 · 日预算 40 分钟"}'></div>
      <div class="small" style="line-height:1.4"><b>4m20s</b><div class="faint">今日决策用时</div></div>
      <button class="help" data-toast="操作手册：待批（演示）" aria-label="帮助">?</button>
    </div>
  </div>

  <div data-tabs>
    <div class="tabs" role="tablist" aria-label="审批类型">
      <button role="tab" data-tab="c2" aria-selected="true">同意 2<span class="n">3</span></button>
      <button role="tab" data-tab="c1" aria-selected="false">同意 1<span class="n">1</span></button>
      <button role="tab" data-tab="held" aria-selected="false">挂起<span class="n">1</span></button>
      <button role="tab" data-tab="void" aria-selected="false">已作废<span class="n">1</span></button>
    </div>

    <!-- ======================= 同意 2 ======================= -->
    <div data-pane="c2">
      <div class="aq">
        <div class="queue" aria-label="同意 2 队列">
          <h4>队列 · 服务端优先级</h4>
          <button class="qi sel" data-toast="当前单（演示）"><span class="thumb" data-art="spoons"></span>
            <span><span class="t" lang="ja">シリコン調理スプーン5点セット</span><span class="m">¥1,980 · 34.2% · <span class="badge wait" style="height:18px;font-size:12px">1 WARN</span></span></span>
            <span class="pr"><span>优先级</span><span class="meter"><i style="width:82%"></i></span><span>1 小时</span></span></button>
          <button class="qi" data-toast="演示：同一结构的另一张单"><span class="thumb" data-art="cable"></span>
            <span><span class="t" lang="ja">デスクケーブルオーガナイザー</span><span class="m">¥1,680 · 29.8% · <span class="badge wait" style="height:18px;font-size:12px">2 WARN</span></span></span>
            <span class="pr"><span>优先级</span><span class="meter"><i style="width:76%"></i></span><span>1 小时</span></span></button>
          <button class="qi" data-toast="演示：同一结构的另一张单"><span class="thumb" data-art="brush"></span>
            <span><span class="t" lang="ja">ペット用ブラシ 抜け毛クリーナー</span><span class="m">¥1,880 · 33.0%</span></span>
            <span class="pr"><span>优先级</span><span class="meter"><i style="width:61%"></i></span><span>45 分钟</span></span></button>
          <div class="qhint">快捷键 <kbd>A</kbd> 批准（满足查看条件时）· <kbd>R</kbd> 退回 · <kbd>Space</kbd> 展开下一块证据。批准没有撤销键。</div>
        </div>

        <div class="card flush" data-approval id="t2">
          <div class="tk">
            <div class="tk-head">
              <span class="thumb xl" data-art="spoons"></span>
              <div>
                <h2>批准上架「<span lang="ja">シリコン調理スプーン5点セット</span>」：售价 ¥1,980，毛利 34.2%</h2>
                <div class="sub">由 Pilot 打包 · 13:30 · 素材 v1 · 9 图 + 1 视频</div>
              </div>
              <div class="chart" data-chart="ring" data-cfg='{"pct":34.2,"size":88,"stroke":9,"label":"34.2%","sub":"毛利","color":"ok","fs":16,"tip":"利润 ¥677 ÷ 营收 ¥1,980 · 底线 12% · 目标 32%"}'></div>
            </div>
            <div class="badges">
              <span class="badge wait">同意 2</span><span class="badge block">对外可见</span><span class="badge block">不可撤回</span><span class="badge primary">需你本人批</span><span class="badge">单人运行</span>
            </div>
            <div class="lede"><b>必须先看这一句：</b>批准后生成上架清单；提交平台审核后无法撤回，只能去后台下架，且下架不会消除平台违规记录。</div>
            <div class="three">
              <div class="mini"><div class="k">影响面</div><div class="v">1 个商品 · 对外可见</div><div class="n">9 图 + 1 视频 · 在庫初值 30<br>到岸敞口 ¥29,790（30 × ¥993）</div></div>
              <div class="mini"><div class="k">为什么找你</div><div class="v">对外发布内容的同意</div><div class="n">毛利 34.2% ≥ 底线 12% · 0 BLOCK · 1 WARN · 不可授权</div></div>
              <div class="mini"><div class="k">时效</div><div class="v">长期有效，等待批准</div><div class="n">已挂起 1 小时 · 不会自动放行或放弃</div></div>
            </div>

            <div class="blk-t"><h3>批准后会发生什么</h3><span class="meta">一张单一个动作 · 逐字段</span></div>
            <table class="diff">
              <thead><tr><th>字段</th><th>现在</th><th>批准后</th><th>依据</th></tr></thead>
              <tbody>
                <tr><td>动作</td><td class="bf">未上架</td><td class="af"><span class="new">NEW</span>新建商品 1 个（不含改价、改库存）</td><td class="why">通道 A：生成执行清单，你在后台照做</td></tr>
                <tr><td>商品タイトル</td><td class="bf">—</td><td class="af" lang="ja">シリコン調理スプーン5点セット 耐熱 キッチンツール 食洗機対応</td><td class="why">G2 通过 · 38/60 字</td></tr>
                <tr><td>販売価格（税込）</td><td class="bf">—</td><td class="af">¥1,980</td><td class="why">建议价：满足底线 + 3pp 安全边际，落在竞品带 ¥1,780–2,480</td></tr>
                <tr><td>在庫初值 / 送料</td><td class="bf">—</td><td class="af">30 / <span lang="ja">送料無料（売主負担）</span></td><td class="why">送料已计入 c3；在庫 ≤ 供应商确认量 200</td></tr>
                <tr><td>発送までの日数</td><td class="bf">—</td><td class="af" lang="ja">4営業日以内に発送</td><td class="why">店铺档案已确认 · 10-12</td></tr>
              </tbody>
            </table>

            <div class="blk-t"><h3>证据</h3><span class="meta">4 块必看，展开即记为已查看</span>
              <div class="right evbar"><span id="evCount">已看 0 / 4</span><span class="pips" id="evPips"><i></i><i></i><i></i><i></i></span></div></div>

            <details class="ev" data-ev>
              <summary><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-8 9"/></svg></span><b>素材与依据图并排</b><span class="faint">9 图 · 1 视频 · 授权证据</span><span class="viewed badge wait">必看</span></summary>
              <div class="body">
                <div class="imgs9" id="imgs9"></div>
                <div class="pair">
                  <div><div class="ph photo"><span class="af" data-art="spoons"></span></div><div class="lab">依据图 · 自有实拍（图 8）</div></div>
                  <div><div class="ph"><span class="scene"></span><span class="af small" data-art="spoons"></span><span class="lv L2">L2</span><span class="wm">AI生成</span></div><div class="lab">图 5 · 场景图（派生）</div></div>
                  <dl class="kv" style="font-size:14px"><dt>授权</dt><dd><span class="tag">ai_from_own_photo</span></dd><dt>底图</dt><dd>本 SKU 样品实拍，10-17 拍摄</dd><dt>其余 8 张</dt><dd><span class="tag">supplier_license</span> ×5 · <span class="tag">own_shot</span> ×3</dd><dt>证据</dt><dd>供应商授权书.pdf · 10-18 · 授权方为权利人</dd></dl>
                </div>
              </div>
            </details>
            <details class="ev" data-ev>
              <summary><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg></span><b>合规报告 G1–G4</b><span class="faint">31 通过 · 1 WARN · 0 BLOCK</span><span class="viewed badge wait">必看</span></summary>
              <div class="body">
                <div class="heat" id="heat2"></div>
                <table class="tbl tl2" style="margin-top:10px"><tbody>
                  <tr><td><span class="badge ok">通过</span></td><td>G1 上架必备表示 6/6：送料、発送日数、返品条件、原産国、特商法表示、税込表示</td></tr>
                  <tr><td><span class="badge ok">通过</span></td><td>G2 文案 11/11：功效/医疗暗示、最上級、二重価格、ステマ、数字断言来源、原産国誤認、简体字形</td></tr>
                  <tr><td><span class="badge wait">WARN</span></td><td>G3-002 图 5 为 AI 生成场景（L2）：需确认以本 SKU 实拍图为底图、商品本体未改动</td></tr>
                  <tr><td><span class="badge ok">通过</span></td><td>G4 平台规格 5/5：9 图 ≤5MB ≥300×300；视频 MP4 5.9MB 9:16 18 秒</td></tr>
                </tbody></table>
                <p class="small faint" style="margin:8px 0 0">规则库 2026-10-20 版 · 校验于 10:38 · Checker 复核 10:42</p>
              </div>
            </details>
            <details class="ev" data-ev>
              <summary><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h9M8 4v2M5 14c2-2 4-5 5-8M7 10c1 2 3 3 5 4"/><path d="M13 20l4-9 4 9M14.5 17h5"/></svg></span><b>日文 + 中文回译</b><span class="faint">标题 · 5 卖点 · 术语一致</span><span class="viewed badge wait">必看</span></summary>
              <div class="body">
                <div class="jp"><span class="lb">标题</span><span lang="ja">シリコン調理スプーン5点セット 耐熱 キッチンツール <mark class="term">食洗機</mark>対応</span><span class="cn">硅胶烹饪勺 5 件套 耐热 厨房工具 可用洗碗机</span></div>
                <div class="jp"><span class="lb">卖点1</span><span lang="ja">5点セットで、調理に必要なスプーンがそろいます。</span><span class="cn">五件套，烹饪所需的勺子一应俱全。</span></div>
                <div class="jp"><span class="lb">卖点2</span><span lang="ja"><mark class="term">耐熱</mark>230℃のシリコン製で、鍋やフライパンを傷つけにくいです。</span><span class="cn">耐热 230℃ 的硅胶材质，不易划伤锅具。</span></div>
                <div class="jp"><span class="lb">卖点3</span><span lang="ja"><mark class="term">食洗機</mark>対応で、お手入れが簡単です。</span><span class="cn">可用洗碗机，清洗方便。</span></div>
                <div class="jp"><span class="lb">卖点4</span><span lang="ja">持ち手が長く、深い鍋でも使いやすいです。</span><span class="cn">手柄较长，深锅也好用。</span></div>
                <div class="jp"><span class="lb">卖点5</span><span lang="ja">吊り下げ用の穴付きで、すっきり収納できます。</span><span class="cn">带挂孔，收纳整齐。</span></div>
                <div class="row wrap" style="margin-top:8px"><span class="badge ok">食洗機 = 洗碗机</span><span class="badge ok">耐熱 = 耐热</span><span class="badge ok">税込 = 含税</span><span class="badge ok">原産国 = 原产国</span><span class="small faint">回译用另一模型逐句直译，仅帮你读懂</span></div>
              </div>
            </details>
            <details class="ev" data-ev>
              <summary><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg></span><b>价格与毛利分项</b><span class="faint">售价 ¥1,980 · 利润 ¥677 · 毛利 34.2%</span><span class="viewed badge wait">必看</span></summary>
              <div class="body">
                <div class="stack sm">
                  <div class="chart" data-chart="waterfall" data-cfg='{"w":540,"lw":110,"rowH":24,"items":[{"label":"售价（税込）","value":1980,"type":"revenue"},{"label":"到岸 c1–c7","value":993,"type":"cost","color":"s1","tip":"c1 ¥499 · c2 ¥62 · c3 ¥380 · c4 ¥0 · c5 ¥0 · c6 ¥30 · c7 ¥22"},{"label":"c8 佣金 10%","value":198,"type":"cost","color":"s4"},{"label":"c9 手续费 3%","value":59,"type":"cost","color":"s4"},{"label":"c10 退货损耗","value":53,"type":"cost","color":"s2"},{"label":"利润","value":677,"type":"profit"}],"legend":[{"label":"到岸成本","color":"s1"},{"label":"佣金手续费","color":"s4"},{"label":"退货损耗","color":"s2"}]}'></div>
                  <table class="cost"><tbody>
                    <tr><td>c1 采购价（24 CNY × 20.80）</td><td>¥499</td><td class="src">货源 10-18</td></tr>
                    <tr><td>c2 国内段运费</td><td>¥62</td><td class="src">费率卡 v12</td></tr>
                    <tr><td>c3 国际运费</td><td>¥380</td><td class="src">费率卡 v12</td></tr>
                    <tr><td>c4 关税 · c5 输入消費税</td><td>¥0 · ¥0</td><td class="src">演示假设</td></tr>
                    <tr><td>c6 通関 · c7 包材</td><td>¥30 · ¥22</td><td class="src">费率卡 v12</td></tr>
                    <tr class="total"><td>到岸小计</td><td>¥993</td><td></td></tr>
                    <tr><td>c8 佣金 10%</td><td>¥198</td><td class="src">平台费率页</td></tr>
                    <tr><td>c9 手续费 3%</td><td>¥59</td><td class="src">平台费率页</td></tr>
                    <tr><td>c10 退货损耗</td><td>¥53</td><td class="src">r=2.6%</td></tr>
                    <tr class="total"><td>利润 · 毛利</td><td>¥677 · 34.2%</td><td></td></tr>
                  </tbody></table>
                </div>
                <p class="small muted" style="margin:8px 0 0">成本地板价 ¥1,178 · 底线价 ¥1,373 · 竞品带 ¥1,780–2,480。税额为演示假设，未核实。</p>
              </div>
            </details>

            <div class="blk-t"><h3>需要你逐条确认的 WARN</h3><span class="meta">确认记录入审计并纳入周抽检</span><span class="right faint" id="warnCount">0 / 1 已确认</span></div>
            <div class="warn-row" id="warnRow">
              <div class="ph"><span class="scene"></span><span class="af small" data-art="spoons"></span><span class="lv L2">L2</span></div>
              <div>
                <div class="t">G3-002 · 图 5 场景图为 AI 生成（L2）</div>
                <div class="d">需确认：以本 SKU 实拍图（图 8）为底图，商品本体像素与比例未被改动；画面已标注「AI生成」。</div>
                <div class="row wrap">
                  <label class="chk"><input type="checkbox" id="warn1"> 我已核对，确认可用</label>
                  <select class="select" id="warnreason" aria-label="确认依据"><option value="">确认依据（必选）</option><option>已并排核对底图与成品</option><option>已附拍摄记录证据</option><option>其他（需备注）</option></select>
                </div>
              </div>
            </div>

            <div class="blk-t"><h3>备选方案</h3><span class="meta">不批准时可以这样做</span></div>
            <div class="alts">
              <div class="alt"><div class="row"><b>退回改写</b><span class="badge primary">常用</span></div><p>Creator 按你选的原因重做场景图或文案，约 8 分钟后作为新单回到这里。</p>
                <div class="cons"><span>· 本单结束（已退回），不会上架</span><span>· 原因进语料库，下一版默认规避</span></div></div>
              <div class="alt"><div class="row"><b>放弃该品</b></div><p>状态置“已放弃”，不再占用待批；可在选品页恢复。</p>
                <div class="cons"><span>· 已花的生成费 ¥96 不退</span><span>· 事实变化前 Pilot 不再提这个品</span></div></div>
            </div>
          </div>

          <div class="decision">
            <div class="law">未批准绝不执行；未决期间挂起等待，不自动放行也不自动放弃。<span>Agent 默认无批准权，不能批自己提的单。</span></div>
            <div class="row wrap" style="margin-top:12px">
              <button class="btn primary lg" id="approve2" disabled data-toast="已批准 · 已生成上架清单（演示）">批准</button>
              <select class="select" id="ret2" style="height:42px" aria-label="退回原因"><option value="">退回原因（必选）</option><option>措辞</option><option>图片</option><option>价格</option><option>合规</option><option>其他</option></select>
              <button class="btn lg" id="retBtn2" disabled data-toast="已退回改写（演示）">退回改写</button>
              <button class="btn lg danger" data-toast="已拒绝；事实变化前 Pilot 不再提这个品（演示）">拒绝</button>
            </div>
            <div class="need" id="need2"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================= 同意 1 ======================= -->
    <div data-pane="c1" hidden>
      <div class="card flush" data-approval id="t1">
        <div class="tk">
          <div class="tk-head" style="grid-template-columns:auto minmax(0,1fr) auto">
            <div class="row" style="gap:0">
              <span class="thumb lg" data-art="box" style="box-shadow:0 0 0 3px var(--surface)"></span><span class="thumb lg" data-art="spoons" style="margin-left:-28px;box-shadow:0 0 0 3px var(--surface)"></span><span class="thumb lg" data-art="cup" style="margin-left:-28px;box-shadow:0 0 0 3px var(--surface)"></span>
            </div>
            <div><h2>批准 5 个品进入采集：预计毛利 28.4%–34.2%</h2><div class="sub">由 Pilot 打包 · 08:30 · 方向卡 v7 · 单批上限 10</div></div>
            <div class="chart" data-chart="ring" data-cfg='{"pct":50,"size":80,"stroke":8,"label":"5/10","sub":"单批上限","color":"primary","fs":15}'></div>
          </div>
          <div class="badges"><span class="badge wait">同意 1</span><span class="badge">不对外</span><span class="badge">可撤销（放弃该品即可）</span><span class="badge">单人运行</span></div>
          <div class="lede"><b>必须先看这一句：</b>批准只会启动采集与素材生成，不会对外发布；每个品之后还要过一次同意 2。</div>
          <div class="three">
            <div class="mini"><div class="k">影响面</div><div class="v">5 个品 · 不对外</div><div class="n">启动采集；素材生成预计 ¥480</div></div>
            <div class="mini"><div class="k">为什么找你</div><div class="v">选品同意</div><div class="n">1 行数据不全，超出现有授权范围</div></div>
            <div class="mini"><div class="k">时效</div><div class="v">长期有效，等待批准</div><div class="n">已挂起 6 小时 · 不会自动放行或放弃</div></div>
          </div>

          <div class="blk-t"><h3>逐行看：5 个品</h3><span class="meta">数据不全的行必须展开才能批</span></div>
          <div class="c1row hd"><span></span><span>品名</span><span>售价</span><span>毛利</span><span>需求来源 · 一句话理由</span><span>数据</span></div>
          <div class="c1row"><span class="thumb" data-art="box"></span><span class="nm" lang="ja">折叠収納ボックス3個セット<small lang="zh-CN">折叠收纳箱 3 件套 · 分数 82</small></span><span>¥2,480</span><span class="mg"><b>31.7%</b><div class="meter ok"><i style="width:79%"></i></div></span><span><span class="grade A">A</span> 榜单 #14，价格带集中在 ¥2,200–2,800，高于底线 19.7 点</span><span class="badge ok">数据齐</span></div>
          <div class="c1row"><span class="thumb" data-art="spoons"></span><span class="nm" lang="ja">シリコン調理スプーン5点セット<small lang="zh-CN">硅胶烹饪勺 5 件套 · 79</small></span><span>¥1,980</span><span class="mg"><b>34.2%</b><div class="meter ok"><i style="width:86%"></i></div></span><span><span class="grade A">A</span> 榜单 #31，价格带空白处，到岸成本低</span><span class="badge ok">数据齐</span></div>
          <div class="c1row"><span class="thumb" data-art="cable"></span><span class="nm" lang="ja">デスクケーブルオーガナイザー<small lang="zh-CN">桌面理线器 · 76</small></span><span>¥1,680</span><span class="mg"><b>29.8%</b><div class="meter ok"><i style="width:75%"></i></div></span><span><span class="grade">B</span> 第三方导出，近 30 天增长；竞争中等</span><span class="badge ok">数据齐</span></div>
          <div class="c1row"><span class="thumb" data-art="brush"></span><span class="nm" lang="ja">ペット用ブラシ 抜け毛クリーナー<small lang="zh-CN">宠物浮毛梳 · 74</small></span><span>¥1,880</span><span class="mg"><b>33.0%</b><div class="meter ok"><i style="width:83%"></i></div></span><span><span class="grade A">A</span> 榜单 #22，类目增长快，头部评价数 &lt;5000</span><span class="badge ok">数据齐</span></div>
          <div class="c1row deg"><span class="thumb" data-art="cup"></span><span class="nm" lang="ja">折りたたみシリコンカップ<small lang="zh-CN">折叠硅胶杯 · 71（已扣减）</small></span><span>¥1,480</span><span class="mg"><b>28.4%</b><div class="meter wait"><i style="width:71%"></i></div></span><span><span class="grade C">C</span> 截图识别（已确认）；<b>竞争数据缺失</b>，总分已扣减</span><span class="badge wait">数据不全</span></div>
          <details class="ev c1ev" data-ev>
            <summary><b>展开「<span lang="ja">折りたたみシリコンカップ</span>」证据</b><span class="faint">数据不全的行必须展开</span><span class="viewed badge wait">必看</span></summary>
            <div class="body small">
              <dl class="kv"><dt>竞争强度</dt><dd><span class="badge wait">数据待补</span> 未导入同类在架数，不可算</dd><dt>需求</dt><dd>截图识别，已逐行确认（来源等级 C）</dd><dt>毛利</dt><dd>28.4%（底线 12%，成本 13 项齐全）</dd><dt>G0</dt><dd>通过 · 厨房小工具</dd><dt>方向卡</dt><dd>v7</dd></dl>
              <p class="faint" style="margin:6px 0 0">补导入竞品数据可解锁完整评分。<a href="03-candidates.html">去选品页</a></p>
            </div>
          </details>
          <div class="chart" style="margin-top:14px" data-chart="hbars" data-cfg='{"lw":150,"max":40,"items":[{"label":"シリコン調理スプーン","value":34.2,"text":"34.2%","color":"primary"},{"label":"ペット用ブラシ","value":33.0,"text":"33.0%","color":"primary"},{"label":"折叠収納ボックス","value":31.7,"text":"31.7%","color":"primary"},{"label":"ケーブルオーガナイザー","value":29.8,"text":"29.8%","color":"primary"},{"label":"シリコンカップ","value":28.4,"text":"28.4%","color":"wait","tip":"数据不全：竞争数据待补"}]}'></div>
          <p class="small faint" style="margin:6px 0 0">毛利对比 · 读法：5 个品都高于底线 12%；最低的一行数据不全。</p>

          <div class="blk-t"><h3>授权</h3><span class="meta">仅同意 1 可以加入；同意 2 永远由你本人批</span></div>
          <label class="chk"><input type="checkbox" id="grantchk"> 把这一类加入授权清单（仅同意 1）</label>
          <div class="grantcard" id="grantprev" hidden>
            <div class="row"><b>授权预览 · 选品同意</b><span class="badge wait">24 小时后生效 · 10-21 14:30</span><span class="right small faint">范围只能收窄，可随时撤销</span></div>
            <div class="env">
              <div class="dim"><span class="k">类目</span><span><span class="chip" aria-pressed="true" style="pointer-events:none">家居收纳</span> <span class="chip" aria-pressed="true" style="pointer-events:none">厨房小工具</span></span><span class="v">2 类</span></div>
              <div class="dim"><span class="k">价格带</span><span class="trk" data-tip="轴 ¥0–3,000；点为本单 5 个品"><span class="ax"></span><span class="in" style="left:33%;width:50%"></span><span class="pt" style="left:83%"></span><span class="pt" style="left:66%"></span><span class="pt" style="left:56%"></span><span class="pt" style="left:63%"></span><span class="pt" style="left:49%"></span></span><span class="v">¥1,000–2,500</span></div>
              <div class="dim"><span class="k">毛利下限</span><span class="trk" data-tip="轴 0–40%；竖线为下限 28%"><span class="ax"></span><span class="in" style="left:70%;width:30%"></span><span class="lim" style="left:70%"></span><span class="pt" style="left:85%"></span><span class="pt" style="left:82%"></span><span class="pt" style="left:79%"></span><span class="pt" style="left:74%"></span><span class="pt" style="left:71%"></span></span><span class="v">≥ 28%</span></div>
              <div class="dim"><span class="k">每日上限</span><span class="cells3"><i></i><i></i><i></i></span><span class="v">≤ 3 个/日 · 共 ≤10 次</span></div>
              <div class="dim"><span class="k">有效期</span><span class="trk"><span class="ax"></span><span class="in" style="left:3%;width:77%"></span><span class="lim" style="left:3%"></span><span class="lim" style="left:80%"></span></span><span class="v">至 11-12（30 天内）</span></div>
              <div class="dim"><span class="k">要求</span><span class="small">利润可算 · G0 通过 · 无数据不全 · 来源等级 ≥B</span><span class="v">抽检 20%</span></div>
            </div>
            <p class="small muted" style="margin:10px 0 0">之后 Pilot 可在此范围内代批选品同意；本单里数据不全的那一行在授权下也会回到你手里。</p>
          </div>
        </div>
        <div class="decision">
          <div class="law">未批准绝不执行；未决期间挂起等待，不自动放行也不自动放弃。<span>Agent 默认无批准权，不能批自己提的单。</span></div>
          <div class="row wrap" style="margin-top:12px">
            <button class="btn primary lg" id="approve1" disabled data-toast="已批准 5 个品 · 采集已启动（演示）">批准 5 个品</button>
            <select class="select" id="ret1" style="height:42px" aria-label="退回原因"><option value="">退回原因（必选）</option><option>品不对路</option><option>价格</option><option>数据不全</option><option>其他</option></select>
            <button class="btn lg" id="retBtn1" disabled data-toast="已退回重选（演示）">退回重选</button>
          </div>
          <div class="need" id="need1"></div>
        </div>
      </div>
    </div>

    <!-- ======================= 挂起 ======================= -->
    <div data-pane="held" hidden class="stack">
      <div class="alert wait"><span><b>挂起不会自动放行也不会自动放弃</b>，这里没有倒计时；每张卡写清楚需要你做什么。</span></div>
      <div class="card hcard">
        <span class="thumb lg" data-art="box"></span>
        <div>
          <div class="row wrap"><b lang="ja" style="font-size:17px">折叠収納ボックス3個セット</b><span class="badge block">读回不一致</span><span class="badge wait">已挂起 3 小时</span></div>
          <p class="small muted" style="margin:6px 0 0"><b style="color:var(--text)">挂起原因：</b>已在后台提交；后台价格 <b style="color:var(--block)">¥2,680</b> ≠ 批准价 ¥2,480（关键字段）。</p>
          <div class="small" style="margin-top:8px;font-weight:600">需要你做什么</div>
          <ol class="todo"><li>去卖家后台把价格改回 ¥2,480，回来重新回填；</li><li>或者去后台下架该商品。</li></ol>
          <p class="small faint" style="margin:4px 0 0">关键字段不一致不能“接受”；下架不会消除平台违规记录。</p>
        </div>
        <div class="side">
          <div class="vbox" style="padding:10px 12px"><div class="small faint">价格</div><div class="row between small"><span>批准</span><b>¥2,480</b></div><div class="row between small"><span>后台</span><b style="color:var(--block)">¥2,680</b></div></div>
          <a class="btn primary" href="07-listing.html">去上架页处理</a>
        </div>
      </div>
      <div class="card hcard">
        <span class="thumb lg" data-art="basket"></span>
        <div>
          <div class="row wrap"><b lang="ja" style="font-size:17px">折りたたみ洗濯かご</b><span class="badge wait">数据待补 · 缺税口径</span><span class="tag">形态示例</span></div>
          <p class="small muted" style="margin:6px 0 0"><b style="color:var(--text)">挂起原因：</b>c4 关税、c5 输入消費税的税口径未设定，利润不可算。</p>
          <div class="small" style="margin-top:8px;font-weight:600">需要你做什么</div>
          <ol class="todo"><li>在设置 · 费率卡里为该类目选定税口径并写出处；</li><li>保存后系统重算，满足条件再生成新单。</li></ol>
        </div>
        <div class="side">
          <div class="vbox" style="padding:10px 12px"><div class="small faint">毛利</div><b style="color:var(--wait)">不可算</b></div>
          <a class="btn" href="10-settings.html">去设置补税口径</a>
        </div>
      </div>
    </div>

    <!-- ======================= 已作废 ======================= -->
    <div data-pane="void" hidden>
      <div class="card void-card">
        <div class="row" style="gap:14px">
          <span class="thumb lg" data-art="cup"></span>
          <div><h2 class="strike">批准上架「<span lang="ja">折りたたみシリコンカップ</span>」¥1,480</h2><div class="small faint">原单 · 10-19 16:05 生成 · 10-20 09:00 作废</div></div>
          <span class="badge right">已作废</span>
        </div>
        <div class="alert wait" style="margin-top:14px"><span><b>批准时依据的事实已变化，原批准作废，不会执行；已生成新单，附差异说明。</b></span></div>
        <div class="vgrid">
          <div class="vbox">
            <h4>汇率 CNY→JPY · 偏离 +3.6%</h4>
            <div class="vbar"><span>快照 10-19</span><span class="tr"><i style="width:50%;background:var(--s1)"></i><span class="tol" style="left:88.75%"><span>容忍线 +3% · 21.42</span></span></span><b>20.80</b></div>
            <div class="vbar"><span>现在 10-20</span><span class="tr"><i style="width:96.9%;background:var(--block)"></i><span class="tol" style="left:88.75%"></span></span><b style="color:var(--block)">21.55</b></div>
            <p class="small faint" style="margin:8px 0 0">轴 20.00–21.60 · 超过容忍线即作废</p>
          </div>
          <div class="vbox">
            <h4>毛利与到岸成本</h4>
            <div class="vbar"><span>毛利 原</span><span class="tr"><i style="width:71%;background:var(--s1)"></i></span><b>28.4%</b></div>
            <div class="vbar"><span>毛利 新</span><span class="tr"><i style="width:67.3%;background:var(--s2)"></i><span class="tol" style="left:30%;border-left-color:var(--text-3)"><span style="color:var(--text-3);top:auto;bottom:-18px;right:auto;left:4px">底线 12%</span></span></span><b>26.9%</b></div>
            <div class="vbar" style="margin-top:20px"><span>到岸成本</span><span class="small">¥1,090 → <b>¥1,128</b>（+¥38）</span><span></span></div>
          </div>
        </div>
        <div class="succ">
          <span class="badge wait">后继单</span>
          <span class="small"><b>批准上架「<span lang="ja">折りたたみシリコンカップ</span>」¥1,480 · 毛利 26.9%</b><br><span class="faint">差异已写入新单的“批准后会发生什么”，仍需你批</span></span>
          <a class="btn sm right" href="#" data-toast="跳转到后继单（演示）">查看后继单</a>
        </div>
      </div>
    </div>
  </div>`;
