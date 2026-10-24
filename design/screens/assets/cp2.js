/* CrossPilot 画面原型 · 壳与交互 v2
   页面写法：
     <body data-page="today" data-crumb="今日">
       <template id="main-tpl"> …主区… </template>
       <template id="detail-tpl"> …右栏默认内容… </template>   （可选）
       <script src="assets/art.js"></script><script src="assets/charts.js"></script><script src="assets/cp2.js"></script>
   自动能力：商品插画 [data-art]、图表 [data-chart]、提示 [data-tip]、toast [data-toast]、复制 [data-copy]、
            标签页 role=tab[data-tab]+[data-pane]、行选中 tr[data-detail]→右栏模板、勾选计数 input[data-count]、
            分段切换 button[data-view][data-group]+[data-group][data-pane-view]、开关 .switch、chip 切换 .chip */
(function(){
  var I = {
    today:'<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    direction:'<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    candidates:'<path d="M4 6h16M4 12h10M4 18h6"/><circle cx="18" cy="16" r="3"/><path d="M20.2 18.2L22 20"/>',
    sourcing:'<path d="M3 8l9-5 9 5v8l-9 5-9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    assets:'<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-8 9"/>',
    listing:'<path d="M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1z"/><rect x="5" y="6" width="14" height="15" rx="2"/><path d="M9 12h6M9 16h4"/>',
    approvals:'<path d="M8 12.5l3 3 5-6"/><rect x="3" y="3" width="18" height="18" rx="4"/>',
    grants:'<path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    audit:'<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>',
    settings:'<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>'
  };
  function ic(k){ return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(I[k]||'')+'</svg>'; }
  window.CP = window.CP || {}; CP.icon = ic;
  var NAV = [
    ['', [['today','今日','01-today.html']]],
    ['流水线', [['direction','方向','02-direction.html'],['candidates','选品','03-candidates.html'],['sourcing','货源','04-sourcing.html'],['assets','素材','05-assets.html'],['listing','上架','07-listing.html']]],
    ['治理', [['approvals','待批','06-approvals.html',5],['grants','授权清单','08-grants.html'],['audit','审计','09-audit.html']]],
    ['', [['settings','设置','10-settings.html']]]
  ];

  /* ---------- 换肤 ---------- */
  var SKINS = [
    ['mint','明亮·青','默认。浅色侧栏，青色主色',['#F7FBFA','#DDF0F0','#0B6E73']],
    ['sky','天空·蓝','浅蓝侧栏，蓝色主色',['#F3F8FE','#DCE9FB','#1D5FD0']],
    ['violet','薰衣草·紫','浅紫侧栏，紫色主色',['#F8F6FD','#E7E2FA','#5B45C9']],
    ['paper','纸白·靛蓝','中性白灰，靛蓝主色',['#FFFFFF','#E8EAFB','#3B49C4']],
    ['navy','深蓝·橙','深蓝侧栏，橙色品牌点缀',['#14264A','#2A4A8C','#F26B1D']],
    ['carbon','碳黑·青','碳黑侧栏，青色强调',['#14171C','#2A323C','#17B8C9']]
  ];
  var SK_KEY='cp.skin', root=document.documentElement;
  function readSkin(){
    var q=(location.search.match(/[?&]skin=(\w+)/)||[])[1]; if(q) return q;
    try{ var v=localStorage.getItem(SK_KEY); if(v) return v; }catch(_){}
    var m=(window.name||'').match(/cpskin=(\w+)/); return m?m[1]:'mint';
  }
  function setSkin(k,persist){
    if(!SKINS.some(function(s){return s[0]===k;})) k='mint';
    root.setAttribute('data-skin',k);
    if(persist){ try{ localStorage.setItem(SK_KEY,k); }catch(_){} try{ window.name='cpskin='+k; }catch(_){} }
    document.querySelectorAll('.skin-opt').forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.skin===k); });
    var lbl=document.getElementById('skin-lbl'); if(lbl){ SKINS.forEach(function(s){ if(s[0]===k) lbl.textContent=s[1]; }); }
  }
  CP.setSkin=setSkin;
  setSkin(readSkin(),false);
  var body=document.body, page=body.dataset.page, crumb=body.dataset.crumb||'';
  var mainTpl=document.getElementById('main-tpl'), detTpl=document.getElementById('detail-tpl');
  var nav='<nav class="nav" aria-label="主导航">';
  NAV.forEach(function(g){
    if(g[0]) nav+='<h4>'+g[0]+'</h4>';
    g[1].forEach(function(i){ nav+='<a href="'+i[2]+'"'+(i[0]===page?' aria-current="page"':'')+'>'+ic(i[0])+'<span>'+i[1]+'</span>'+(i[3]?'<span class="cnt">'+i[3]+'</span>':'')+'</a>'; });
  });
  nav+='<div class="foot"><b>林薇</b>Owner + Operator · 单人运行<br>日本站 JP-01 · 跨境直邮<br>上架通道 A（执行清单）<br><a href="00-login.html">退出登录</a></div></nav>';
  var top='<header class="topbar"><div class="brand"><i><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 17-7-4-7 4z"/></svg></i>CrossPilot</div>'
    +'<span class="crumb">'+crumb+'</span>'
    +'<div class="sysbar">'
    +'<span class="sys" data-tip="规则库 2026-10-20 版，新鲜度正常"><span class="dot"></span>规则库 <b>FRESH</b></span>'
    +'<span class="sys" data-tip="今日模型花费 ¥312 / 上限 ¥1,500；未设上限=不生成"><b>¥312</b><span class="mini"><i style="width:21%"></i></span>¥1,500</span>'
    +'<span class="sys wait" data-tip="没有第二位审批人：系统用延迟生效、抽检和查看门槛补偿"><span class="dot"></span><b>单人运行</b></span>'
    +'<span class="sys">JP-01 日本站</span>'
    +'<span class="skin-btn"><button class="btn sm" id="skin-toggle" aria-haspopup="true" aria-expanded="false" data-nopersist="1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 0 18c1.2 0 2-.8 2-1.8 0-.5-.2-.9-.5-1.3-.3-.4-.5-.8-.5-1.300 0-1 .8-1.800 1.800-1.800H17a4 4 0 0 0 4-4c0-4.400-4-8-9-8z"/><circle cx="7.500" cy="11" r="1"/><circle cx="10.500" cy="7" r="1"/><circle cx="15" cy="7" r="1"/></svg><span id="skin-lbl">换肤</span></button><div class="skin-pop" id="skin-pop" role="menu"><h4>换肤 · 框架配色</h4>'+SKINS.map(function(s){return '<button class="skin-opt" role="menuitemradio" data-skin="'+s[0]+'" aria-pressed="false"><span class="swatch"><i style="background:'+s[3][0]+'"></i><i style="background:linear-gradient(90deg,'+s[3][1]+' 50%,'+s[3][2]+' 50%)"></i></span><span><b>'+s[1]+'</b><span class="d">'+s[2]+'</span></span></button>';}).join('')+'<p class="hint">快捷键：Alt + 1–6。选择会记住，并带到其他画面。语义色与图表色不随皮肤变化。</p></div></span>'
    +'<button class="btn sm" data-toast="站内通知：无未读">通知</button></div></header>';
  var detail='<aside class="detail" id="detail" aria-label="详情">'+(detTpl?detTpl.innerHTML:'<p class="empty">选中一行，在这里看证据与影响面。</p>')+'</aside>';
  body.insertAdjacentHTML('afterbegin', top+'<div class="shell">'+nav+'<main class="main" id="main">'+(mainTpl?mainTpl.innerHTML:'')+'</main>'+detail+'</div><div class="toast" id="toast" role="status"></div><div class="demo">演示数据 · 非平台事实</div>');

  setSkin(readSkin(),false);
  (function(){
    var tg=document.getElementById('skin-toggle'), pop=document.getElementById('skin-pop');
    if(!tg) return;
    tg.addEventListener('click',function(e){ e.stopPropagation(); var on=!pop.classList.contains('on'); pop.classList.toggle('on',on); tg.setAttribute('aria-expanded',on); });
    pop.addEventListener('click',function(e){ var b=e.target.closest('.skin-opt'); if(b){ setSkin(b.dataset.skin,true); toast('已换肤：'+b.querySelector('b').textContent); } e.stopPropagation(); });
    document.addEventListener('click',function(){ pop.classList.remove('on'); tg.setAttribute('aria-expanded',false); });
    document.addEventListener('keydown',function(e){
      if(e.key==='Escape') pop.classList.remove('on');
      if(e.altKey && /^[1-6]$/.test(e.key)){ var s=SKINS[+e.key-1]; if(s){ setSkin(s[0],true); toast('已换肤：'+s[1]); e.preventDefault(); } }
    });
    // 导航链接带上皮肤参数，保证跨页保持（localStorage 不可用时的兜底）
    document.querySelectorAll('.nav a').forEach(function(a){ a.addEventListener('click',function(){ try{ window.name='cpskin='+root.getAttribute('data-skin'); }catch(_){} }); });
  })();

  function hydrate(root){ if(CP.hydratePhone) CP.hydratePhone(root); if(CP.tagJa) CP.tagJa(root); if(CP.hydrateArt) CP.hydrateArt(root); if(CP.mountCharts) CP.mountCharts(root); }
  hydrate(document);
  /* 含假名的文本自动标 lang=ja：中日同字形不同，用 lang 让浏览器选对字形与字体 */
  CP.tagJa=function(scope){
    var kana=/[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]/;
    (scope||document).querySelectorAll('.main *, .detail *, .tip, .phone *').forEach(function(el){
      if(el.closest('[lang]') && el.closest('[lang]')!==document.documentElement && el.closest('[lang]').lang.indexOf('ja')===0) return;
      if(el.children.length===0 && kana.test(el.textContent)) el.setAttribute('lang','ja');
    });
  };
  CP.tagJa(document);

  var toastEl=document.getElementById('toast'), tt;
  function toast(m){ toastEl.textContent=m; toastEl.classList.add('on'); clearTimeout(tt); tt=setTimeout(function(){toastEl.classList.remove('on')},2200); }
  CP.toast = toast;

  document.addEventListener('click', function(e){
    var t=e.target.closest('[data-toast]');
    if(t && !t.hasAttribute('disabled') && !t.classList.contains('disabled')){ toast(t.dataset.toast); if(t.tagName==='A') e.preventDefault(); }
    var c=e.target.closest('[data-copy]');
    if(c){ try{ navigator.clipboard.writeText(c.dataset.copy); }catch(_){} toast('已复制'); }
    var tab=e.target.closest('[role=tab]');
    if(tab){
      var list=tab.parentElement; list.querySelectorAll('[role=tab]').forEach(function(b){ b.setAttribute('aria-selected', b===tab); });
      var scope=list.closest('[data-tabs]')||document;
      scope.querySelectorAll('[data-pane]').forEach(function(p){ p.hidden = p.dataset.pane!==tab.dataset.tab; });
    }
    var v=e.target.closest('button[data-view]');
    if(v){ var g=v.dataset.group; document.querySelectorAll('button[data-view][data-group="'+g+'"]').forEach(function(b){ b.setAttribute('aria-pressed', b===v); });
      document.querySelectorAll('[data-pane-view][data-group="'+g+'"]').forEach(function(p){ p.hidden = p.dataset.paneView!==v.dataset.view; }); }
    var chip=e.target.closest('.chip[aria-pressed]'); if(chip && !chip.dataset.view){ chip.setAttribute('aria-pressed', chip.getAttribute('aria-pressed')!=='true'); }
    var sw=e.target.closest('.switch'); if(sw){ sw.setAttribute('aria-checked', sw.getAttribute('aria-checked')!=='true'); }
    var row=e.target.closest('[data-detail]');
    if(row && !e.target.closest('input,button,a,select')){
      document.querySelectorAll('.sel').forEach(function(r){r.classList.remove('sel')}); row.classList.add('sel');
      var tpl=document.getElementById(row.dataset.detail);
      if(tpl){ var d=document.getElementById('detail'); d.innerHTML=tpl.innerHTML; hydrate(d); d.scrollTop=0; }
    }
    var open=e.target.closest('[data-open]');
    if(open){ var tp=document.getElementById(open.dataset.open); if(tp){ var d2=document.getElementById('detail'); d2.innerHTML=tp.innerHTML; hydrate(d2); } }
  });
  document.addEventListener('change', function(e){
    var i=e.target; if(!i.matches||!i.matches('input[data-count]')) return;
    var boxes=document.querySelectorAll('input[data-count="'+i.dataset.count+'"]'), max=+i.dataset.max||999, n=0;
    boxes.forEach(function(b){ if(b.checked) n++; });
    if(n>max){ i.checked=false; n--; toast('单批最多勾选 '+max+' 个'); }
    document.querySelectorAll(i.dataset.count).forEach(function(o){ o.textContent=n; });
  });
  document.addEventListener('toggle', function(e){
    var d=e.target; if(!d.matches||!d.matches('details[data-ev]')) return;
    if(d.open){ d.dataset.seen='1'; var v=d.querySelector('.viewed'); if(v){ v.textContent='已查看'; v.className='viewed badge ok'; } }
    var scope=d.closest('[data-approval]'); if(!scope) return;
    var ok=true; scope.querySelectorAll('details[data-ev]').forEach(function(x){ if(x.dataset.seen!=='1') ok=false; });
    var btn=scope.querySelector('[data-approve]'), hint=scope.querySelector('[data-approve-hint]');
    if(btn){ btn.disabled=!ok; btn.classList.toggle('disabled',!ok); }
    if(hint) hint.textContent = ok?'':'还有必看证据未展开，批准暂不可用';
  }, true);
  CP.hydrate = hydrate;
})();
