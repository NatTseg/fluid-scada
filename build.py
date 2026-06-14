#!/usr/bin/env python3
"""
Build FluidSCADA Ignition Perspective project.
Layout guide: flex-first, grow/shrink/basis on every flex child, component.onActionPerformed nav.
Coord is kept ONLY for the process flow P&ID (overlapping fixed-geometry content).
"""
import json, os, shutil, subprocess

SRC  = os.path.dirname(os.path.abspath(__file__))
DEST = "/usr/local/ignition/data/projects/fluid-scada"

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#070D1A"
SURF    = "#0D1B2E"
SURF2   = "#112240"
BORDER  = "#1E3D5C"
BLUE    = "#2D7DD2"
BLUE_LT = "#60A5FA"
GREEN   = "#10B981"
RED     = "#EF4444"
YELLOW  = "#F59E0B"
PURPLE  = "#8B5CF6"
CYAN    = "#06B6D4"
TEXT    = "#E2E8F0"
MUTED   = "#64748B"
MUTED2  = "#94A3B8"
PIPE    = "#1E3D5C"
PIPE_ON = "#2D7DD2"

F  = "'Inter', 'Barlow', 'Helvetica Neue', Arial, sans-serif"
FM = "'JetBrains Mono', 'Courier New', monospace"

# ── Core layout helpers ───────────────────────────────────────────────────────
def _pos(grow=None, shrink=None, basis=None):
    d = {}
    if grow   is not None: d["grow"]   = grow
    if shrink is not None: d["shrink"] = shrink
    if basis  is not None:
        d["basis"] = basis
    elif grow is not None or shrink is not None:
        d["basis"] = "auto"
    return d

def flex(children, direction="column", justify="flex-start", align="stretch",
         grow=None, shrink=None, basis=None, gap=None, pad=None,
         bg=None, border=None, radius=None, wrap=None, name="flex",
         overflow=None, min_height=None, **kw_style):
    style = {}
    if gap:        style["gap"]             = gap
    if pad:        style["padding"]         = pad
    if bg:         style["backgroundColor"] = bg
    if border:     style["border"]          = border
    if radius:     style["borderRadius"]    = radius
    if overflow:   style["overflow"]        = overflow
    if min_height: style["minHeight"]       = min_height
    style.update(kw_style)
    props = {"direction": direction, "justify": justify,
             "alignItems": align, "style": style}
    if wrap: props["wrap"] = wrap
    comp = {"type": "ia.container.flex", "meta": {"name": name},
            "props": props, "children": children}
    pos = _pos(grow, shrink, basis)
    if pos: comp["position"] = pos
    return comp

def lbl(text, sz="0.875rem", col=TEXT, bold=False, track="normal", upper=False,
        align="left", font=F, grow=None, shrink=None, basis=None, name="lbl",
        **kw_style):
    style = {"color": col, "fontSize": sz, "fontFamily": font,
             "textAlign": align, "letterSpacing": track}
    if bold:  style["fontWeight"]    = "700"
    if upper: style["textTransform"] = "uppercase"
    style.update(kw_style)
    comp = {"type": "ia.display.label", "meta": {"name": name},
            "props": {"text": text, "style": style}}
    pos = _pos(grow, shrink, basis)
    if pos: comp["position"] = pos
    return comp

def btn(text, page=None, bg="transparent", col=BLUE_LT,
        border=f"1px solid {BORDER}", sz="0.6875rem", radius="6px",
        track="normal", grow=0, shrink=0, basis="auto", name="btn", pad="0.375rem 0.875rem"):
    style = {"backgroundColor": bg, "color": col, "fontSize": sz,
             "fontFamily": F, "letterSpacing": track,
             "border": border, "borderRadius": radius,
             "cursor": "pointer", "padding": pad}
    comp = {"type": "ia.input.button", "meta": {"name": name},
            "props": {"text": text, "style": style},
            "position": _pos(grow, shrink, basis)}
    if page:
        comp["events"] = {"component": {"onActionPerformed": {
            "type": "script", "scope": "G",
            "config": {"script": f"system.perspective.navigate(page='{page}')"}
        }}}
    return comp

def spacer():
    return lbl("", grow=1, shrink=1, basis="0%")

