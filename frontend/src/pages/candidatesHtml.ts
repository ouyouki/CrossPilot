// 原样取自 design/screens/03-candidates.html 的 <template id="main-tpl">。
export const candidatesHtml = String.raw`  <div class="page-head">
    <div>
      <span class="eyebrow">Pipeline · 2026-10-20 · 方向 v6</span>
      <h1>选品</h1>
      <p>候选 24 · 夜间 03:10 已打分 · 本屏只发起，不直接批</p>
    </div>
    <div class="actions">
      <button class="help" data-toast="操作手册：选品页（演示）" aria-label="帮助">?</button>
      <details class="menu" id="impmenu">
        <summary class="btn">数据同步</summary>
        <div class="pop" role="menu">
          <button role="menuitem" data-toast="已触发授权数据服务立即同步，完成后重新打分（演示）"><span class="tag">AUTO</span><span><b>立即同步</b><small>授权数据服务 · 下次自动 10-21 02:40</small></span></button>
          <button role="menuitem" data-toast="选择 CSV 文件：卖家后台导出记 A，第三方工具导出记 B（演示）"><span class="tag">CSV</span><span><b>手动导入 CSV（兜底）</b><small>卖家后台导出记 A，第三方导出记 B</small></span></button>
          <button role="menuitem" data-toast="打开粘贴框：解析失败的行会写明“请人工修正第 N 行”（演示）"><span class="tag">TSV</span><span><b>粘贴表格</b><small>解析失败的行会写明第几行</small></span></button>
          <button role="menuitem" disabled aria-disabled="true"><span class="tag">IMG</span><span><b>截图识别 <span class="badge" style="height:18px">后续开放</span></b><small>识别结果记 C，需逐行确认</small></span></button>
        </div>
      </details>
      <span class="small" id="go-hint" style="color:var(--wait);max-width:190px;line-height:1.4;text-align:right"></span>
      <button class="btn primary lg" id="go" data-toast="已生成同意 1 审批单，请到待批查看（演示）">发起同意 1（已勾 <span id="cnt">5</span>/10）</button>
    </div>
  </div>

  <div class="band">
    <section class="card">
      <div class="card-head"><h2>需求 × 毛利 地图</h2><span class="meta">横轴需求分 · 纵轴毛利 %</span><div class="tools legend"><span><i style="background:var(--primary)"></i>已勾选</span><span><i style="background:var(--surface);box-shadow:inset 0 0 0 1.5px var(--primary)"></i>未勾选</span></div></div>
      <div id="scatter" class="chart"></div>
      <p class="small faint" style="margin:6px 0 0">读法：越靠右上越值得做；红虚线是毛利底线 12%。数据待补的 7 个毛利不可算，不在图上。</p>
    </section>
    <div class="side">
      <div class="minic">
        <h3>数据来源等级 <span class="r">24 个候选</span></h3>
        <div class="chart" data-chart="stack" data-cfg='{"h":12,"items":[{"label":"A 官方导出 · 手动 CSV","value":10,"color":"s1","text":"10"},{"label":"B 授权服务 · 自动同步","value":9,"color":"s3","text":"9"},{"label":"C 截图/手录","value":5,"color":"s4","text":"5"}]}'></div>
      </div>
      <div class="minic">
        <h3>数据缺口 <span class="badge wait">7 个待补</span></h3>
        <div class="row" style="align-items:flex-end;margin-bottom:8px"><div style="font-size:15px;line-height:1.45">补 <b>c3 国际运费</b><br><span class="small faint">（货源重量）可解锁 3 个</span></div><button class="btn sm right" id="go-nd">去补</button></div>
        <div class="chart" data-chart="hbars" data-cfg='{"lw":78,"color":"wait","max":3,"items":[{"label":"c3 国际运费","value":3,"text":"3 个"},{"label":"税口径","value":2,"text":"2 个"},{"label":"c6 通関费","value":1,"text":"1 个"},{"label":"c10 退货率","value":1,"text":"1 个"}]}'></div>
      </div>
      <div class="minic">
        <h3>已选摘要 <span class="r" id="sel-n">5 个</span></h3>
        <div class="row" style="gap:12px"><div class="stackthumbs" id="sel-th"></div>
          <div class="right" style="text-align:right"><div class="small faint">预计平均毛利</div><b style="font-size:22px" id="sel-avg">31.4%</b></div></div>
        <div class="small muted" style="margin-top:6px" id="sel-rg">毛利区间 28.4%–34.2% · 均分 76</div>
      </div>
    </div>
  </div>

  <details class="ev imp" id="imp">
    <summary><b>数据同步</b><span class="small faint">需求信号只来自授权数据服务与你导入的文件，系统不会抓取平台页面</span><span class="badge ok viewed">自动同步 02:40</span></summary>
    <div class="body">
      <div class="syncg">
        <div class="impc sync">
          <div class="row between"><b>自动同步</b>
            <div class="seg" role="group" aria-label="连接器状态（演示两态）">
              <button data-view="on" data-group="conn" aria-pressed="true">已连接</button>
              <button data-view="off" data-group="conn" aria-pressed="false">未配置</button>
            </div>
          </div>
          <div data-pane-view="on" data-group="conn">
            <div class="row" style="margin:8px 0 6px"><span class="badge ok">已连接</span><span class="small">授权数据服务 · 榜单 / 竞品 / 价格带</span><span class="grade B right" data-tip="来源等级 B：已授权的第三方数据服务">B</span></div>
            <dl class="kv small"><dt>最近一次</dt><dd><span class="mono">2026-10-20 02:40</span> · 22 行 · 全部解析</dd><dt>下次</dt><dd><span class="mono">2026-10-21 02:40</span>（每日夜间）</dd><dt>新鲜度</dt><dd>7 小时前 · 上限 24 小时</dd></dl>
            <div class="meter ok" style="margin:6px 0 4px"><i style="width:29%"></i></div>
            <p class="small faint" style="margin:6px 0 0">失败时：当日无数据，候选标“数据不全”，不静默；连续失败 3 次告警。</p>
            <div class="row" style="margin-top:8px"><button class="btn sm" data-toast="已触发立即同步（演示）">立即同步</button><button class="btn sm ghost" data-toast="打开设置 · 数据连接（演示）">连接设置</button></div>
          </div>
          <div data-pane-view="off" data-group="conn" hidden>
            <div class="row" style="margin:8px 0 6px"><span class="badge">未配置</span><span class="small">没有已授权的数据服务</span></div>
            <p>需先在设置里接入有合同或令牌的数据服务（API 或定时导出文件夹）。未配置时只用手动 CSV，新鲜度按最近一次导入算。</p>
            <button class="btn sm" data-toast="打开设置 · 数据连接（演示）">去设置数据连接</button>
          </div>
        </div>
        <div class="impc">
          <div class="row between"><b>手动导入 CSV</b><span class="badge">兜底</span></div>
          <p>卖家后台导出记 A，第三方工具导出记 B。解析失败的行写明“请人工修正第 N 行”，不猜。</p>
          <div class="row wrap"><button class="btn sm" data-toast="选择 CSV 文件（演示）">选择文件</button><button class="btn sm" data-toast="打开粘贴框（演示）">粘贴表格</button><button class="btn sm" disabled data-toast="截图识别后续开放（演示）">截图识别 · 后续开放</button></div>
        </div>
      </div>
      <ul class="feed">
        <li><span class="dot ok"></span><div>2026-10-20 02:40 · <span class="src a">自动同步</span> 授权数据服务（B）· 22 行，全部解析<div class="t">与 A 重复的 9 行已按 A 合并</div></div></li>
        <li><span class="dot ok"></span><div>2026-10-19 22:10 · <span class="src m">手动 CSV</span> 卖家后台榜单导出（A）· 40 行，解析 38 行 → 24 个候选入库<div class="t">第 12、27 行列数不符：请人工修正第 12、27 行 · <a href="#" data-toast="下载出错行（演示）">查看出错行</a></div></div></li>
        <li><span class="dot" style="background:var(--block)"></span><div>2026-10-18 02:40 · <span class="src a">自动同步</span> 失败（服务无响应）<div class="t">当日无数据，当天候选标“数据不全”；10-19 已恢复</div></div></li>
      </ul>
    </div>
  </details>

  <div data-tabs style="margin-top:16px">
    <div class="tabs" role="tablist">
      <button role="tab" data-tab="ok" aria-selected="true">可选<span class="n">12</span></button>
      <button role="tab" data-tab="nd" aria-selected="false" id="tab-nd">数据待补<span class="n">7</span></button>
      <button role="tab" data-tab="bk" aria-selected="false">不可售<span class="n">5</span></button>
    </div>

    <div data-pane="ok">
      <div class="card flush">
        <div class="pane-tools">
          <b style="font-size:16px">可选候选</b><span class="small faint">按分数排序 · 默认勾选前 5 · 单批最多 10</span>
          <div class="seg right" role="group" aria-label="视图">
            <button data-view="tbl" data-group="cv" aria-pressed="true">表格</button>
            <button data-view="card" data-group="cv" aria-pressed="false">卡片</button>
          </div>
        </div>
        <div data-pane-view="tbl" data-group="cv">
          <div class="tblwrap">
          <table class="tbl cand">
            <thead><tr>
              <th scope="col"><span class="sr">勾选</span></th><th scope="col">商品</th><th scope="col" class="num">售价</th><th scope="col" class="num">毛利</th>
              <th scope="col">分数</th><th scope="col">来源</th><th scope="col">竞争</th><th scope="col">一句话理由 · 风险旗</th></tr></thead>
            <tbody>
<tr data-detail="d-1"><td><input type="checkbox" data-pick="1" checked aria-label="选择 #1"></td>
  <td><div class="prod"><span class="thumb" data-art="box"></span><div><div class="t" lang="ja">折叠収納ボックス3個セット</div><div class="s">折叠收纳箱三件套 · 家居收纳</div></div></div></td>
  <td class="num">¥2,480</td><td class="num"><b class="mg">31.7%</b></td>
  <td><div class="sc" data-tip="<b>总分 82</b><br>需求 98 × 0.35 = 34.3<br>利润 98 × 0.35 = 34.5<br>竞争空档 94 × 0.15 = 14.1<br>风险 −8 × 0.15 = −1.2"><span class="scbar"><i style="width:82%"></i></span><b>82</b></div></td>
  <td class="nowrap"><span class="grade A" data-tip="来源等级 A：卖家后台官方导出 · 手动导入 CSV">A</span> <span class="src m">手动 CSV</span></td><td class="small">低</td>
  <td class="why">类目榜第 7 位，同类在架少，毛利接近目标<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-2"><td><input type="checkbox" data-pick="2" checked aria-label="选择 #2"></td>
  <td><div class="prod"><span class="thumb" data-art="spoons"></span><div><div class="t" lang="ja">シリコン調理スプーン5点セット</div><div class="s">硅胶厨具五件套 · 厨房小工具</div></div></div></td>
  <td class="num">¥1,980</td><td class="num"><b class="mg">34.2%</b></td>
  <td><div class="sc" data-tip="<b>总分 79</b><br>需求 94 × 0.35 = 32.9<br>利润 100 × 0.35 = 35.0<br>竞争空档 78 × 0.15 = 11.7<br>风险 −5 × 0.15 = −0.8"><span class="scbar"><i style="width:79%"></i></span><b>79</b></div></td>
  <td class="nowrap"><span class="grade A" data-tip="来源等级 A：卖家后台官方导出 · 手动导入 CSV">A</span> <span class="src m">手动 CSV</span></td><td class="small">中</td>
  <td class="why">近 7 日榜单上升 12 位，毛利全场最高<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-gen"><td><input type="checkbox" data-pick="3" checked aria-label="选择 #3"></td>
  <td><div class="prod"><span class="thumb" data-art="cable"></span><div><div class="t" lang="ja">デスクケーブルオーガナイザー</div><div class="s">桌面理线器 · 桌面办公</div></div></div></td>
  <td class="num">¥1,680</td><td class="num"><b class="mg">29.8%</b></td>
  <td><div class="sc" data-tip="<b>总分 76</b><br>需求 92 × 0.35 = 32.2<br>利润 89 × 0.35 = 31.2<br>竞争空档 95 × 0.15 = 14.2<br>风险 −12 × 0.15 = −1.8"><span class="scbar"><i style="width:76%"></i></span><b>76</b></div></td>
  <td class="nowrap"><span class="grade B" data-tip="来源等级 B：授权数据服务 · 自动同步">B</span> <span class="src a">自动同步</span></td><td class="small">低</td>
  <td class="why">需求稳定，同类在架少<div class="flags" style="margin-top:4px"><span class="badge wait">品牌疑似</span></div></td></tr>
<tr data-detail="d-gen"><td><input type="checkbox" data-pick="4" checked aria-label="选择 #4"></td>
  <td><div class="prod"><span class="thumb" data-art="brush"></span><div><div class="t" lang="ja">ペット用ブラシ 抜け毛クリーナー</div><div class="s">宠物梳毛粘毛器 · 宠物用品</div></div></div></td>
  <td class="num">¥1,880</td><td class="num"><b class="mg">33.0%</b></td>
  <td><div class="sc" data-tip="<b>总分 74</b><br>需求 84 × 0.35 = 29.4<br>利润 100 × 0.35 = 35.0<br>竞争空档 66 × 0.15 = 9.9<br>风险 −5 × 0.15 = −0.8"><span class="scbar"><i style="width:74%"></i></span><b>74</b></div></td>
  <td class="nowrap"><span class="grade A" data-tip="来源等级 A：卖家后台官方导出 · 手动导入 CSV">A</span> <span class="src m">手动 CSV</span></td><td class="small">中</td>
  <td class="why">带货达人 14 人，毛利 33.0%<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-5"><td><input type="checkbox" data-pick="5" checked aria-label="选择 #5"></td>
  <td><div class="prod"><span class="thumb" data-art="cup"></span><div><div class="t" lang="ja">折りたたみシリコンカップ</div><div class="s">折叠硅胶杯 · 厨房小工具</div></div></div></td>
  <td class="num">¥1,480</td><td class="num"><b class="mg">28.4%</b></td>
  <td><div class="sc" data-tip="<b>总分 71</b><br>需求 90 × 0.35 = 31.5<br>利润 82 × 0.35 = 28.7<br>竞争空档 80 × 0.15 = 12.0<br>风险 −6 × 0.15 = −0.9"><span class="scbar"><i style="width:71%"></i></span><b>71</b></div></td>
  <td class="nowrap"><span class="grade C" data-tip="来源等级 C：截图识别或手录">C</span> <span class="src m">截图</span></td><td class="small">中</td>
  <td class="why">户外季需求上升，体积小运费低<div class="flags" style="margin-top:4px"><span class="badge wait">数据不全</span></div></td></tr>
<tr data-detail="d-gen"><td><input type="checkbox" data-pick="6" aria-label="选择 #6"></td>
  <td><div class="prod"><span class="thumb" data-art="rack"></span><div><div class="t" lang="ja">キッチン水切りラック</div><div class="s">厨房沥水架 · 厨房小工具</div></div></div></td>
  <td class="num">¥2,780</td><td class="num"><b class="mg">27.1%</b></td>
  <td><div class="sc" data-tip="<b>总分 68</b><br>需求 97 × 0.35 = 33.9<br>利润 76 × 0.35 = 26.4<br>竞争空档 62 × 0.15 = 9.3<br>风险 −12 × 0.15 = −1.8"><span class="scbar"><i style="width:68%"></i></span><b>68</b></div></td>
  <td class="nowrap"><span class="grade B" data-tip="来源等级 B：授权数据服务 · 自动同步">B</span> <span class="src a">自动同步</span></td><td class="small">高</td>
  <td class="why">需求最高，但国际运费占售价 23%<div class="flags" style="margin-top:4px"><span class="badge wait">运费占比超线</span></div></td></tr>
<tr data-detail="d-gen"><td><input type="checkbox" data-pick="7" aria-label="选择 #7"></td>
  <td><div class="prod"><span class="thumb" data-art="divider"></span><div><div class="t" lang="ja">引き出し仕切り板</div><div class="s">抽屉分隔板 · 家居收纳</div></div></div></td>
  <td class="num">¥1,580</td><td class="num"><b class="mg">30.2%</b></td>
  <td><div class="sc" data-tip="<b>总分 66</b><br>需求 66 × 0.35 = 23.1<br>利润 91 × 0.35 = 31.8<br>竞争空档 80 × 0.15 = 12.0<br>风险 −5 × 0.15 = −0.8"><span class="scbar"><i style="width:66%"></i></span><b>66</b></div></td>
  <td class="nowrap"><span class="grade B" data-tip="来源等级 B：授权数据服务 · 自动同步">B</span> <span class="src a">自动同步</span></td><td class="small">低</td>
  <td class="why">体积小，运费占比低<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-gen"><td><input type="checkbox" data-pick="8" aria-label="选择 #8"></td>
  <td><div class="prod"><span class="thumb" data-art="hooks"></span><div><div class="t" lang="ja">マグネットフック6個入</div><div class="s">磁吸挂钩6个装 · 家居收纳</div></div></div></td>
  <td class="num">¥1,180</td><td class="num"><b class="mg">26.0%</b></td>
  <td><div class="sc" data-tip="<b>总分 63</b><br>需求 80 × 0.35 = 28.0<br>利润 70 × 0.35 = 24.5<br>竞争空档 78 × 0.15 = 11.7<br>风险 −5 × 0.15 = −0.8"><span class="scbar"><i style="width:63%"></i></span><b>63</b></div></td>
  <td class="nowrap"><span class="grade A" data-tip="来源等级 A：卖家后台官方导出 · 手动导入 CSV">A</span> <span class="src m">手动 CSV</span></td><td class="small">中</td>
  <td class="why">单价低，毛利空间窄<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-gen" class="more" hidden><td><input type="checkbox" data-pick="9" aria-label="选择 #9"></td>
  <td><div class="prod"><span class="thumb" data-art="rack"></span><div><div class="t" lang="ja">シンク下収納ラック</div><div class="s">水槽下收纳架 · 家居收纳</div></div></div></td>
  <td class="num">¥2,280</td><td class="num"><b class="mg">22.5%</b></td>
  <td><div class="sc" data-tip="<b>总分 58</b><br>需求 80 × 0.35 = 28.0<br>利润 52 × 0.35 = 18.4<br>竞争空档 80 × 0.15 = 12.0<br>风险 −5 × 0.15 = −0.8"><span class="scbar"><i style="width:58%"></i></span><b>58</b></div></td>
  <td class="nowrap"><span class="grade B" data-tip="来源等级 B：授权数据服务 · 自动同步">B</span> <span class="src a">自动同步</span></td><td class="small">低</td>
  <td class="why">需求平稳，毛利偏低<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-gen" class="more" hidden><td><input type="checkbox" data-pick="10" aria-label="选择 #10"></td>
  <td><div class="prod"><span class="thumb" data-art="divider"></span><div><div class="t" lang="ja">シューズラック</div><div class="s">鞋架 · 家居收纳</div></div></div></td>
  <td class="num">¥2,980</td><td class="num"><b class="mg">19.8%</b></td>
  <td><div class="sc" data-tip="<b>总分 55</b><br>需求 85 × 0.35 = 29.8<br>利润 39 × 0.35 = 13.7<br>竞争空档 85 × 0.15 = 12.8<br>风险 −5 × 0.15 = −0.8"><span class="scbar"><i style="width:55%"></i></span><b>55</b></div></td>
  <td class="nowrap"><span class="grade B" data-tip="来源等级 B：授权数据服务 · 自动同步">B</span> <span class="src a">自动同步</span></td><td class="small">低</td>
  <td class="why">体积大，运费拉低毛利<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-gen" class="more" hidden><td><input type="checkbox" data-pick="11" aria-label="选择 #11"></td>
  <td><div class="prod"><span class="thumb" data-art="cup"></span><div><div class="t" lang="ja">ペット用食器スタンド</div><div class="s">宠物餐具架 · 宠物用品</div></div></div></td>
  <td class="num">¥2,680</td><td class="num"><b class="mg">16.4%</b></td>
  <td><div class="sc" data-tip="<b>总分 49</b><br>需求 80 × 0.35 = 28.0<br>利润 22 × 0.35 = 7.7<br>竞争空档 100 × 0.15 = 15.0<br>风险 −10 × 0.15 = −1.5"><span class="scbar"><i style="width:49%"></i></span><b>49</b></div></td>
  <td class="nowrap"><span class="grade B" data-tip="来源等级 B：授权数据服务 · 自动同步">B</span> <span class="src a">自动同步</span></td><td class="small">低</td>
  <td class="why">竞争空档大，毛利偏低<div class="flags" style="margin-top:4px"></div></td></tr>
<tr data-detail="d-gen" class="more" hidden><td><input type="checkbox" data-pick="12" aria-label="选择 #12"></td>
  <td><div class="prod"><span class="thumb" data-art="spoons"></span><div><div class="t" lang="ja">シリコン鍋つかみ</div><div class="s">硅胶隔热夹 · 厨房小工具</div></div></div></td>
  <td class="num">¥1,080</td><td class="num"><b class="mg">15.6%</b></td>
  <td><div class="sc" data-tip="<b>总分 44</b><br>需求 75 × 0.35 = 26.2<br>利润 18 × 0.35 = 6.3<br>竞争空档 90 × 0.15 = 13.5<br>风险 −14 × 0.15 = −2.1"><span class="scbar"><i style="width:44%"></i></span><b>44</b></div></td>
  <td class="nowrap"><span class="grade C" data-tip="来源等级 C：截图识别或手录">C</span> <span class="src m">截图</span></td><td class="small">中</td>
  <td class="why">单价低，毛利贴近底线<div class="flags" style="margin-top:4px"><span class="badge wait">数据新鲜度低</span></div></td></tr>
            </tbody>
          </table>
          </div>
          <div class="row" style="padding:10px 20px 16px"><button class="btn sm ghost" id="more-btn">展开其余 4 个（分数 63 以下）</button><span class="small faint right">悬停分数看 需求 / 利润 / 竞争 / 风险 分解</span></div>
        </div>
        <div data-pane-view="card" data-group="cv" hidden>
          <div class="cards">
<div class="pcard" data-detail="d-1"><div class="ph" data-art="box"></div>
  <label class="pk"><input type="checkbox" data-pick="1" checked aria-label="选择 #1"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">折叠収納ボックス3個セット</div><div class="s">折叠收纳箱三件套 · ¥2,480</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":82,"size":52,"stroke":6,"label":"82","fs":15,"color":"primary","tip":"分数 82"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>31.7%</b><span class="grade A" style="margin-left:auto">A</span></div>
  <div class="small muted" style="margin-top:4px">类目榜第 7 位，同类在架少，毛利接近目标</div><div class="flags" style="margin-top:6px"></div></div></div>
<div class="pcard" data-detail="d-2"><div class="ph" data-art="spoons"></div>
  <label class="pk"><input type="checkbox" data-pick="2" checked aria-label="选择 #2"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">シリコン調理スプーン5点セット</div><div class="s">硅胶厨具五件套 · ¥1,980</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":79,"size":52,"stroke":6,"label":"79","fs":15,"color":"primary","tip":"分数 79"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>34.2%</b><span class="grade A" style="margin-left:auto">A</span></div>
  <div class="small muted" style="margin-top:4px">近 7 日榜单上升 12 位，毛利全场最高</div><div class="flags" style="margin-top:6px"></div></div></div>
<div class="pcard" data-detail="d-gen"><div class="ph" data-art="cable"></div>
  <label class="pk"><input type="checkbox" data-pick="3" checked aria-label="选择 #3"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">デスクケーブルオーガナイザー</div><div class="s">桌面理线器 · ¥1,680</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":76,"size":52,"stroke":6,"label":"76","fs":15,"color":"primary","tip":"分数 76"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>29.8%</b><span class="grade B" style="margin-left:auto">B</span></div>
  <div class="small muted" style="margin-top:4px">需求稳定，同类在架少</div><div class="flags" style="margin-top:6px"><span class="badge wait">品牌疑似</span></div></div></div>
<div class="pcard" data-detail="d-gen"><div class="ph" data-art="brush"></div>
  <label class="pk"><input type="checkbox" data-pick="4" checked aria-label="选择 #4"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">ペット用ブラシ 抜け毛クリーナー</div><div class="s">宠物梳毛粘毛器 · ¥1,880</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":74,"size":52,"stroke":6,"label":"74","fs":15,"color":"primary","tip":"分数 74"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>33.0%</b><span class="grade A" style="margin-left:auto">A</span></div>
  <div class="small muted" style="margin-top:4px">带货达人 14 人，毛利 33.0%</div><div class="flags" style="margin-top:6px"></div></div></div>
<div class="pcard" data-detail="d-5"><div class="ph" data-art="cup"></div>
  <label class="pk"><input type="checkbox" data-pick="5" checked aria-label="选择 #5"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">折りたたみシリコンカップ</div><div class="s">折叠硅胶杯 · ¥1,480</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":71,"size":52,"stroke":6,"label":"71","fs":15,"color":"primary","tip":"分数 71"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>28.4%</b><span class="grade C" style="margin-left:auto">C</span></div>
  <div class="small muted" style="margin-top:4px">户外季需求上升，体积小运费低</div><div class="flags" style="margin-top:6px"><span class="badge wait">数据不全</span></div></div></div>
<div class="pcard" data-detail="d-gen"><div class="ph" data-art="rack"></div>
  <label class="pk"><input type="checkbox" data-pick="6" aria-label="选择 #6"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">キッチン水切りラック</div><div class="s">厨房沥水架 · ¥2,780</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":68,"size":52,"stroke":6,"label":"68","fs":15,"color":"primary","tip":"分数 68"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>27.1%</b><span class="grade B" style="margin-left:auto">B</span></div>
  <div class="small muted" style="margin-top:4px">需求最高，但国际运费占售价 23%</div><div class="flags" style="margin-top:6px"><span class="badge wait">运费占比超线</span></div></div></div>
<div class="pcard" data-detail="d-gen"><div class="ph" data-art="divider"></div>
  <label class="pk"><input type="checkbox" data-pick="7" aria-label="选择 #7"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">引き出し仕切り板</div><div class="s">抽屉分隔板 · ¥1,580</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":66,"size":52,"stroke":6,"label":"66","fs":15,"color":"primary","tip":"分数 66"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>30.2%</b><span class="grade B" style="margin-left:auto">B</span></div>
  <div class="small muted" style="margin-top:4px">体积小，运费占比低</div><div class="flags" style="margin-top:6px"></div></div></div>
<div class="pcard" data-detail="d-gen"><div class="ph" data-art="hooks"></div>
  <label class="pk"><input type="checkbox" data-pick="8" aria-label="选择 #8"></label>
  <div class="pc-b"><div class="row top" style="gap:10px"><div style="min-width:0;flex:1"><div class="t" lang="ja">マグネットフック6個入</div><div class="s">磁吸挂钩6个装 · ¥1,180</div></div>
  <div class="chart" data-chart="ring" data-cfg='{"pct":63,"size":52,"stroke":6,"label":"63","fs":15,"color":"primary","tip":"分数 63"}'></div></div>
  <div class="row" style="margin-top:6px"><span class="small faint">毛利</span><b>26.0%</b><span class="grade A" style="margin-left:auto">A</span></div>
  <div class="small muted" style="margin-top:4px">单价低，毛利空间窄</div><div class="flags" style="margin-top:6px"></div></div></div>
          </div>
        </div>
      </div>
      <div class="alert wait warnbar" id="warn5" hidden><span><b>已勾选 1 行数据不全：需在右栏展开确认</b><br><span lang="ja">折りたたみシリコンカップ</span> 的季节标注缺失、需求来自截图识别（C）。确认前不能发起同意 1。</span><button class="btn sm right" data-open="d-5">展开确认</button></div>
    </div>

    <div data-pane="nd" hidden>
      <div class="alert wait" style="margin-bottom:12px"><span><b>补一项，可解锁一批</b>　补「c3 国际运费（重量）」解锁 3 个 · 补「税口径」解锁 2 个 · 补「c6 通関费」「c10 退货率」各 1 个</span></div>
      <div class="card flush">
        <div class="tblwrap">
        <table class="tbl">
          <thead><tr><th scope="col">商品</th><th scope="col">缺什么</th><th scope="col" class="num">毛利</th><th scope="col" class="num">分数</th><th scope="col">去补</th></tr></thead>
          <tbody>
            <tr data-detail="d-nd1"><td><div class="prod"><span class="thumb" data-art="whisk"></span><div><div class="t" lang="ja">シリコン泡立て器</div><div class="s">硅胶打蛋器 · 厨房小工具</div></div></div></td><td><span class="badge wait">缺 c3 国际运费</span><span class="sub">货源未填重量</span></td><td class="num faint">不可算</td><td class="num faint">不可算</td><td><a class="btn sm" href="04-sourcing.html">去货源补重量</a></td></tr>
            <tr data-detail="d-nd2"><td><div class="prod"><span class="thumb" data-art="basket"></span><div><div class="t" lang="ja">折りたたみ洗濯かご</div><div class="s">折叠洗衣篮 · 家居收纳</div></div></div></td><td><span class="badge wait">缺税口径</span><span class="sub">c4 关税、c5 输入消费税不可算</span></td><td class="num faint">不可算</td><td class="num faint">不可算</td><td><a class="btn sm" href="10-settings.html">去设置补税口径</a></td></tr>
            <tr><td><div class="prod"><span class="thumb" data-art="box"></span><div><div class="t" lang="ja">米びつ スタッカブル</div><div class="s">可叠放米桶 · 厨房小工具</div></div></div></td><td><span class="badge wait">缺 c3 国际运费</span><span class="sub">货源未填重量</span></td><td class="num faint">不可算</td><td class="num faint">不可算</td><td><a class="btn sm" href="04-sourcing.html">去货源补重量</a></td></tr>
            <tr><td><div class="prod"><span class="thumb" data-art="box"></span><div><div class="t" lang="ja">靴下収納ボックス</div><div class="s">袜子收纳盒 · 家居收纳</div></div></div></td><td><span class="badge wait">缺 c3 国际运费</span><span class="sub">货源未填重量</span></td><td class="num faint">不可算</td><td class="num faint">不可算</td><td><a class="btn sm" href="04-sourcing.html">去货源补重量</a></td></tr>
            <tr><td><div class="prod"><span class="thumb" data-art="cable"></span><div><div class="t" lang="ja">アルミ製スマホスタンド</div><div class="s">铝制手机支架 · 桌面办公</div></div></div></td><td><span class="badge wait">缺税口径</span><span class="sub">c4、c5 不可算</span></td><td class="num faint">不可算</td><td class="num faint">不可算</td><td><a class="btn sm" href="10-settings.html">去设置补税口径</a></td></tr>
            <tr><td><div class="prod"><span class="thumb" data-art="rack"></span><div><div class="t" lang="ja">食器乾燥マット</div><div class="s">餐具沥水垫 · 厨房小工具</div></div></div></td><td><span class="badge wait">缺 c6 通関费</span><span class="sub">费率卡未填</span></td><td class="num faint">不可算</td><td class="num faint">不可算</td><td><a class="btn sm" href="10-settings.html">去设置补费率</a></td></tr>
            <tr><td><div class="prod"><span class="thumb" data-art="cup"></span><div><div class="t" lang="ja">耐熱シリコンマット</div><div class="s">耐热硅胶垫 · 厨房小工具</div></div></div></td><td><span class="badge wait">缺 c10 退货率</span><span class="sub">费率卡未填</span></td><td class="num faint">不可算</td><td class="num faint">不可算</td><td><a class="btn sm" href="10-settings.html">去设置补费率</a></td></tr>
          </tbody>
        </table>
        </div>
      </div>
    </div>

    <div data-pane="bk" hidden>
      <div class="alert block" style="margin-bottom:12px"><span><b>这 5 个不能选</b>　命中品类准入规则，没有例外入口。</span></div>
      <div class="card flush">
        <div class="tblwrap">
        <table class="tbl">
          <thead><tr><th scope="col"><span class="sr">勾选</span></th><th scope="col">商品</th><th scope="col">命中原因</th><th scope="col">出处</th></tr></thead>
          <tbody>
            <tr class="dim" data-detail="d-bk1"><td><input type="checkbox" disabled aria-label="不可选择"></td><td><div class="prod"><span class="thumb" data-art="earbuds"></span><div><div class="t" lang="ja">Bluetoothイヤホン</div><div class="s">蓝牙耳机 · 数码配件</div></div></div></td><td><div class="flags"><span class="badge block">类目未登记</span><span class="badge block">含无线</span><span class="badge block">含电池</span></div></td><td class="small">品类白名单 · 风险词库</td></tr>
            <tr class="dim"><td><input type="checkbox" disabled aria-label="不可选择"></td><td><div class="prod"><span class="thumb" data-art="serum"></span><div><div class="t" lang="ja">美容液</div><div class="s">美容精华液 · 美妆个护</div></div></div></td><td><div class="flags"><span class="badge block">类目未登记</span><span class="badge block">化粧品</span></div></td><td class="small">品类白名单 · 风险词库</td></tr>
            <tr class="dim"><td><input type="checkbox" disabled aria-label="不可选择"></td><td><div class="prod"><span class="thumb" data-art="powerbank"></span><div><div class="t" lang="ja">モバイルバッテリー</div><div class="s">移动电源 · 数码配件</div></div></div></td><td><div class="flags"><span class="badge block">类目未登记</span><span class="badge block">含电池</span><span class="badge block">承运商禁运</span></div></td><td class="small">品类白名单 · 承运商清单</td></tr>
            <tr class="dim"><td><input type="checkbox" disabled aria-label="不可选择"></td><td><div class="prod"><span class="thumb" data-art="mask"></span><div><div class="t" lang="ja">保湿マスク</div><div class="s">保湿面膜 · 美妆个护</div></div></div></td><td><div class="flags"><span class="badge block">类目未登记</span><span class="badge block">化粧品</span></div></td><td class="small">品类白名单 · 风险词库</td></tr>
            <tr class="dim"><td><input type="checkbox" disabled aria-label="不可选择"></td><td><div class="prod"><span class="thumb" data-art="snack"></span><div><div class="t" lang="ja">お菓子ギフト</div><div class="s">点心礼盒 · 食品</div></div></div></td><td><div class="flags"><span class="badge block">类目未登记</span><span class="badge block">食品</span></div></td><td class="small">品类白名单 · 风险词库</td></tr>
          </tbody>
        </table>
        </div>
      </div>
      <p class="faint small">要让某类商品可选，需要先在 <a href="10-settings.html">设置</a> 里登记品类并附出处（属于放宽，24 小时后生效）。</p>
    </div>
  </div>`;
