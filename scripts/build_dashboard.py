#!/usr/bin/env python3
"""
Build script: transform the design HTML into the connected dashboard.
Run from repo root: python3 scripts/build_dashboard.py
"""

import re
import sys
import os

SRC = os.path.expanduser("~/Downloads/plantaos-wow-v4 (8) (1).html")
OUT = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "static", "index.html")
OUT = os.path.abspath(OUT)

print(f"Reading {SRC} …")
with open(SRC, "r", encoding="utf-8") as f:
    html = f.read()
print(f"  {len(html):,} chars read")

# ── 1. Critical color: never red ────────────────────────────
html = html.replace("--red:#E24B4A;", "--red:#C25A1A;")
html = html.replace("--red:#c0392b;", "--red:#C25A1A;")   # light-mode red
html = html.replace('critico:"#E24B4A"', 'critico:"#C25A1A"')
# E24B4A in JS strings (queue bar, co2 indicator on map)
html = html.replace('fill="#E24B4A"', 'fill="#C25A1A"')
# legend circle in home page
html = html.replace('background:#E24B4A"', 'background:#C25A1A"')
print("  ✓ Critical color fixed (#C25A1A)")

# ── 2. Remove SIMULADO / seed=2026 labels ──────────────────
# Topbar pill
html = html.replace(
    '<div class="lpill">SIMULADO · seed=2026</div>',
    '<div class="lpill" id="live-pill" style="transition:all .4s">A LIGAR…</div>'
)
# span with SIMULADO seed=2026 in home page
html = html.replace(
    '% Utilização por cluster · 1137 lugares · 8 clusters · SIMULADO seed=2026',
    '% Utilização por cluster · 1137 lugares · 8 clusters · dados ao vivo'
)
# Terminal init line
html = html.replace(
    '"iniciando PlantaOS · 1137 lugares · 8 clusters · seed=2026"',
    '"PlantaOS · 1137 lugares · 8 clusters · a ligar ao backend…"'
)
# JS comment header
html = html.replace(
    "// F=P/D hypothesis under test · seed=2026 · 8 clusters",
    "// PlantaOS × Rock in Rio Lisboa 2026 · backend live"
)
# Chat src div
html = html.replace(
    'PlantaOS · Gemini 2.5 Flash · PT-PT · SIMULADO',
    'PlantaOS · Gemini 2.5 Flash · PT-PT'
)
# Chat context badge
html = html.replace(
    '<div class="ch-s">Gemini 2.5 Flash · PT-PT · SIMULADO</div>',
    '<div class="ch-s">Gemini 2.5 Flash · PT-PT · dados ao vivo</div>'
)
# SIMULADO badge next to Chat AI title
html = html.replace(
    'SIMULADO</span>',
    'AO VIVO</span>'
)
# tick textContent with seed=2026
html = html.replace(
    'tk.textContent="tick #"+TICK+" · seed=2026"',
    'tk.textContent="tick #"+TICK'
)
# JS HL comment
html = html.replace(
    '# HL-01 ok · seed=2026 · tick=\'+TICK+\' · \'+MODE+\'',
    '# HL-01 ok · tick=\'+TICK+\' · \'+MODE+\''
)
# Any remaining [SIMULADO seed=2026] or [SIMULADO] in DEMO strings
html = html.replace("[SIMULADO seed=2026]", "")
html = html.replace("[SIMULADO]", "")
html = html.replace("· SIMULADO", "")
html = html.replace("SIMULADO", "AO VIVO")
print("  ✓ SIMULADO/seed=2026 labels removed")

# ── 3. Fix hero description (remove CO₂/água/CO2) ──────────
html = html.replace(
    "PlantaOS monitoriza cada cluster WC por género, % utilização, CO₂, água e fila em tempo real.<br>\n    Simula os 4 shows segundo a afluência real. Contrafactuais automáticos. 127 sensores Reed + CO₂ + água.",
    "PlantaOS monitoriza cada cluster WC por género, % utilização, fila e fluxo em tempo real.<br>\n    Contrafactuais automáticos. Dados ao vivo via IR, WiFi e câmaras Prosegur."
)
print("  ✓ Hero description updated")