# ── Coord helper (P&ID only) ──────────────────────────────────────────────────
def coord(children, w, h, name="coord", **kw_style):
    style = {"width": f"{w}px", "height": f"{h}px", "flexShrink": "0"}
    style.update(kw_style)
    return {"type": "ia.container.coord", "meta": {"name": name},
            "props": {"style": style}, "children": children}

def cp(x, y, w, h):
    return {"x": x, "y": y, "width": w, "height": h}

# ── resource.json + write helpers ─────────────────────────────────────────────
def resource(files):
    return {"scope": "G", "version": 1, "restricted": False, "overridable": True,
            "files": files,
            "attributes": {"lastModification": {
                "actor": "admin", "timestamp": "2026-06-14T00:00:00Z"}}}

def write(rel, obj):
    full = os.path.join(SRC, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def view_json(root_comp, width=1440, height=900):
    return {"custom": {}, "params": {},
            "props": {"defaultSize": {"width": width, "height": height}},
            "root": root_comp}

def write_view(name, root_comp, width=1440, height=900):
    base = f"com.inductiveautomation.perspective/views/{name}"
    write(f"{base}/view.json",     view_json(root_comp, width, height))
    write(f"{base}/resource.json", resource(["view.json"]))
    print(f"  {name}")

# ── Process data (static mock) ────────────────────────────────────────────────
TANKS = {
    "T-101": {"name": "FEED TANK",     "level": 72.5, "temp": 22.3, "pres": 1.2, "fill": BLUE_LT, "x": 60},
    "T-102": {"name": "MIX TANK",      "level": 45.8, "temp": 38.5, "pres": 1.8, "fill": PURPLE,  "x": 545},
    "T-103": {"name": "PRODUCT TANK",  "level": 85.2, "temp": 23.1, "pres": 1.1, "fill": GREEN,   "x": 1050},
    "T-104": {"name": "CHEM ADDITIVE", "level": 31.4, "temp": 18.0, "pres": 0.8, "fill": YELLOW,  "x": 545},
}

# ── P&ID component builders (coord children) ──────────────────────────────────
def tank_coord(tag, data, y=50):
    lv = data["level"]; c = data["fill"]; x = data["x"]
    fill_h = int(180 * lv / 100); empty_h = 180 - fill_h
    def cl(text, style, pos): return {"type": "ia.display.label",
        "meta": {"name": f"lbl_{tag}_{text[:4]}"},
        "props": {"text": text, "style": style}, "position": pos}
    return [
        cl(tag, {"fontSize":"10px","fontWeight":"700","color":MUTED2,"letterSpacing":"1px","textAlign":"center"}, cp(x, y-20, 90, 18)),
        cl(data["name"], {"fontSize":"9px","color":MUTED,"textAlign":"center"}, cp(x, y-4, 90, 14)),
        cl("", {"backgroundColor":SURF,"border":f"2px solid {BORDER}","borderRadius":"4px 4px 0 0"}, cp(x, y, 90, 180)),
        cl("", {"backgroundColor":c,"opacity":"0.25"}, cp(x+2, y+empty_h, 86, fill_h-2)),
        cl("", {"backgroundColor":c,"height":"3px"}, cp(x+2, y+empty_h, 86, 3)),
        cl(f"{lv}%", {"fontSize":"14px","fontWeight":"700","color":c,"textAlign":"center"}, cp(x, y+max(4, empty_h//2-10), 90, 20)),
        cl(f"⚡ {data['temp']}°C  ⧉ {data['pres']} bar",
           {"fontSize":"9px","color":MUTED2,"textAlign":"center","backgroundColor":SURF2,
            "border":f"1px solid {BORDER}","padding":"2px 0","borderRadius":"0 0 4px 4px"},
           cp(x, y+180, 90, 20)),
    ]

def pipe_h_c(x, y, w, active=True):
    return {"type": "ia.display.label", "meta": {"name": "ph"},
            "props": {"text": "", "style": {"backgroundColor": PIPE_ON if active else PIPE, "borderRadius":"2px"}},
            "position": cp(x, y, w, 12)}

def pipe_v_c(x, y, h, active=True):
    return {"type": "ia.display.label", "meta": {"name": "pv"},
            "props": {"text": "", "style": {"backgroundColor": PIPE_ON if active else PIPE, "borderRadius":"2px"}},
            "position": cp(x, y, 12, h)}

def valve_c(tag, x, y, pct, active=True):
    color = GREEN if pct >= 85 else (RED if pct <= 10 else YELLOW)
    state = "OPEN" if pct >= 85 else ("CLSD" if pct <= 10 else f"{int(pct)}%")
    def cl(text, style, pos): return {"type":"ia.display.label","meta":{"name":f"v{tag}"},
        "props":{"text":text,"style":style},"position":pos}
    return [
        cl(tag, {"fontSize":"8px","color":MUTED2,"textAlign":"center"}, cp(x-10, y-14, 56, 12)),
        {"type":"ia.input.button","meta":{"name":f"b{tag}"},"props":{"text":state,
          "style":{"backgroundColor":SURF2,"border":f"2px solid {color}","color":color,
                   "fontSize":"9px","fontWeight":"700","borderRadius":"4px","cursor":"pointer"}},
         "position": cp(x, y, 36, 28)},
        cl(f"{pct}%", {"fontSize":"8px","color":MUTED,"textAlign":"center"}, cp(x, y+30, 36, 12)),
    ]

def pump_c(tag, x, y, running=True, rpm=1450):
    c = GREEN if running else RED; s = "RUN" if running else "STP"
    def cl(text, style, pos): return {"type":"ia.display.label","meta":{"name":f"p{tag}"},
        "props":{"text":text,"style":style},"position":pos}
    return [
        cl(tag, {"fontSize":"8px","color":MUTED2,"textAlign":"center"}, cp(x-6, y-14, 64, 12)),
        cl(f"◎ {s}", {"backgroundColor":SURF2,"border":f"2px solid {c}","color":c,
            "fontSize":"10px","fontWeight":"700","borderRadius":"50%","textAlign":"center",
            "display":"flex","alignItems":"center","justifyContent":"center"},
           cp(x, y, 52, 52)),
        cl(f"{rpm} RPM", {"fontSize":"8px","color":MUTED,"textAlign":"center"}, cp(x-6, y+54, 64, 12)),
    ]

def flow_meter_c(tag, x, y, flow, units="L/min"):
    def cl(text, style, pos): return {"type":"ia.display.label","meta":{"name":f"fi{tag}"},
        "props":{"text":text,"style":style},"position":pos}
    return [
        cl(tag, {"fontSize":"8px","color":MUTED2,"textAlign":"center"}, cp(x, y, 72, 12)),
        cl(f"{flow} {units}", {"fontSize":"10px","color":CYAN,"fontWeight":"700",
           "backgroundColor":SURF2,"border":f"1px solid {BORDER}","borderRadius":"4px",
           "textAlign":"center","padding":"2px 4px"}, cp(x, y+13, 72, 20)),
    ]

def build_pid():
    """Build the P&ID coord container. Coord is valid here: overlapping fixed geometry."""
    PIPE_Y = 248; kids = []
    # Tanks
    kids += tank_coord("T-101", TANKS["T-101"])
    kids += tank_coord("T-102", TANKS["T-102"])
    kids += tank_coord("T-103", TANKS["T-103"])
    kids += tank_coord("T-104", TANKS["T-104"], y=360)
    # Horizontal main pipe
    kids.append(pipe_h_c(105, PIPE_Y, 950))
    # Vertical drop pipes
    kids.append(pipe_v_c(99, 230, PIPE_Y - 230 + 12))
    kids.append(pipe_v_c(584, 230, PIPE_Y - 230 + 12))
    kids.append(pipe_v_c(1089, 230, PIPE_Y - 230 + 12))
    # Chemical feed
    kids.append(pipe_v_c(587, PIPE_Y+12, 360-PIPE_Y-12, active=False))
    kids += valve_c("FV-105", 572, 296, 100)
    # Valves
    kids += valve_c("FV-101", 148, PIPE_Y-8, 100)
    kids += valve_c("FV-102", 446, PIPE_Y-8, 100)
    kids += valve_c("FV-103", 650, PIPE_Y-8, 65)
    kids += valve_c("FV-104", 888, PIPE_Y-8, 100)
    # Pumps
    kids += pump_c("P-101", 278, PIPE_Y-20, rpm=1450)
    kids += pump_c("P-102", 756, PIPE_Y-20, rpm=1480)
    # Flow meters
    kids += flow_meter_c("FI-101", 360, PIPE_Y-34, 125.3)
    kids += flow_meter_c("FI-102", 960, PIPE_Y-34, 118.7)
    # Pressure labels
    for text, x in [("1.2 bar", 200), ("1.8 bar", 700)]:
        kids.append({"type":"ia.display.label","meta":{"name":"pbar"},
            "props":{"text":text,"style":{"fontSize":"9px","color":CYAN,"textAlign":"center"}},
            "position": cp(x, PIPE_Y+14, 60, 12)})
    return coord(kids, 1190, 520, name="PID")

# ── Shared KPI tile ───────────────────────────────────────────────────────────
def kpi_tile(title, value, unit, col, sub=""):
    return flex([
        lbl(title, sz="0.625rem", col=MUTED2, bold=True, track="1.5px", upper=True,
            grow=0, shrink=0),
        flex([
            lbl(value, sz="1.75rem", col=col, bold=True, grow=0, shrink=0),
            lbl(unit,  sz="0.8125rem", col=MUTED2, grow=0, shrink=0),
        ], direction="row", align="baseline", gap="0.375rem", grow=0, shrink=0),
        lbl(sub, sz="0.6875rem", col=MUTED, grow=0, shrink=0),
    ], direction="column", gap="0.25rem",
       grow=1, shrink=1, basis="0%",
       bg=SURF, pad="1rem 1.25rem",
       border=f"1px solid {BORDER}", radius="12px")

# ═══════════════════════════════════════════════════════════════════════════════
#  NAV
# ═══════════════════════════════════════════════════════════════════════════════
def build_nav():
    PAGES = [("/","Overview"),("/tanks","Tanks"),("/trends","Trends"),("/alarms","Alarms")]
    nav_btns = [btn(label, page=page,
                    bg="transparent", border="none", col=TEXT, sz="0.8125rem",
                    radius="8px", grow=0, shrink=0, name=f"nav{label}")
                for page, label in PAGES]
    root = flex([
        flex([
            lbl("⧉", sz="1.375rem", col=BLUE, bold=True, grow=0, shrink=0),
            lbl("FLUIDSCADA", sz="0.9375rem", col=TEXT, bold=True, track="2px",
                grow=0, shrink=0),
            lbl("| PROCESS CONTROL", sz="0.6875rem", col=MUTED, track="1px",
                grow=0, shrink=0),
        ], direction="row", align="center", gap="0.625rem",
           grow=0, shrink=0),
        flex(nav_btns, direction="row", align="center", gap="0.25rem",
             grow=0, shrink=0),
        spacer(),
        lbl("●", sz="0.625rem", col=GREEN, grow=0, shrink=0),
        lbl("All Systems Online", sz="0.75rem", col=MUTED2, grow=0, shrink=0),
    ], direction="row", align="center", gap="0.75rem",
       bg=SURF, pad="0 1.5rem",
       borderBottom=f"1px solid {BORDER}",
       min_height="56px", name="NavRoot")
    write_view("Components/Nav", root, height=56)

# ═══════════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def build_overview():
    kpi_strip = flex([
        kpi_tile("TOTAL FLOW RATE", "244.0", "L/min", BLUE_LT, "Combined FI-101 + FI-102"),
        kpi_tile("MIX TANK LEVEL",  "45.8",  "%",     PURPLE,  "T-102 · 38.5 °C"),
        kpi_tile("ACTIVE ALARMS",   "2",     "",      YELLOW,  "1 High · 1 Warning"),
        kpi_tile("PRODUCT TANK",    "85.2",  "%",     GREEN,   "T-103 · Ready"),
    ], direction="row", gap="1rem", grow=0, shrink=0)

    def alarm_row(sev, tag, msg, ts, col):
        return flex([
            lbl(sev, sz="0.5625rem", col=BG if col != MUTED2 else SURF,
                bold=True, pad="2px 8px", name="sev",
                backgroundColor=col, borderRadius="4px",
                grow=0, shrink=0),
            lbl(tag, sz="0.75rem", col=col, bold=True,
                grow=0, shrink=0, minWidth="80px"),
            lbl(msg, sz="0.75rem", col=MUTED2, grow=1, shrink=1, basis="0%"),
            lbl(ts,  sz="0.6875rem", col=MUTED, grow=0, shrink=0),
            btn("ACK", col=BLUE_LT, border=f"1px solid {BLUE}", grow=0, shrink=0),
        ], direction="row", align="center", gap="0.75rem",
           grow=0, shrink=0, bg=SURF, pad="0.625rem 1rem",
           border=f"1px solid {BORDER}", radius="8px")

    alarm_block = flex([
        flex([
            lbl("ACTIVE ALARMS", sz="0.625rem", col=MUTED2, bold=True, track="1.5px",
                upper=True, grow=0, shrink=0),
            spacer(),
            btn("View All →", page="/alarms", bg="transparent", border="none",
                col=BLUE_LT, sz="0.6875rem", grow=0, shrink=0),
        ], direction="row", align="center", grow=0, shrink=0),
        alarm_row("HIGH", "T-102", "Mix tank temperature exceeds 40 °C setpoint", "14:31", YELLOW),
        alarm_row("WARN", "P-101", "Pump P-101 current draw above nominal 18 A",  "14:28", MUTED2),
    ], direction="column", gap="0.5rem", grow=0, shrink=0)

    pid_card = flex([
        flex([
            lbl("PROCESS FLOW DIAGRAM", sz="0.625rem", col=MUTED2, bold=True, track="2px",
                upper=True, grow=0, shrink=0),
            spacer(),
            lbl("Live  ·  Auto-refresh 5s", sz="0.625rem", col=MUTED, grow=0, shrink=0),
        ], direction="row", align="center", grow=0, shrink=0),
        build_pid(),
    ], direction="column", gap="0.75rem",
       grow=0, shrink=0, bg=SURF, pad="1.25rem",
       border=f"1px solid {BORDER}", radius="16px",
       overflow="auto")

    root = flex([
        {"type":"ia.display.view","meta":{"name":"Nav"},
         "props":{"path":"Components/Nav"},"position":_pos(0,0,"56px")},
        flex([
            flex([
                flex([
                    lbl("PROCESS OVERVIEW", sz="1.375rem", col=TEXT, bold=True,
                        grow=0, shrink=0),
                    lbl("Fluid Processing Unit  ·  Jun 14, 2026  ·  00:00 UTC",
                        sz="0.75rem", col=MUTED, grow=0, shrink=0),
                ], direction="column", gap="2px", grow=1, shrink=1, basis="0%"),
                lbl("● Online · Auto", sz="0.75rem", col=GREEN,
                    backgroundColor="rgba(16,185,129,0.08)",
                    border="1px solid rgba(16,185,129,0.25)",
                    borderRadius="20px", padding="4px 14px",
                    grow=0, shrink=0),
            ], direction="row", align="center", grow=0, shrink=0),
            kpi_strip,
            pid_card,
            alarm_block,
        ], direction="column", gap="1.25rem",
           grow=1, shrink=1, basis="0%",
           pad="1.5rem 1.75rem", overflow="auto"),
    ], direction="column", bg=BG, name="OverviewRoot")

    write_view("Overview", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  TANKS
# ═══════════════════════════════════════════════════════════════════════════════
def build_tanks():
    def tank_card(tag, data):
        lv = data["level"]; fc = data["fill"]
        fill_h = int(280 * lv / 100)
        return flex([
            flex([
                flex([
                    lbl(tag, sz="1.375rem", col=TEXT, bold=True, grow=0, shrink=0),
                    lbl(data["name"], sz="0.75rem", col=MUTED, grow=0, shrink=0),
                ], direction="column", gap="2px", grow=1, shrink=1, basis="0%"),
                lbl("ONLINE", sz="0.625rem", col=BG, bold=True,
                    backgroundColor=GREEN, borderRadius="20px", padding="3px 12px",
                    grow=0, shrink=0),
            ], direction="row", align="center", grow=0, shrink=0),
            # Tank visual
            flex([
                flex([lbl(f"{lv}%", sz="2rem", col=fc, bold=True, align="center",
                          grow=0, shrink=0)],
                     direction="column", justify="center", align="center",
                     grow=1, shrink=1, basis="0%"),
                lbl("", grow=0, shrink=0, basis=f"{fill_h}px",
                    backgroundColor=fc, opacity="0.25"),
            ], direction="column", align="stretch",
               grow=0, shrink=0, basis="280px",
               border=f"2px solid {BORDER}", radius="8px",
               bg=SURF2, overflow="hidden"),
            # Sensors
            flex([
                flex([
                    lbl("TEMPERATURE", sz="0.5rem", col=MUTED2, bold=True, track="1px",
                        upper=True, align="center", grow=0, shrink=0),
                    lbl(f"{data['temp']} °C", sz="1.25rem", col=YELLOW, bold=True,
                        align="center", grow=0, shrink=0),
                ], direction="column", gap="0.25rem", align="center",
                   grow=1, shrink=1, basis="0%",
                   bg=SURF2, pad="0.75rem",
                   border=f"1px solid {BORDER}", radius="10px"),
                flex([
                    lbl("PRESSURE", sz="0.5rem", col=MUTED2, bold=True, track="1px",
                        upper=True, align="center", grow=0, shrink=0),
                    lbl(f"{data['pres']} bar", sz="1.25rem", col=CYAN, bold=True,
                        align="center", grow=0, shrink=0),
                ], direction="column", gap="0.25rem", align="center",
                   grow=1, shrink=1, basis="0%",
                   bg=SURF2, pad="0.75rem",
                   border=f"1px solid {BORDER}", radius="10px"),
                flex([
                    lbl("LEVEL", sz="0.5rem", col=MUTED2, bold=True, track="1px",
                        upper=True, align="center", grow=0, shrink=0),
                    lbl(f"{lv} %", sz="1.25rem", col=fc, bold=True,
                        align="center", grow=0, shrink=0),
                ], direction="column", gap="0.25rem", align="center",
                   grow=1, shrink=1, basis="0%",
                   bg=SURF2, pad="0.75rem",
                   border=f"1px solid {BORDER}", radius="10px"),
            ], direction="row", gap="0.75rem", grow=0, shrink=0),
        ], direction="column", gap="0.875rem",
           grow=1, shrink=1, basis="0%",
           bg=SURF, pad="1.25rem",
           border=f"1px solid {BORDER}", radius="16px")

    root = flex([
        {"type":"ia.display.view","meta":{"name":"Nav"},
         "props":{"path":"Components/Nav"},"position":_pos(0,0,"56px")},
        flex([
            flex([
                lbl("TANK STATUS", sz="1.375rem", col=TEXT, bold=True,
                    grow=0, shrink=0),
                lbl("Level, Temperature & Pressure · Live",
                    sz="0.75rem", col=MUTED, grow=0, shrink=0),
            ], direction="column", gap="2px", grow=0, shrink=0),
            flex([tank_card(t, d) for t, d in TANKS.items()],
                 direction="row", gap="1rem", wrap="wrap", grow=0, shrink=0),
        ], direction="column", gap="1.25rem",
           grow=1, shrink=1, basis="0%",
           pad="1.5rem 1.75rem", overflow="auto"),
    ], direction="column", bg=BG, name="TanksRoot")

    write_view("Tanks", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  ALARMS
# ═══════════════════════════════════════════════════════════════════════════════
def build_alarms():
    ALARMS = [
        ("HIGH",    "T-102-TEMP",  "Mix tank temperature exceeds 40 °C setpoint",  "Jun 14 · 14:31", YELLOW),
        ("WARNING", "P-101-CURR",  "Pump P-101 current draw above nominal 18 A",   "Jun 14 · 14:28", MUTED2),
        ("HIGH",    "T-101-LEVLO", "Feed tank level below 20% — refill required",  "Jun 14 · 13:55", RED),
        ("INFO",    "FV-103-POS",  "Valve FV-103 position drift detected (65%)",   "Jun 14 · 13:40", BLUE_LT),
        ("INFO",    "FI-101-FLOW", "Flow rate FI-101 reduced 8% below setpoint",   "Jun 14 · 13:22", BLUE_LT),
    ]

    def alarm_row(sev, tag, msg, ts, col):
        return flex([
            lbl(sev, sz="0.5625rem", col=BG if col not in (MUTED2, BLUE_LT) else SURF,
                bold=True, align="center",
                backgroundColor=col, borderRadius="4px", padding="3px 10px",
                minWidth="64px", grow=0, shrink=0),
            lbl(tag, sz="0.75rem", col=col, bold=True,
                fontFamily=FM, minWidth="110px", grow=0, shrink=0),
            lbl(msg, sz="0.75rem", col=MUTED2, grow=1, shrink=1, basis="0%"),
            lbl(ts,  sz="0.6875rem", col=MUTED,
                minWidth="110px", textAlign="right", grow=0, shrink=0),
            btn("ACK", col=BLUE_LT, border=f"1px solid {BLUE}",
                radius="4px", grow=0, shrink=0),
        ], direction="row", align="center", gap="0.875rem",
           grow=0, shrink=0, bg=SURF, pad="0.75rem 1rem",
           border=f"1px solid {BORDER}", radius="10px")

    root = flex([
        {"type":"ia.display.view","meta":{"name":"Nav"},
         "props":{"path":"Components/Nav"},"position":_pos(0,0,"56px")},
        flex([
            flex([
                flex([
                    lbl("ALARM MANAGEMENT", sz="1.375rem", col=TEXT, bold=True,
                        grow=0, shrink=0),
                    lbl("Active alarms require acknowledgement",
                        sz="0.75rem", col=MUTED, grow=0, shrink=0),
                ], direction="column", gap="2px", grow=1, shrink=1, basis="0%"),
                flex([
                    lbl("2 HIGH",    sz="0.6875rem", col=TEXT, bold=True,
                        backgroundColor=RED, borderRadius="20px", padding="4px 14px",
                        grow=0, shrink=0),
                    lbl("1 WARNING", sz="0.6875rem", col=BG,  bold=True,
                        backgroundColor=YELLOW, borderRadius="20px", padding="4px 14px",
                        grow=0, shrink=0),
                    lbl("2 INFO",    sz="0.6875rem", col=MUTED2, bold=True,
                        backgroundColor=SURF2, border=f"1px solid {BORDER}",
                        borderRadius="20px", padding="4px 14px",
                        grow=0, shrink=0),
                ], direction="row", gap="0.5rem", grow=0, shrink=0),
            ], direction="row", align="center", grow=0, shrink=0),
            flex([alarm_row(*a) for a in ALARMS],
                 direction="column", gap="0.5rem", grow=0, shrink=0),
        ], direction="column", gap="1.25rem",
           grow=1, shrink=1, basis="0%",
           pad="1.5rem 1.75rem", overflow="auto"),
    ], direction="column", bg=BG, name="AlarmsRoot")

    write_view("Alarms", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
def build_trends():
    def sparkline(tag, value, unit, col, points, note=""):
        max_v = max(points)
        bars = [{"type":"ia.display.label","meta":{"name":"bar"},
                 "props":{"text":"","style":{"backgroundColor":col,"opacity":"0.7",
                     "borderRadius":"2px 2px 0 0","width":"10px"}},
                 "position":{"basis":f"{int(64*v/max_v)}px","shrink":0,"alignSelf":"flex-end"}}
                for v in points]
        return flex([
            flex([
                flex([
                    lbl(tag, sz="0.625rem", col=MUTED2, bold=True, track="1.5px",
                        upper=True, grow=0, shrink=0),
                    flex([
                        lbl(str(value), sz="1.75rem", col=col, bold=True, grow=0, shrink=0),
                        lbl(unit, sz="0.8125rem", col=MUTED2, grow=0, shrink=0),
                    ], direction="row", align="baseline", gap="0.25rem", grow=0, shrink=0),
                    lbl(note, sz="0.6875rem", col=MUTED, grow=0, shrink=0),
                ], direction="column", gap="2px", grow=1, shrink=1, basis="0%"),
                lbl("24h", sz="0.625rem", col=MUTED2,
                    backgroundColor=SURF2, border=f"1px solid {BORDER}",
                    borderRadius="6px", padding="3px 10px",
                    grow=0, shrink=0),
            ], direction="row", align="flex-start", grow=0, shrink=0),
            flex(bars, direction="row", align="flex-end", gap="3px",
                 grow=0, shrink=0, basis="64px",
                 borderTop=f"1px solid {BORDER}", paddingTop="8px"),
        ], direction="column", gap="0.75rem",
           grow=1, shrink=1, basis="0%",
           bg=SURF, pad="1.125rem 1.25rem",
           border=f"1px solid {BORDER}", radius="14px")

    CHARTS = [
        ("T-101 LEVEL", 72.5, "%",     BLUE_LT, [65,68,70,72,71,74,73,72,75,72], "Feed Tank"),
        ("T-102 LEVEL", 45.8, "%",     PURPLE,  [50,48,46,45,44,46,47,45,46,46], "Mix Tank"),
        ("T-103 LEVEL", 85.2, "%",     GREEN,   [78,80,82,83,84,85,86,85,85,85], "Product Tank"),
        ("T-102 TEMP",  38.5, "°C",    YELLOW,  [34,35,36,37,37,38,38,38,39,39], "Mix Tank"),
        ("FI-101 FLOW", 125.3,"L/min", CYAN,    [120,122,124,125,126,125,125,124,125,125], "Line 1"),
        ("FI-102 FLOW", 118.7,"L/min", BLUE,    [115,116,118,117,119,118,119,118,119,119], "Line 2"),
    ]
    time_btns = [btn(t, bg=BLUE if t=="24H" else SURF2,
                     col=TEXT if t=="24H" else BLUE_LT,
                     border=f"1px solid {BLUE if t=='24H' else BORDER}",
                     radius="6px", sz="0.6875rem", grow=0, shrink=0)
                 for t in ["1H","6H","24H","7D"]]

    root = flex([
        {"type":"ia.display.view","meta":{"name":"Nav"},
         "props":{"path":"Components/Nav"},"position":_pos(0,0,"56px")},
        flex([
            flex([
                flex([
                    lbl("PROCESS TRENDS", sz="1.375rem", col=TEXT, bold=True,
                        grow=0, shrink=0),
                    lbl("24-hour historical overview · All process variables",
                        sz="0.75rem", col=MUTED, grow=0, shrink=0),
                ], direction="column", gap="2px", grow=1, shrink=1, basis="0%"),
                flex(time_btns, direction="row", gap="0.5rem", grow=0, shrink=0),
            ], direction="row", align="center", grow=0, shrink=0),
            flex([sparkline(*c) for c in CHARTS],
                 direction="row", gap="1rem", wrap="wrap", grow=0, shrink=0),
        ], direction="column", gap="1.25rem",
           grow=1, shrink=1, basis="0%",
           pad="1.5rem 1.75rem", overflow="auto"),
    ], direction="column", bg=BG, name="TrendsRoot")

    write_view("Trends", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECT FILES
# ═══════════════════════════════════════════════════════════════════════════════
def write_project():
    write("project.json", {
        "title": "FluidSCADA",
        "description": "Fluid Process SCADA — tanks, pumps, valves, flow control",
        "parent": "", "enabled": True, "inheritable": False
    })
    pc_path = "com.inductiveautomation.perspective/page-config"
    write(f"{pc_path}/config.json", {
        "pages": {
            "/":       {"title": "FluidSCADA — Overview", "viewPath": "Overview"},
            "/tanks":  {"title": "Tank Status",           "viewPath": "Tanks"},
            "/trends": {"title": "Trends",                "viewPath": "Trends"},
            "/alarms": {"title": "Alarms",                "viewPath": "Alarms"},
        },
        "sharedDocks": {"cornerPriority": "top-bottom",
                        "bottom": [], "left": [], "right": []}
    })
    write(f"{pc_path}/resource.json", resource(["config.json"]))
    print("  project.json + page-config")

# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD + DEPLOY
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Building FluidSCADA (flex layout, component.onActionPerformed nav)...")
    write_project()
    build_nav()
    build_overview()
    build_tanks()
    build_alarms()
    build_trends()

    print(f"\nDeploying → {DEST}")
    if os.path.exists(DEST):
        shutil.rmtree(DEST)
    subprocess.run([
        "rsync", "-a",
        "--exclude=.git", "--exclude=tags", "--exclude=*.py",
        f"{SRC}/", f"{DEST}/"
    ], check=True)
    subprocess.run(["find", DEST, "-name", "*.json", "-exec", "touch", "{}", ";"])
    print("Done.")
