/* CrossPilot 原型图表库（纯 SVG/HTML，无依赖；颜色全部走 CSS 变量，深浅主题自动）
   声明式用法：<div class="chart" data-chart="类型" data-cfg='{...JSON...}'></div>
   类型：spark ring gauge hbars vbars hist scatter waterfall radar stack line heat donut
   悬停提示：任何带 data-tip="文字或HTML" 的元素都会出现提示框（图表内的标记已自动带上）。
   规范（dataviz）：细标记、圆角数据端、2px 表面色间隔、最多直接标注关键点、网格弱化、状态色只表状态。 */
(function(){
  window.CP = window.CP || {};
  var NS = 'http://www.w3.org/2000/svg';
  function col(c){
    if(!c) return 'var(--primary)';
    if(c[0]==='#'||c.indexOf('var(')===0) return c;
    return 'var(--'+c+')';
  }
  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
  function tipAttr(t){ return t ? ' data-tip="'+esc(t)+'"' : ''; }
  function fmt(n,d){ return Number(n).toLocaleString('ja-JP',{maximumFractionDigits:d||0,minimumFractionDigits:d||0}); }
  function svg(w,h,inner,extra){ return '<svg viewBox="0 0 '+w+' '+h+'" width="'+w+'" height="'+h+'" role="img" '+(extra||'')+' xmlns="'+NS+'">'+inner+'</svg>'; }
  function scale(d0,d1,r0,r1){ return function(v){ return r0 + (v-d0)/(d1-d0||1)*(r1-r0); }; }

  var T = {};

  T.spark = function(c){
    var v=c.values, w=c.w||84, h=c.h||28, pad=3, min=Math.min.apply(null,v), max=Math.max.apply(null,v);
    var x=scale(0,v.length-1,pad,w-pad), y=scale(min,max,h-pad,pad);
    var pts=v.map(function(a,i){return x(i).toFixed(1)+','+y(a).toFixed(1);});
    var color=col(c.color), last=v.length-1;
    var area = c.area===false?'':'<polygon points="'+pad+','+(h-pad)+' '+pts.join(' ')+' '+(w-pad)+','+(h-pad)+'" fill="'+color+'" opacity=".12"/>';
    return svg(w,h, area+'<polyline points="'+pts.join(' ')+'" fill="none" stroke="'+color+'" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/><circle cx="'+x(last).toFixed(1)+'" cy="'+y(v[last]).toFixed(1)+'" r="3" fill="'+color+'" stroke="var(--surface)" stroke-width="2"/>','aria-label="趋势"');
  };

  T.ring = function(c){
    var s=c.size||96, st=c.stroke||10, r=(s-st)/2, L=2*Math.PI*r, p=Math.max(0,Math.min(1,c.pct/100));
    var color=col(c.color), cx=s/2;
    var inner='<circle cx="'+cx+'" cy="'+cx+'" r="'+r+'" fill="none" stroke="var(--surface-3)" stroke-width="'+st+'"/>'
      +'<circle cx="'+cx+'" cy="'+cx+'" r="'+r+'" fill="none" stroke="'+color+'" stroke-width="'+st+'" stroke-linecap="round" stroke-dasharray="'+(L*p).toFixed(1)+' '+L.toFixed(1)+'" transform="rotate(-90 '+cx+' '+cx+')"'+tipAttr(c.tip)+'/>'
      +'<text x="'+cx+'" y="'+(c.sub?cx-1:cx+6)+'" text-anchor="middle" font-size="'+(c.fs||Math.round(s/4.2))+'" font-weight="600" class="val" style="font-size:'+(c.fs||Math.round(s/4.2))+'px">'+esc(c.label||Math.round(c.pct)+'%')+'</text>'
      +(c.sub?'<text x="'+cx+'" y="'+(cx+15)+'" text-anchor="middle">'+esc(c.sub)+'</text>':'');
    return svg(s,s,inner,'aria-label="'+esc(c.label||'')+'"');
  };

  T.gauge = function(c){
    var w=c.w||180, h=c.h||104, st=c.stroke||12, cx=w/2, cy=h-14, r=Math.min(cx-st, cy-st/2), p=Math.max(0,Math.min(1,c.pct/100));
    function pt(a){ return [cx+r*Math.cos(Math.PI*(1-a)), cy-r*Math.sin(Math.PI*(1-a))]; }
    var a0=pt(0), a1=pt(1), ap=pt(p);
    var big = '0 0 1';
    var inner='<path d="M'+a0[0]+' '+a0[1]+' A'+r+' '+r+' 0 0 1 '+a1[0]+' '+a1[1]+'" fill="none" stroke="var(--surface-3)" stroke-width="'+st+'" stroke-linecap="round"/>'
     +'<path d="M'+a0[0]+' '+a0[1]+' A'+r+' '+r+' 0 0 1 '+ap[0].toFixed(1)+' '+ap[1].toFixed(1)+'" fill="none" stroke="'+col(c.color)+'" stroke-width="'+st+'" stroke-linecap="round"'+tipAttr(c.tip)+'/>'
     +'<text x="'+cx+'" y="'+(cy-4)+'" text-anchor="middle" class="val" style="font-size:24px">'+esc(c.label||Math.round(c.pct)+'%')+'</text>'
     +(c.sub?'<text x="'+cx+'" y="'+(cy+12)+'" text-anchor="middle">'+esc(c.sub)+'</text>':'');
    return svg(w,h,inner,'aria-label="'+esc(c.label||'')+'"');
  };

  T.hbars = function(c){
    var max=c.max||Math.max.apply(null,c.items.map(function(i){return i.value;}));
    return '<div style="display:grid;gap:10px">'+c.items.map(function(i){
      var p=Math.max(2,i.value/max*100);
      return '<div'+tipAttr(i.tip)+' style="display:grid;grid-template-columns:'+(c.lw||96)+'px 1fr auto;gap:10px;align-items:center;font-size:14px"><span class="muted" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+esc(i.label)+'</span>'
       +'<span style="height:10px;border-radius:5px;background:var(--surface-3);overflow:hidden"><i style="display:block;height:100%;width:'+p+'%;background:'+col(i.color||c.color)+';border-radius:5px"></i></span>'
       +'<b style="font-weight:600;min-width:44px;text-align:right">'+esc(i.text||i.value)+'</b></div>';
    }).join('')+'</div>';
  };

  T.vbars = function(c){
    var w=c.w||320,h=c.h||150,l=34,b=24,t=14,r=8, n=c.items.length;
    var max=c.max||Math.max.apply(null,c.items.map(function(i){return i.value;}))*1.15, y=scale(0,max,h-b,t), bw=Math.min(28,(w-l-r)/n*0.55), step=(w-l-r)/n;
    var g='';
    [0,.5,1].forEach(function(f){ var yy=y(max*f/1.0*(f?1:0)); g+='<line class="grid" x1="'+l+'" x2="'+(w-r)+'" y1="'+yy+'" y2="'+yy+'"/><text x="'+(l-6)+'" y="'+(yy+4)+'" text-anchor="end">'+fmt(max*f/1.0*(f?1:0))+'</text>'; });
    var bars=c.items.map(function(it,i){
      var x=l+step*i+(step-bw)/2, yy=y(it.value);
      return '<rect x="'+x+'" y="'+yy+'" width="'+bw+'" height="'+(h-b-yy)+'" rx="4" fill="'+col(it.color||c.color)+'"'+tipAttr(it.tip||it.label+'：'+it.value)+'/><text x="'+(x+bw/2)+'" y="'+(h-6)+'" text-anchor="middle">'+esc(it.label)+'</text>'
        +(c.labels?'<text x="'+(x+bw/2)+'" y="'+(yy-5)+'" text-anchor="middle" class="val">'+esc(it.text||it.value)+'</text>':'');
    }).join('');
    return svg(w,h,g+bars);
  };

  T.hist = function(c){
    var w=c.w||340,h=c.h||120,l=4,b=22,t=14,r=4, v=c.values, n=v.length, max=Math.max.apply(null,v)*1.1;
    var step=(w-l-r)/n, bw=step-3, y=scale(0,max,h-b,t), hi=c.highlight||[0,-1];
    var bars=v.map(function(a,i){
      var on=i>=hi[0]&&i<=hi[1], x=l+i*step+1.5;
      return '<rect x="'+x+'" y="'+y(a)+'" width="'+bw+'" height="'+(h-b-y(a))+'" rx="3" fill="'+(on?col(c.color):'var(--surface-3)')+'"'+tipAttr((c.labels&&c.labels[i]?c.labels[i]+'：':'')+a+(c.unit||''))+'/>';
    }).join('');
    var ax='';
    if(c.labels){ [0,Math.floor(n/2),n-1].forEach(function(i){ ax+='<text x="'+(l+i*step+step/2)+'" y="'+(h-6)+'" text-anchor="middle">'+esc(c.labels[i])+'</text>'; }); }
    var marks=(c.marks||[]).map(function(m){ var x=l+m.at*step; return '<line x1="'+x+'" x2="'+x+'" y1="'+(t-4)+'" y2="'+(h-b)+'" stroke="'+col(m.color||'wait')+'" stroke-width="1.5" stroke-dasharray="4 3"/><text x="'+x+'" y="'+(t-6)+'" text-anchor="middle" style="fill:'+col(m.color||'wait')+';font-weight:600">'+esc(m.label)+'</text>'; }).join('');
    return svg(w,h,bars+ax+marks);
  };

  T.scatter = function(c){
    var w=c.w||520,h=c.h||280,l=44,b=34,t=16,r=16;
    var x=scale(c.xmin,c.xmax,l,w-r), y=scale(c.ymin,c.ymax,h-b,t), g='';
    for(var i=0;i<=4;i++){ var yv=c.ymin+(c.ymax-c.ymin)*i/4, yy=y(yv); g+='<line class="grid" x1="'+l+'" x2="'+(w-r)+'" y1="'+yy+'" y2="'+yy+'"/><text x="'+(l-8)+'" y="'+(yy+4)+'" text-anchor="end">'+fmt(yv)+(c.yunit||'')+'</text>'; }
    for(var j=0;j<=4;j++){ var xv=c.xmin+(c.xmax-c.xmin)*j/4; g+='<text x="'+x(xv)+'" y="'+(h-b+18)+'" text-anchor="middle">'+fmt(xv)+'</text>'; }
    g+='<text x="'+((l+w-r)/2)+'" y="'+(h-4)+'" text-anchor="middle">'+esc(c.xlabel||'')+'</text>';
    g+='<text x="10" y="'+t+'" >'+esc(c.ylabel||'')+'</text>';
    var lines=(c.hlines||[]).map(function(m){ var yy=y(m.y); return '<line x1="'+l+'" x2="'+(w-r)+'" y1="'+yy+'" y2="'+yy+'" stroke="'+col(m.color||'block')+'" stroke-width="1.5" stroke-dasharray="5 4"/><text x="'+(w-r)+'" y="'+(yy-6)+'" text-anchor="end" style="fill:'+col(m.color||'block')+';font-weight:600">'+esc(m.label)+'</text>'; }).join('');
    var zone=(c.zone? '<rect x="'+x(c.zone.x0)+'" y="'+y(c.zone.y1)+'" width="'+(x(c.zone.x1)-x(c.zone.x0))+'" height="'+(y(c.zone.y0)-y(c.zone.y1))+'" rx="8" fill="var(--primary)" opacity=".07"/><text x="'+(x(c.zone.x0)+8)+'" y="'+(y(c.zone.y1)+16)+'" style="fill:var(--primary-strong);font-weight:600">'+esc(c.zone.label||'')+'</text>':'');
    var pts=c.points.map(function(p){
      var rr=p.r||7, color=col(p.color||'primary');
      var fill=p.hollow?'var(--surface)':color;
      return '<circle cx="'+x(p.x)+'" cy="'+y(p.y)+'" r="'+rr+'" fill="'+fill+'" fill-opacity="'+(p.hollow?1:.85)+'" stroke="'+(p.hollow?color:'var(--surface)')+'" stroke-width="'+(p.hollow?1.8:2)+'"'+tipAttr(p.tip||p.label)+'/>'
        +(p.label&&p.show?'<text x="'+(x(p.x)+rr+5)+'" y="'+(y(p.y)+4)+'" class="val">'+esc(p.label)+'</text>':'');
    }).join('');
    return svg(w,h,g+zone+lines+pts,'aria-label="散点图"');
  };

  T.waterfall = function(c){
    var w=c.w||420,rowH=c.rowH||26,l=c.lw||118,r=52,items=c.items,h=items.length*rowH+30;
    var max=c.max||items[0].value, x=scale(0,max,l,w-r), run=0, out='', legendUsed={};
    items.forEach(function(it,i){
      var y0=i*rowH+6, x0,x1,color;
      if(it.type==='revenue'){ x0=x(0); x1=x(it.value); run=it.value; color='var(--primary)'; }
      else if(it.type==='profit'){ x0=x(0); x1=x(it.value); color=it.value>=0?'var(--ok)':'var(--block)'; }
      else { var after=run-it.value; x0=x(after); x1=x(run); run=after; color=col(it.color||'s1'); }
      var bw=Math.max(2,x1-x0);
      out+='<text x="'+(l-10)+'" y="'+(y0+rowH/2+1)+'" text-anchor="end" style="fill:var(--text-2)">'+esc(it.label)+'</text>'
        +'<rect x="'+x0+'" y="'+y0+'" width="'+bw+'" height="'+(rowH-10)+'" rx="4" fill="'+color+'"'+tipAttr(it.tip||(it.label+'：¥'+fmt(it.value)))+'/>'
        +'<text x="'+(x1+7)+'" y="'+(y0+rowH/2+1)+'" class="val">'+(it.type==='cost'?'−':'')+'¥'+fmt(it.value)+'</text>';
      if(i<items.length-1 && it.type!=='profit'){ out+='<line x1="'+x(run)+'" x2="'+x(run)+'" y1="'+(y0+rowH-10)+'" y2="'+(y0+rowH+0)+'" stroke="var(--axis)" stroke-width="1" stroke-dasharray="2 2"/>'; }
    });
    out+='<line class="axis" x1="'+l+'" x2="'+l+'" y1="2" y2="'+(h-24)+'"/>';
    var leg=(c.legend||[]).map(function(g){ return '<span><i style="background:'+col(g.color)+'"></i>'+esc(g.label)+'</span>'; }).join('');
    return svg(w,h-24,out,'aria-label="成本瀑布图"')+(leg?'<div class="legend" style="margin-top:8px">'+leg+'</div>':'');
  };

  T.radar = function(c){
    var s=c.size||200, cx=s/2, cy=s/2+4, R=s/2-34, n=c.axes.length, out='';
    function pt(i,k){ var a=-Math.PI/2+2*Math.PI*i/n; return [cx+R*k*Math.cos(a), cy+R*k*Math.sin(a)]; }
    [0.33,0.66,1].forEach(function(k){ out+='<polygon points="'+c.axes.map(function(_,i){return pt(i,k).join(',');}).join(' ')+'" fill="none" stroke="var(--grid)" stroke-width="1"/>'; });
    c.axes.forEach(function(a,i){ var p=pt(i,1), q=pt(i,1.22); out+='<line x1="'+cx+'" y1="'+cy+'" x2="'+p[0]+'" y2="'+p[1]+'" stroke="var(--grid)"/><text x="'+q[0]+'" y="'+(q[1]+4)+'" text-anchor="middle">'+esc(a.label)+'</text>'; });
    (c.series||[{values:c.axes.map(function(a){return a.value;}),color:'primary'}]).forEach(function(se){
      var pts=se.values.map(function(v,i){return pt(i,v).join(',');}).join(' ');
      out+='<polygon points="'+pts+'" fill="'+col(se.color)+'" fill-opacity=".18" stroke="'+col(se.color)+'" stroke-width="2" stroke-linejoin="round"/>'
        +se.values.map(function(v,i){var p=pt(i,v);return '<circle cx="'+p[0]+'" cy="'+p[1]+'" r="3.5" fill="'+col(se.color)+'" stroke="var(--surface)" stroke-width="1.5"'+tipAttr(c.axes[i].label+'：'+Math.round(v*100))+'/>';}).join('');
    });
    return svg(s,s+8,out,'aria-label="雷达图"');
  };

  T.stack = function(c){
    var total=c.items.reduce(function(a,i){return a+i.value;},0);
    var bar='<div style="display:flex;gap:2px;height:'+(c.h||14)+'px;border-radius:7px;overflow:hidden">'+c.items.map(function(i){
      return '<i'+tipAttr(i.tip||(i.label+'：'+i.text))+' style="display:block;height:100%;width:'+(i.value/total*100)+'%;background:'+col(i.color)+';border-radius:3px"></i>'; }).join('')+'</div>';
    var leg=c.legend===false?'':'<div class="legend" style="margin-top:8px">'+c.items.map(function(i){ return '<span><i style="background:'+col(i.color)+'"></i>'+esc(i.label)+(i.text?' <b style="color:var(--text);font-weight:600">'+esc(i.text)+'</b>':'')+'</span>'; }).join('')+'</div>';
    return bar+leg;
  };

  T.line = function(c){
    var w=c.w||520,h=c.h||190,l=40,b=26,t=14,r=14, n=c.labels.length;
    var all=[].concat.apply([],c.series.map(function(s){return s.values;}));
    var ymin=c.ymin!=null?c.ymin:0, ymax=c.ymax||Math.max.apply(null,all)*1.15;
    var x=scale(0,n-1,l,w-r), y=scale(ymin,ymax,h-b,t), g='';
    for(var i=0;i<=3;i++){ var v=ymin+(ymax-ymin)*i/3, yy=y(v); g+='<line class="grid" x1="'+l+'" x2="'+(w-r)+'" y1="'+yy+'" y2="'+yy+'"/><text x="'+(l-8)+'" y="'+(yy+4)+'" text-anchor="end">'+fmt(v,c.dec||0)+(c.unit||'')+'</text>'; }
    c.labels.forEach(function(lab,i){ if(n<=8||i%Math.ceil(n/8)===0) g+='<text x="'+x(i)+'" y="'+(h-6)+'" text-anchor="middle">'+esc(lab)+'</text>'; });
    var lines=c.series.map(function(s,si){
      var pts=s.values.map(function(v,i){return x(i).toFixed(1)+','+y(v).toFixed(1);});
      var color=col(s.color||('s'+(si+1)));
      var area=si===0&&c.area!==false?'<polygon points="'+x(0)+','+(h-b)+' '+pts.join(' ')+' '+x(n-1)+','+(h-b)+'" fill="'+color+'" opacity=".1"/>':'';
      var dots=s.values.map(function(v,i){return '<circle cx="'+x(i)+'" cy="'+y(v)+'" r="'+(i===n-1?4.5:9)+'" fill="'+(i===n-1?color:'transparent')+'" stroke="'+(i===n-1?'var(--surface)':'none')+'" stroke-width="2"'+tipAttr(s.name+' · '+c.labels[i]+'：'+fmt(v,c.dec||0)+(c.unit||''))+'/>';}).join('');
      return area+'<polyline points="'+pts.join(' ')+'" fill="none" stroke="'+color+'" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" '+(s.dash?'stroke-dasharray="5 4"':'')+'/>'+dots;
    }).join('');
    var ref=(c.hlines||[]).map(function(m){ var yy=y(m.y); return '<line x1="'+l+'" x2="'+(w-r)+'" y1="'+yy+'" y2="'+yy+'" stroke="'+col(m.color||'block')+'" stroke-dasharray="5 4" stroke-width="1.5"/><text x="'+(w-r)+'" y="'+(yy-6)+'" text-anchor="end" style="fill:'+col(m.color||'block')+';font-weight:600">'+esc(m.label)+'</text>'; }).join('');
    var leg=c.series.length>1?'<div class="legend" style="margin-top:8px">'+c.series.map(function(s,si){return '<span><i style="background:'+col(s.color||('s'+(si+1)))+'"></i>'+esc(s.name)+'</span>';}).join('')+'</div>':'';
    return svg(w,h,g+ref+lines,'aria-label="折线图"')+leg;
  };

  T.heat = function(c){
    var rows=c.rows, cols=c.cols, m=c.matrix, max=c.max||Math.max.apply(null,[].concat.apply([],m)), cw=c.cw||16, ch=c.ch||16, gap=3, l=c.lw||34, t=18;
    var w=l+cols.length*(cw+gap), h=t+rows.length*(ch+gap)+4, out='';
    cols.forEach(function(cl,j){ if(cl!=='') out+='<text x="'+(l+j*(cw+gap)+cw/2)+'" y="12" text-anchor="middle">'+esc(cl)+'</text>'; });
    rows.forEach(function(rw,i){
      out+='<text x="'+(l-8)+'" y="'+(t+i*(ch+gap)+ch-4)+'" text-anchor="end">'+esc(rw)+'</text>';
      m[i].forEach(function(v,j){
        var a=v/max, tp=(c.tip?c.tip(rows[i],cols[j],v):rows[i]+' '+cols[j]+'：'+v);
        out+='<rect x="'+(l+j*(cw+gap))+'" y="'+(t+i*(ch+gap))+'" width="'+cw+'" height="'+ch+'" rx="4" fill="'+(v===0?'var(--surface-3)':col(c.color||'primary'))+'" fill-opacity="'+(v===0?1:(0.18+0.82*a).toFixed(2))+'"'+tipAttr(tp)+'/>';
      });
    });
    return svg(w,h,out,'aria-label="热力图"');
  };

  T.donut = function(c){
    var s=c.size||150, st=c.stroke||20, r=(s-st)/2, cx=s/2, L=2*Math.PI*r, total=c.items.reduce(function(a,i){return a+i.value;},0), off=0, out='';
    out+='<circle cx="'+cx+'" cy="'+cx+'" r="'+r+'" fill="none" stroke="var(--surface-3)" stroke-width="'+st+'"/>';
    c.items.forEach(function(it){
      var len=it.value/total*L;
      out+='<circle cx="'+cx+'" cy="'+cx+'" r="'+r+'" fill="none" stroke="'+col(it.color)+'" stroke-width="'+st+'" stroke-dasharray="'+Math.max(0,len-2).toFixed(1)+' '+(L-Math.max(0,len-2)).toFixed(1)+'" stroke-dashoffset="'+(-off).toFixed(1)+'" transform="rotate(-90 '+cx+' '+cx+')"'+tipAttr(it.tip||(it.label+'：'+it.text))+'/>';
      off+=len;
    });
    out+='<text x="'+cx+'" y="'+(cx+(c.sub?0:6))+'" text-anchor="middle" class="val" style="font-size:'+(c.fs||20)+'px">'+esc(c.label||'')+'</text>'+(c.sub?'<text x="'+cx+'" y="'+(cx+16)+'" text-anchor="middle">'+esc(c.sub)+'</text>':'');
    var leg=c.legend===false?'':'<div class="legend" style="flex-direction:column;gap:6px">'+c.items.map(function(i){return '<span><i style="background:'+col(i.color)+'"></i>'+esc(i.label)+(i.text?' <b style="color:var(--text);font-weight:600">'+esc(i.text)+'</b>':'')+'</span>';}).join('')+'</div>';
    return '<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap">'+svg(s,s,out,'aria-label="环形图"')+leg+'</div>';
  };

  CP.chart = T;
  CP.mountCharts = function(root){
    (root||document).querySelectorAll('[data-chart]').forEach(function(el){
      if(el.dataset.mounted) return;
      var fn=T[el.dataset.chart]; if(!fn) return;
      var cfg={}; try{ cfg=JSON.parse(el.dataset.cfg||'{}'); }catch(e){ console.warn('chart cfg',e); }
      el.innerHTML=fn(cfg); el.dataset.mounted='1'; el.classList.add('chart');
    });
  };

  /* 悬停提示 */
  var tip;
  function ensureTip(){ if(!tip){ tip=document.createElement('div'); tip.className='tip'; document.body.appendChild(tip);} return tip; }
  document.addEventListener('mouseover',function(e){
    var t=e.target.closest&&e.target.closest('[data-tip]'); if(!t) return;
    var el=ensureTip(); el.innerHTML=t.getAttribute('data-tip'); el.classList.add('on');
  });
  document.addEventListener('mousemove',function(e){
    if(!tip||!tip.classList.contains('on')) return;
    var x=e.clientX+14, y=e.clientY+16; if(x+tip.offsetWidth>innerWidth-8) x=e.clientX-tip.offsetWidth-14; if(y+tip.offsetHeight>innerHeight-8) y=e.clientY-tip.offsetHeight-14;
    tip.style.left=x+'px'; tip.style.top=y+'px';
  });
  document.addEventListener('mouseout',function(e){ var t=e.target.closest&&e.target.closest('[data-tip]'); if(t&&tip) tip.classList.remove('on'); });
})();