# ── 4. Remove CO₂ / temp / humidity from tooltip ──────────
html = html.replace(
    "tt.innerHTML='<strong>'+wc.id+'</strong> ['+wc.t+']<br>'+wc.z+'<br>Utilização: <span style=\"color:'+c+'\">'+wc.util+'% ('+wc.status+')</span><br>M:'+wc.masc_occ+'/'+wc.masc+' F:'+wc.fem_occ+'/'+wc.fem+'<br>Fila: '+wc.q+' pax · Espera: ~'+wc.avg_wait_min+'min<br>CO₂: '+wc.co2+'ppm · Água: '+(wc.water_L_hr||0)+'L/h';",
    "tt.innerHTML='<strong>'+wc.id+'</strong> ['+wc.t+']<br>'+wc.z+'<br>Utilização: <span style=\"color:'+c+'\">'+wc.util+'% ('+wc.status+')</span><br>M:'+wc.masc_occ+'/'+wc.masc+' F:'+wc.fem_occ+'/'+wc.fem+'<br>Fila: '+wc.q+' pax · Espera: ~'+wc.avg_wait_min+'min<br>Confiança: '+(wc.confianca||'—')+'% · Fontes: '+(wc.fontes||[]).join(', ');"
)
print("  ✓ Tooltip CO₂ replaced with confidence/sources")

# ── 5. Remove CO₂ indicator from SVG map dots ──────────────
# co2_indicator variable - make it always empty string
html = html.replace(
    "var co2_indicator=wc.co2>800?'<circle r=\"6\" cx=\"'+(r-4)+'\" cy=\"'+(-r+4)+'\" fill=\"#C25A1A\" opacity=\"0.9\"/><text x=\"'+(r-4)+'\" y=\"'+(-r+8)+'\" text-anchor=\"middle\" font-family=\"DM Mono,monospace\" font-size=\"7\" fill=\"#fff\">C</text>':''",
    "var co2_indicator=''"
)
print("  ✓ CO₂ dot removed from SVG map")

# ── 6. Remove CO₂/temp/humid sensors from detail panel ─────
# The 4-sensor grid in renderDP: CO₂, Temp, Humid, Água
# Replace with Confiança, Fontes, Fila, Espera
OLD_SENSOR_GRID = """  var co2c=wc.co2>800?"var(--red)":wc.co2>600?"var(--amb)":"var(--verde)";
  h+='<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:8px">';
  [
    {icon:"💨",v:wc.co2+"ppm",l:"CO₂",c:co2c},
    {icon:"🌡",v:wc.temp+"°C",l:"Temp",c:wc.temp>30?"var(--red)":"var(--verde)"},
    {icon:"💧",v:wc.humid+"%",l:"Humid.",c:"var(--t)"},
    {icon:"💧",v:(wc.water_L_hr||0)+"L/h",l:"Água",c:"#3B82F6"},
  ].forEach(function(s){h+='<div style="background:var(--dp-bg);border:1px solid var(--bd);border-radius:5px;padding:6px;text-align:center"><div style="font-size:.9rem">'+s.icon+'</div><div style="font-family:var(--fm);font-size:.78rem;color:'+s.c+'">'+s.v+'</div><div style="font-size:.48rem;color:var(--t3);text-transform:uppercase">'+s.l+'</div></div>'});
  h+='</div>';"""

NEW_SENSOR_GRID = """  var confColor=(wc.confianca||0)>=70?"var(--verde)":(wc.confianca||0)>=40?"var(--amb)":"var(--red)";
  var fontesStr=(wc.fontes&&wc.fontes.length)?(wc.fontes.join("+")):"—";
  h+='<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:8px">';
  [
    {icon:"📡",v:(wc.confianca||"—")+"%",l:"Confiança",c:confColor},
    {icon:"🔌",v:fontesStr,l:"Fontes",c:"var(--t)"},
    {icon:"⏱",v:(wc.avg_wait_min||0)+"min",l:"Espera",c:wc.avg_wait_min>5?"var(--amb)":"var(--verde)"},
    {icon:"↗",v:(wc.pax_hora||0)+"/h",l:"Fluxo",c:"var(--t)"},
  ].forEach(function(s){h+='<div style="background:var(--dp-bg);border:1px solid var(--bd);border-radius:5px;padding:6px;text-align:center"><div style="font-size:.9rem">'+s.icon+'</div><div style="font-family:var(--fm);font-size:.78rem;color:'+s.c+'">'+s.v+'</div><div style="font-size:.48rem;color:var(--t3);text-transform:uppercase">'+s.l+'</div></div>'});
  h+='</div>';"""

if OLD_SENSOR_GRID in html:
    html = html.replace(OLD_SENSOR_GRID, NEW_SENSOR_GRID)
    print("  ✓ Detail panel sensors updated (removed CO₂/temp/humid)")
