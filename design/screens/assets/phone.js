/* TikTok Shop 日本站 · 手机商品详情页示意（演示用）
   依据 TikTok Shop 日本站 App 商品详情页的常见版式绘制：顶部标签（商品/レビュー/詳細/おすすめ）、
   图片轮播与页码、税込价格、タイトル、レビュー、配送与返品、ストア卡、商品詳細、特定商取引法に基づく表記、
   底部栏（ストア/カート + カートに追加/今すぐ購入）。实际渲染以卖家后台预览为准。
   用法：<div data-phone='{"art":"spoons","price":1980,"title":"…","count":"1/9"}'></div> */
(function(){
  window.CP = window.CP || {};
  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
  function yen(n){ return '¥' + Number(n).toLocaleString('ja-JP'); }
  var ICON = {
    back:'<path d="M15 5l-7 7 7 7"/>', search:'<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>', cart:'<path d="M3 4h2.500l2 11h10l2-8H7"/><circle cx="9" cy="19" r="1.300"/><circle cx="17" cy="19" r="1.300"/>',
    more:'<circle cx="5" cy="12" r="1.200"/><circle cx="12" cy="12" r="1.200"/><circle cx="19" cy="12" r="1.200"/>', chev:'<path d="M9 5l7 7-7 7"/>', store:'<path d="M4 9l1.500-5h13L20 9"/><path d="M4 9a2.700 2.700 0 0 0 5.300 0 2.700 2.700 0 0 0 5.400 0A2.700 2.700 0 0 0 20 9"/><path d="M5.500 12v8h13v-8"/>',
    truck:'<path d="M2 6h11v10H2zM13 9h4l3 3v4h-7"/><circle cx="7" cy="17.500" r="1.600"/><circle cx="17" cy="17.500" r="1.600"/>', ret:'<path d="M4 10h11a5 5 0 0 1 0 10H8"/><path d="M8 6l-4 4 4 4"/>', shield:'<path d="M12 3l8 3v6c0 4.500-3.200 8-8 9-4.800-1-8-4.500-8-9V6z"/>', star:'<path d="M12 3.500l2.600 5.300 5.800.8-4.200 4.100 1 5.800L12 16.800l-5.200 2.700 1-5.800L3.600 9.600l5.800-.8z"/>'
  };
  function ic(k,cls){ return '<svg class="'+(cls||'')+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+ICON[k]+'</svg>'; }
  CP.phone = function(c){
    var art = CP.art ? CP.art(c.art||'box') : '';
    var bullets = (c.bullets||[]).map(function(b){ return '<li>'+esc(b)+'</li>'; }).join('');
    return '<div class="tt-phone" lang="ja">'
    +'<div class="tt-dev"><div class="tt-status"><span>9:41</span><span class="tt-notch"></span><span class="tt-sig"><i></i><i></i><i></i><i></i></span></div>'
    +'<div class="tt-scroll">'
      +'<div class="tt-gal">'+art
        +'<div class="tt-nav"><span class="tt-b">'+ic('back')+'</span><span class="tt-tabs"><b>商品</b><span>レビュー</span><span>詳細</span><span>おすすめ</span></span><span class="tt-b">'+ic('cart')+'</span><span class="tt-b">'+ic('more')+'</span></div>'
        +'<span class="tt-cnt">'+esc(c.count||'1/9')+'</span></div>'
      +'<div class="tt-price"><b>'+yen(c.price)+'</b><small>税込</small><span class="tt-pill">'+esc(c.ship||'送料無料')+'</span></div>'
      +'<div class="tt-title">'+(c.titleHtml||esc(c.title))+'</div>'
      +'<div class="tt-rate">'+ic('star','tt-s')+'<span>新商品 · レビューはまだありません</span></div>'
      +'<div class="tt-sec">'
        +'<div class="tt-row"><span class="tt-k">'+ic('truck')+'配送</span><span class="tt-v"><b>'+esc(c.dispatch||'4営業日以内に発送')+'</b>'+(c.shipNote?'<em>'+esc(c.shipNote)+'</em>':'')+'</span></div>'
        +'<div class="tt-row"><span class="tt-k">'+ic('ret')+'返品</span><span class="tt-v"><b>'+esc(c.returns||'到着後7日以内')+'</b></span></div>'
        +'<div class="tt-row"><span class="tt-k">'+ic('shield')+'原産国</span><span class="tt-v"><b>'+esc(c.origin||'中国')+'</b></span></div>'
      +'</div>'
      +'<div class="tt-store"><span class="tt-av">J</span><span><b>'+esc(c.store||'JP-01 ストア')+'</b><em>跨境ストア · 商品 12</em></span><span class="tt-follow">フォロー</span></div>'
      +'<div class="tt-desc"><h5>商品詳細</h5><ul>'+bullets+'</ul><span class="tt-more">すべて見る'+ic('chev')+'</span></div>'
      +'<div class="tt-legal">特定商取引法に基づく表記'+ic('chev')+'</div>'
    +'</div>'
    +'<div class="tt-bar"><span class="tt-ib">'+ic('store')+'<em>ストア</em></span><span class="tt-ib">'+ic('cart')+'<em>カート</em></span><span class="tt-btn tt-add">カートに追加</span><span class="tt-btn tt-buy">今すぐ購入</span></div>'
    +'</div></div>';
  };
  CP.hydratePhone = function(root){
    (root||document).querySelectorAll('[data-phone]').forEach(function(el){
      if(el.dataset.done) return; var c={}; try{ c=JSON.parse(el.dataset.phone); }catch(e){}
      el.innerHTML = CP.phone(c); el.dataset.done='1';
    });
  };
})();
