#!/usr/bin/env python3
"""Fix remaining red/seed/CO2 issues in the built dashboard."""
import re, os

PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "static", "index.html")
PATH = os.path.abspath(PATH)

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)

# 1. counterfactual scenario color entries
content = content.replace('"color":"#E24B4A"', '"color":"#C25A1A"')

# 2. terminal hi.util red
content = content.replace(
    'color:#E24B4A">\'+hi.util+\'%</span>',
    'color:#C25A1A">\'+hi.util+\'%</span>'
)

# 3. tline init seed=2026 in HTML body
content = content.replace(
    '>iniciando PlantaOS · 1137 lugares · 8 clusters · seed=2026<',
    '>PlantaOS · 1137 lugares · 8 clusters · a ligar ao backend…<'
)
# Also JS string version
content = content.replace(
    '"iniciando PlantaOS · 1137 lugares · 8 clusters · seed=2026"',
    '"PlantaOS · 1137 lugares · 8 clusters · a ligar ao backend…"'
)

# 4. terminal co2_max snip — find it and replace entirely
# Pattern: function(){var co2h=STATES... return 'co2_max → ...
co2max_start = content.find("function(){var co2h=STATES")
if co2max_start != -1:
    # Find the matching closing '}' for the return statement
    end = content.find("}'", co2max_start)
    if end != -1:
        end += 2
        replacement = "function(){var hi=STATES.reduce(function(a,b){return a.util>b.util?a:b},STATES[0]);return'util_max \\u2192 <span style=\\'color:#C25A1A\\'>'+hi.id+' = '+hi.util+'%</span>  <span style=\\'color:var(--t3)\\'>fila:'+hi.q+'</span>'}"
        content = content[:co2max_start] + replacement + content[end:]
        print("  ✓ co2_max snip replaced with util_max")
    else:
        print("  ⚠ could not find end of co2_max snip")
else:
    print("  ⚠ co2_max snip not found")

# 5. CO2 badge in WC list items (left panel in twin view)
# Pattern: +'<span style="font-size:.48rem;color:'+(wc.co2>...'>CO₂ '+wc.co2+'</span>'+
co2_badge = content.find("+'<span style=\"font-size:.48rem;color:'+(wc.co2>800?\"var(--red)\":\"var(--t3)\")+';margin-left:auto'>CO₂ '+wc.co2+'</span>'")
if co2_badge != -1:
    # Find end of this expression (usually followed by newline + +)
    end_badge = co2_badge + 300
    # Find the actual end
    line_end = content.find("\n", co2_badge)
    content = content[:co2_badge] + "" + content[line_end:]
    print("  ✓ CO₂ badge removed from WC list items")
else:
    print("  ⚠ CO₂ badge in list not found (may already be gone)")

# 6. CO2 in WC card mini display
# +'<span style="color:'+(wc.co2>800?...'">CO₂:'+wc.co2+'</span>'
# +'<span style="color:#3B82F6">'+(wc.water_L_hr||0)+'L/h</span>'
co2_card = content.find("'>CO₂:'+wc.co2+'</span>'")
if co2_card != -1:
    # Find start of this expression
    start_co2 = content.rfind("+'<span style=\"color:'+(wc.co2", 0, co2_card)
    if start_co2 != -1:
        end_co2 = co2_card + len("'>CO₂:'+wc.co2+'</span>'")
        # Also grab the water_L_hr span if it follows
        water_span = content.find("+'<span style=\"color:#3B82F6\">'+(wc.water_L_hr||0)+'L/h</span>'", end_co2)
        if water_span != -1 and water_span < end_co2 + 200:
            end_co2 = water_span + len("+'<span style=\"color:#3B82F6\">'+(wc.water_L_hr||0)+'L/h</span>'")
        replacement = "+'<span style=\"color:var(--t3)\">conf:'+(wc.confianca||'—')+'%</span>'"
        content = content[:start_co2] + replacement + content[end_co2:]
        print("  ✓ CO₂/water card badge replaced with confidence")
    else:
        print("  ⚠ could not find start of CO₂ card span")
else:
    print("  ⚠ CO₂ card badge not found")

# 7. ventilação forçada CO2 in counterfactual
content = content.replace(
    '{k:"Ventilação forçada",v:"CO₂ "+wc.co2+"→"+Math.round(wc.co2*0.62)+"ppm",bad:false},',
    '{k:"Ventilação forçada",v:"recomendada",bad:false},'
)
print("  ✓ Ventilation CO₂ fixed in counterfactual")

# 8. Any remaining wc.co2>800 patterns in live display (not the disabled one)
# The one already disabled with false&& is fine; neutralize any others
remaining_co2 = [(m.start(), content[max(0,m.start()-60):m.start()+100]) for m in re.finditer(r'wc\.co2', content) if 'false&&' not in content[max(0,m.start()-20):m.start()]]
print(f"  Remaining active wc.co2 refs: {len(remaining_co2)}")
for pos, ctx in remaining_co2:
    print(f"    pos {pos}: {repr(ctx[:80])}")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

# Final verification
red_hits = [m.group() for m in re.finditer(r'#E24B4A|#e24b4a|#c0392b', content)]
seed_hits = re.findall(r'seed=2026', content)
simulado_hits = [m.group(0) for m in re.finditer(r'\bSIMULADO\b', content)]

print(f"\n── Final verification ────────────────")
print(f"  Red color hits: {len(red_hits)} {'✓' if not red_hits else '⚠ ' + str(red_hits[:3])}")
print(f"  seed=2026 hits: {len(seed_hits)} {'✓' if not seed_hits else '⚠'}")
print(f"  SIMULADO text: {len(simulado_hits)} {'✓' if not simulado_hits else '⚠ ' + str(simulado_hits[:3])}")
print(f"  File size: {len(content)/1024:.1f} KB")
print(f"\nDone ✓")