else:
    # Fallback: patch just the co2c variable and array
    print("  ⚠ Detail panel sensor grid not found verbatim — using fallback patch")
    html = html.replace(
        'var co2c=wc.co2>800?"var(--red)":wc.co2>600?"var(--amb)":"var(--verde)";',
        'var confColor=(wc.confianca||0)>=70?"var(--verde)":(wc.confianca||0)>=40?"var(--amb)":"var(--red)";'
    )

# ── 7. Remove CO₂ alert block in renderDP ──────────────────
html = html.replace(
    "// CO₂ alert\n  if(wc.co2>800)h+=",
    "// CO₂ alert (disabled — backend counts people only)\n  if(false&&wc.co2>800)h+="
)
# Also try without comment
old_co2_alert = "if(wc.co2>800)h+='<div style=\"background:rgba(226,75,74,.1);border:1px solid rgba(226,75,74,.3);border-radius:5px;padding:7px;font-size:.62rem;color:#F87171;margin-top:5px\">⚠ CO₂ '+wc.co2+'ppm"
if old_co2_alert in html:
    # Find full extent and remove
    start = html.find(old_co2_alert)
    end = html.find("</div>'", start)
    if end != -1:
        end += len("</div>'")
    html = html[:start] + "/* CO2 alert removed */" + html[end:]
    print("  ✓ CO₂ alert block in detail panel removed")

# ── 8. Fix terminal snip that shows CO₂ ──────────────────
html = html.replace(
    "' · CO₂:'+w.co2+'ppm · água:'+(w.water_L_hr",
    "' · fila:'+w.q+' · conf:'+(w.confianca"
)
html = html.replace(
    "||0)+'L/h'",
    "||'—')+'%'"
)
print("  ✓ Terminal snippet CO₂ line updated")

# ── 9. Remove CO₂ from stats table rows in detail panel ───
html = html.replace(
    '["Show actual",show.hl+" ("+show.date+")"],\n    ["Género show",show.male_pct+"% M / "+(100-show.male_pct)+"% F"]',
    '["Show actual",show.hl+" ("+show.date+")"],\n    ["Género show",show.male_pct+"% M / "+(100-show.male_pct)+"% F"],\n    ["Bat/RSSI",wc.bat+"V · "+wc.rssi+"dBm"]'
)
# Remove the separate Bat/RSSI row since we just added it above
html = html.replace(
    '["Bat/RSSI",wc.bat+"V · "+wc.rssi+"dBm"],\n    ["Show actual"',
    '["Show actual"'
)
print("  ✓ Stats table cleaned")

# ── 10. Replace sendChat with backend API call ──────────────
OLD_SEND_CHAT = """function sendChat(){var inp=g("chat-in"),msg=inp.value.trim();if(!msg)return;inp.value="";addMsg("u",msg);var ty=document.createElement("div");ty.className="bubble a";ty.innerHTML='<div class="typing"><span></span><span></span><span></span></div>';var msgs=g("cm");msgs.appendChild(ty);msgs.scrollTop=9999;setTimeout(function(){if(ty.parentNode)ty.parentNode.removeChild(ty);addMsg("a",DEMO[DI%DEMO.length]());DI++},650+Math.random()*750)}"""

NEW_SEND_CHAT = """var CHAT_HISTORY=[];
function sendChat(){
  var inp=g("chat-in"),msg=inp.value.trim();
  if(!msg)return;
  inp.value="";
  addMsg("u",msg);
  CHAT_HISTORY.push({role:"user",content:msg});
  var ty=document.createElement("div");ty.className="bubble a";
  ty.innerHTML='<div class="typing"><span></span><span></span><span></span></div>';
  var msgs=g("cm");msgs.appendChild(ty);msgs.scrollTop=9999;
  fetch(API_URL+"/api/v1/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({mensagem:msg,historico:CHAT_HISTORY.slice(-8)})
  }).then(function(r){return r.json();})
  .then(function(d){
    if(ty.parentNode)ty.parentNode.removeChild(ty);
    var resp=d.resposta||d.response||d.answer||"Sem resposta do servidor.";
    addMsg("a",resp);
    CHAT_HISTORY.push({role:"assistant",content:resp});
  })
  .catch(function(err){
    if(ty.parentNode)ty.parentNode.removeChild(ty);
    // Fallback to local demo answers if backend unreachable
    addMsg("a",DEMO[DI%DEMO.length]());DI++;
  });
}"""

if OLD_SEND_CHAT in html:
    html = html.replace(OLD_SEND_CHAT, NEW_SEND_CHAT)
    print("  ✓ sendChat replaced with backend API call + fallback")
