/* 商品插画（演示用，扁平几何风；颜色走 CSS 变量，深浅主题自动）
   用法：CP.art('box') 返回 <svg>；页面里写 <span class="thumb" data-art="box"></span> 会被自动填充。 */
(function(){
  var F = function(c){ return 'fill="var(--art-'+c+')"'; };
  var S = function(c,w){ return 'stroke="var(--art-'+c+')" stroke-width="'+(w||3)+'" fill="none" stroke-linecap="round" stroke-linejoin="round"'; };
  var ART = {
    box: ['a', '<polygon points="20,44 56,44 56,78 20,78" '+F(1)+'/><polygon points="56,44 78,34 78,68 56,78" '+F(1)+' opacity=".72"/><polygon points="20,44 42,34 78,34 56,44" '+F(6)+' opacity=".22"/><rect x="30" y="52" width="16" height="6" rx="3" '+F(3)+'/><line x1="20" y1="66" x2="56" y2="66" '+S(3,1.5)+' opacity=".5"/><rect x="26" y="22" width="30" height="14" rx="3" '+F(2)+' opacity=".9"/>'],
    spoons: ['b', '<g transform="rotate(-30 48 84)"><ellipse cx="48" cy="24" rx="8" ry="11" '+F(5)+'/><rect x="45" y="32" width="6" height="46" rx="3" '+F(5)+'/></g><g><rect x="40" y="14" width="16" height="22" rx="4" '+F(1)+'/><rect x="45" y="34" width="6" height="44" rx="3" '+F(1)+'/></g><g transform="rotate(30 48 84)"><ellipse cx="48" cy="24" rx="10" ry="10" '+F(2)+'/><rect x="45" y="32" width="6" height="46" rx="3" '+F(2)+'/></g>'],
    cable: ['c', '<rect x="10" y="62" width="76" height="16" rx="4" '+F(4)+'/><path d="M22 14 C22 40 30 40 30 56" '+S(6,3)+'/><path d="M44 14 C44 38 48 40 48 56" '+S(1,3)+'/><path d="M70 14 C70 40 62 40 64 56" '+S(5,3)+'/><rect x="24" y="52" width="12" height="12" rx="3" '+F(1)+'/><rect x="42" y="52" width="12" height="12" rx="3" '+F(1)+'/><rect x="60" y="52" width="12" height="12" rx="3" '+F(1)+'/>'],
    brush: ['d', '<rect x="39" y="12" width="18" height="40" rx="9" '+F(1)+'/><rect x="24" y="50" width="48" height="20" rx="7" '+F(2)+'/><g '+S(6,2)+'><line x1="30" y1="70" x2="30" y2="80"/><line x1="37" y1="70" x2="37" y2="80"/><line x1="44" y1="70" x2="44" y2="80"/><line x1="51" y1="70" x2="51" y2="80"/><line x1="58" y1="70" x2="58" y2="80"/><line x1="65" y1="70" x2="65" y2="80"/></g><circle cx="48" cy="26" r="3" '+F(3)+'/>'],
    cup: ['e', '<polygon points="26,32 70,32 63,78 33,78" '+F(1)+'/><g '+S(3,1.5)+' opacity=".55"><line x1="29" y1="46" x2="67" y2="46"/><line x1="31" y1="58" x2="65" y2="58"/><line x1="32" y1="69" x2="64" y2="69"/></g><rect x="22" y="26" width="52" height="8" rx="4" '+F(2)+'/>'],
    rack: ['a', '<rect x="14" y="68" width="68" height="9" rx="3" '+F(4)+'/><g '+F(1)+'><rect x="22" y="26" width="4" height="42" rx="2"/><rect x="32" y="26" width="4" height="42" rx="2"/><rect x="42" y="26" width="4" height="42" rx="2"/><rect x="52" y="26" width="4" height="42" rx="2"/><rect x="62" y="26" width="4" height="42" rx="2"/><rect x="72" y="26" width="4" height="42" rx="2"/></g><ellipse cx="47" cy="42" rx="20" ry="7" '+S(2,3)+'/>'],
    divider: ['b', '<rect x="14" y="26" width="68" height="46" rx="6" '+F(3)+' stroke="var(--art-4)" stroke-width="2"/><rect x="34" y="30" width="4" height="38" rx="2" '+F(1)+'/><rect x="56" y="30" width="4" height="38" rx="2" '+F(1)+'/><circle cx="24" cy="48" r="5" '+F(2)+'/><circle cx="46" cy="52" r="6" '+F(5)+'/><rect x="64" y="42" width="12" height="18" rx="3" '+F(6)+' opacity=".6"/>'],
    hooks: ['c', '<g><circle cx="26" cy="30" r="10" '+F(4)+'/><circle cx="26" cy="30" r="5" '+F(1)+'/><path d="M26 40 V58 Q26 68 34 66" '+S(1,4)+'/></g><g><circle cx="48" cy="30" r="10" '+F(4)+'/><circle cx="48" cy="30" r="5" '+F(2)+'/><path d="M48 40 V58 Q48 68 56 66" '+S(2,4)+'/></g><g><circle cx="70" cy="30" r="10" '+F(4)+'/><circle cx="70" cy="30" r="5" '+F(5)+'/><path d="M70 40 V58 Q70 68 78 66" '+S(5,4)+'/></g>'],
    whisk: ['d', '<rect x="43" y="10" width="10" height="30" rx="5" '+F(1)+'/><g '+S(2,2.5)+'><path d="M48 40 C28 50 30 76 48 80 C66 76 68 50 48 40Z"/><path d="M48 40 C40 52 40 72 48 80 C56 72 56 52 48 40Z"/></g>'],
    basket: ['e', '<path d="M18 38 H78 L70 78 H26Z" '+F(1)+'/><g '+S(3,2)+' opacity=".5"><line x1="22" y1="52" x2="74" y2="52"/><line x1="24" y1="64" x2="72" y2="64"/><line x1="40" y1="38" x2="38" y2="78"/><line x1="56" y1="38" x2="58" y2="78"/></g><path d="M18 38 Q48 14 78 38" '+S(2,4)+'/>'],
    earbuds: ['c', '<rect x="22" y="48" width="52" height="30" rx="14" '+F(4)+'/><circle cx="36" cy="38" r="10" '+F(6)+'/><rect x="42" y="38" width="6" height="22" rx="3" '+F(6)+'/><circle cx="62" cy="38" r="10" '+F(6)+'/><rect x="48" y="38" width="6" height="22" rx="3" '+F(6)+' opacity="0"/><circle cx="48" cy="63" r="3" '+F(5)+'/>'],
    serum: ['d', '<rect x="36" y="38" width="24" height="40" rx="7" '+F(2)+'/><rect x="43" y="28" width="10" height="12" '+F(6)+'/><ellipse cx="48" cy="22" rx="7" ry="9" '+F(5)+'/><rect x="40" y="52" width="16" height="12" rx="3" '+F(3)+' opacity=".8"/>'],
    powerbank: ['c', '<rect x="26" y="18" width="44" height="62" rx="9" '+F(6)+'/><rect x="32" y="26" width="32" height="14" rx="3" '+F(1)+'/><path d="M52 48 L42 62 H49 L45 74 L58 58 H51Z" '+F(2)+'/>'],
    mask: ['d', '<rect x="22" y="22" width="52" height="56" rx="8" '+F(3)+' stroke="var(--art-4)" stroke-width="2"/><ellipse cx="48" cy="50" rx="14" ry="18" '+F(5)+' opacity=".85"/><circle cx="43" cy="46" r="2" '+F(3)+'/><circle cx="53" cy="46" r="2" '+F(3)+'/><path d="M43 58 Q48 62 53 58" '+S(3,2)+'/>'],
    snack: ['b', '<rect x="20" y="40" width="56" height="38" rx="5" '+F(5)+'/><rect x="16" y="32" width="64" height="12" rx="4" '+F(2)+'/><rect x="44" y="32" width="8" height="46" '+F(3)+' opacity=".9"/><path d="M48 32 C40 18 28 24 36 32 M48 32 C56 18 68 24 60 32" '+S(3,3)+'/>']
  };
  var BG = {a:'--art-a',b:'--art-b',c:'--art-c',d:'--art-d',e:'--art-e'};
  function art(name){
    var a = ART[name] || ART.box;
    return '<svg viewBox="0 0 96 96" role="img" aria-label="商品示意图" xmlns="http://www.w3.org/2000/svg"><rect width="96" height="96" fill="var('+BG[a[0]]+')"/>'+a[1]+'</svg>';
  }
  window.CP = window.CP || {};
  CP.art = art;
  CP.artNames = Object.keys(ART);
  CP.hydrateArt = function(root){
    (root||document).querySelectorAll('[data-art]').forEach(function(el){ if(!el.firstChild){ el.innerHTML = art(el.dataset.art); } });
  };
})();