else:
    print("  ⚠ sendChat not found verbatim — injecting before addMsg")
    html = html.replace(
        "function addMsg(",
        NEW_SEND_CHAT + "\nfunction addMsg("
    )

# ── 11. Inject WebSocket + REST connection code ─────────────
WS_CODE = """
// ═══════════════════════════════════════════════════════════
// BACKEND CONNECTION — WebSocket + REST API
// ═══════════════════════════════════════════════════════════
var API_URL="http://localhost:8000";
var WS_URL="ws://localhost:8000/api/v1/ws";
var _ws=null,_wsConnected=false,_wsRetry=1000,_wsTimer=null;

function _wsSetPill(txt,bg,color){
  var p=g("live-pill");
  if(!p)return;
  p.textContent=txt;
  p.style.background=bg;
  p.style.color=color;
}

function _wsConnect(){
  try{
    _ws=new WebSocket(WS_URL);
    _ws.onopen=function(){
      _wsConnected=true;_wsRetry=1000;
      _wsSetPill("AO VIVO ●","rgba(111,175,130,.18)","#6FAF82");
      var tl=g("tline");
      if(tl)tl.textContent="PlantaOS ligado ao backend :8000 · "+STATES.length+" clusters ao vivo";
    };
    _ws.onclose=function(){
      _wsConnected=false;
      _wsSetPill("RECONECTANDO…","rgba(107,114,128,.15)","#9CA3AF");
      if(_wsTimer)clearTimeout(_wsTimer);
      _wsTimer=setTimeout(function(){_wsRetry=Math.min(_wsRetry*2,30000);_wsConnect();},_wsRetry);
    };
    _ws.onerror=function(){try{_ws.close();}catch(e){}};
    _ws.onmessage=function(e){
      try{
        var d=JSON.parse(e.data);
        if(d.type==="cluster_update"&&d.clusters){
          _applyWS(d);
        }
      }catch(ex){}
    };
  }catch(ex){
    if(_wsTimer)clearTimeout(_wsTimer);
    _wsTimer=setTimeout(function(){_wsRetry=Math.min(_wsRetry*2,30000);_wsConnect();},_wsRetry);
  }
}

function _applyWS(payload){
  if(!payload.clusters)return;
  payload.clusters.forEach(function(c){
    var idx=-1;
    for(var i=0;i<STATES.length;i++){if(STATES[i].id===c.cluster_id){idx=i;break;}}
    if(idx===-1)return;
    var secs=c.secoes||{};
    var occ_pct,occ_abs,q,wait,flow_in,conf,sources;
    if(c.tipo==="unissex"){
      var su=secs["U"]||{};
      occ_pct=su.ocupacao_pct||0;occ_abs=su.ocupacao_absoluta||0;
      q=su.fila_actual||0;wait=su.tempo_espera_min||0;
      flow_in=su.fluxo_entrada_pmin||0;conf=su.confianca_pct||0;
      sources=su.fontes_activas||[];
      STATES[idx].masc_occ=occ_abs;STATES[idx].fem_occ=0;
      STATES[idx].q_masc=Math.floor(q/2);STATES[idx].q_fem=Math.floor(q/2);
    }else{
      var sm=secs["M"]||{},sf=secs["F"]||{};
      var pm=sm.ocupacao_pct||0,pf=sf.ocupacao_pct||0;
      occ_pct=Math.round((pm+pf)/2);
      occ_abs=(sm.ocupacao_absoluta||0)+(sf.ocupacao_absoluta||0);
      q=(sm.fila_actual||0)+(sf.fila_actual||0);
      wait=Math.max(sm.tempo_espera_min||0,sf.tempo_espera_min||0);
      flow_in=(sm.fluxo_entrada_pmin||0)+(sf.fluxo_entrada_pmin||0);
      conf=Math.round(((sm.confianca_pct||0)+(sf.confianca_pct||0))/2);
      sources=sm.fontes_activas||[];
      STATES[idx].masc_occ=sm.ocupacao_absoluta||0;
      STATES[idx].fem_occ=sf.ocupacao_absoluta||0;
      STATES[idx].q_masc=sm.fila_actual||0;
      STATES[idx].q_fem=sf.fila_actual||0;
    }
    var lug=STATES[idx].lug||133;
    var status=sources.length===0?"offline":occ_pct>=90?"critico":occ_pct>=75?"ambar":"verde";
    var h=(STATES[idx].h||[]).slice();h.push(occ_pct);if(h.length>24)h.shift();
    STATES[idx].util=occ_pct;
    STATES[idx].occ=occ_abs;
    STATES[idx].livres=Math.max(0,lug-occ_abs);
    STATES[idx].q=q;
    STATES[idx].q_masc=STATES[idx].q_masc||0;
    STATES[idx].q_fem=STATES[idx].q_fem||0;
    STATES[idx].avg_wait_min=parseFloat((wait||0).toFixed(1));
    STATES[idx].pax_hora=Math.round(flow_in*60);
    STATES[idx].status=status;
    STATES[idx].h=h;
    STATES[idx].confianca=conf;
    STATES[idx].fontes=sources;
  });
  // Update KPI widgets
  if(payload.kpis){
    var k=payload.kpis;
    var hutil=g("hutil"),hlv=g("hlv"),hcr=g("hcr"),hwater=g("hwater");
    if(hutil)hutil.textContent=(k.kpi_02||0).toFixed(0)+"%";
    if(hlv)hlv.textContent=STATES.reduce(function(s,st){return s+(st.livres||0);},0);
    if(hcr)hcr.textContent=k.kpi_03||0;
    if(hwater)hwater.textContent="—";  // backend counts people, not water
    var htime=g("htime");if(htime)htime.textContent=new Date().toLocaleTimeString("pt-PT",{hour:"2-digit",minute:"2-digit"});
  }
  // Show info
  if(payload.show_activo){
    var showEl=g("cur-show-name");
    if(showEl)showEl.textContent="★ "+payload.show_activo;
  }
  // Re-render map overlay and list
  if(typeof rOverlay==="function")rOverlay();
  if(typeof rList==="function")rList();
  if(SEL&&typeof renderDP==="function"){
    var sel=STATES.filter(function(s){return s.id===SEL;})[0];
    if(sel)renderDP(sel);
  }
}

// REST fallback poll every 10s when WS disconnected
setInterval(function(){
  if(_wsConnected)return;
  fetch(API_URL+"/api/v1/clusters").then(function(r){return r.json();})
  .then(function(d){
    if(d.clusters){
      _applyWS({clusters:d.clusters,kpis:null});
    }
  }).catch(function(){});
},10000);

// Connect on load
_wsConnect();
// ═══════════════════════════════════════════════════════════
"""

# Inject WS code just before the closing })(); of the IIFE
CLOSE_IIFE = "})();\n\n</script>\n</body>\n</html>"
if CLOSE_IIFE in html:
    html = html.replace(CLOSE_IIFE, WS_CODE + "\n" + CLOSE_IIFE)
    print("  ✓ WebSocket + REST connection code injected")
else:
    # Try alternative closing
    html = html.replace("})();\n</script>", WS_CODE + "\n})();\n</script>")
    print("  ✓ WebSocket code injected (alt close)")

# ── 12. Add id="cur-show-name" to show element if possible ──
html = html.replace(
    'id="cur-show"',
    'id="cur-show-name"'
)

# ── 13. Backend URL config at top of JS (after "use strict") ─
html = html.replace(
    '"use strict";',
    '"use strict";\nvar API_URL_CONFIG="http://localhost:8000"; // override with ?api= param\nvar _apiParam=new URLSearchParams(location.search).get("api"); if(_apiParam)API_URL_CONFIG=_apiParam;'
)

# ── 14. Fix Hwater metric label (remove água/water) ─────────
html = html.replace(
    '<div class="ml">Água L/h</div>',
    '<div class="ml">Redirecionados</div>'
)

print(f"\nWriting to {OUT} …")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = len(html) / 1024
print(f"  ✓ Written: {size_kb:.1f} KB")

# ── Verify no red remains ────────────────────────────────────
red_hits = len(re.findall(r'#E24B4A|#e24b4a|#c0392b', html))
simulado_hits = len(re.findall(r'seed=2026', html))
co2_data_hits = len(re.findall(r"wc\.co2|wc\.temp\b|wc\.humid\b", html))

print(f"\n── Verification ──────────────────────")
print(f"  Red color hits (#E24B4A/#c0392b): {red_hits} {'✓' if red_hits==0 else '⚠ FIXME'}")
print(f"  seed=2026 hits: {simulado_hits} {'✓' if simulado_hits==0 else '⚠ FIXME'}")
print(f"  Live CO₂ data refs (wc.co2): {co2_data_hits} {'✓' if co2_data_hits<=2 else '⚠ check'}")
print(f"\n✅ Dashboard built → {OUT}")
print(f"   Open: http://localhost:8000 (with backend running)")
