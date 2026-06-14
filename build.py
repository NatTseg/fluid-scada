#!/usr/bin/env python3
"""Generate all Ignition Perspective JSON views for FluidSCADA."""
import json, os

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#070D1A"
SURF     = "#0D1B2E"
SURF2    = "#112240"
BORDER   = "#1E3D5C"
BLUE     = "#2D7DD2"
BLUE_LT  = "#60A5FA"
GREEN    = "#10B981"
RED      = "#EF4444"
YELLOW   = "#F59E0B"
PURPLE   = "#8B5CF6"
CYAN     = "#06B6D4"
TEXT     = "#E2E8F0"
MUTED    = "#64748B"
MUTED2   = "#94A3B8"
PIPE     = "#1E3D5C"
PIPE_ACT = "#2D7DD2"

# ── Component helpers ─────────────────────────────────────────────────────────
def lbl(text, style=None, meta=None, **kw):
    p = {"text": text}
    if style: p["style"] = style
    c = {"type": "ia.display.label", "props": p}
    if meta: c["meta"] = meta
    return {**c, **kw}

def btn(text, style=None, on_click=None, meta=None, **kw):
    p = {"text": text}
    if style: p["style"] = style
    if on_click:
        p["events"] = {"dom": {"onClick": {"type": "script", "scope": "G", "config": {"script": on_click}}}}
    c = {"type": "ia.input.button", "props": p}
    if meta: c["meta"] = meta
    return {**c, **kw}

def flex(direction="column", style=None, children=None, meta=None, position=None, **kw):
    p = {"direction": direction}
    if style: p["style"] = style
    c = {"type": "ia.container.flex", "props": p}
    if children: c["children"] = children
    if meta: c["meta"] = meta
    if position: c["position"] = position
    return {**c, **kw}

def coord(style=None, children=None, meta=None, position=None, **kw):
    p = {}
    if style: p["style"] = style
    c = {"type": "ia.container.coord", "props": p}
    if children: c["children"] = children
    if meta: c["meta"] = meta
    if position: c["position"] = position
    return {**c, **kw}

def view_embed(path, meta=None, position=None, **kw):
    c = {"type": "ia.display.view", "props": {"path": path}}
    if meta: c["meta"] = meta
    if position: c["position"] = position
    return {**c, **kw}

def p(x, y, w, h):
    """Coord-container absolute position."""
    return {"x": x, "y": y, "width": w, "height": h}

def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  wrote {path}")

BASE = os.path.dirname(__file__)
VIEWS = os.path.join(BASE, "com.inductiveautomation.perspective", "views")

# ── Process data (static mock) ────────────────────────────────────────────────
TANKS = {
    "T-101": {"name": "FEED TANK",     "level": 72.5, "temp": 22.3, "pres": 1.2, "x": 60,   "fill": BLUE_LT},
    "T-102": {"name": "MIX TANK",      "level": 45.8, "temp": 38.5, "pres": 1.8, "x": 545,  "fill": PURPLE},
    "T-103": {"name": "PRODUCT TANK",  "level": 85.2, "temp": 23.1, "pres": 1.1, "x": 1050, "fill": GREEN},
    "T-104": {"name": "CHEM ADDITIVE", "level": 31.4, "temp": 18.0, "pres": 0.8, "x": 545,  "fill": YELLOW},
}

# ── Helpers for process components ────────────────────────────────────────────
def tank_card(tag, data, is_chem=False):
    """Returns a coord child: tank body with fill level."""
    lv = data["level"]
    fill_h = int(180 * lv / 100)
    empty_h = 180 - fill_h
    color = data["fill"]
    x = data["x"]
    y = 50 if not is_chem else 360
    w, h = 90, 180

    children = [
        # Tag label above tank
        lbl(tag, {"fontSize": "10px", "fontWeight": "700", "color": MUTED2,
                  "letterSpacing": "1px", "textAlign": "center"},
            position=p(x, y - 20, w, 18)),
        # Tank name
        lbl(data["name"], {"fontSize": "9px", "color": MUTED, "textAlign": "center"},
            position=p(x, y - 4, w, 14)),
        # Tank body border
        lbl("", {"backgroundColor": SURF, "border": f"2px solid {BORDER}",
                 "borderRadius": "4px 4px 0 0"},
            position=p(x, y, w, h)),
        # Fill level (colored bar at bottom of tank)
        lbl("", {"backgroundColor": color, "opacity": "0.25"},
            position=p(x + 2, y + empty_h, w - 4, fill_h - 2)),
        # Fill level bright stripe at top of fill
        lbl("", {"backgroundColor": color, "height": "3px"},
            position=p(x + 2, y + empty_h, w - 4, 3)),
        # Level % text (centered vertically in empty space)
        lbl(f"{lv}%", {"fontSize": "14px", "fontWeight": "700", "color": color,
                        "textAlign": "center"},
            position=p(x, y + max(4, empty_h // 2 - 10), w, 20)),
        # Bottom sensors strip
        lbl(f"⚡ {data['temp']}°C  ⧉ {data['pres']} bar",
            {"fontSize": "9px", "color": MUTED2, "textAlign": "center",
             "backgroundColor": SURF2, "border": f"1px solid {BORDER}",
             "padding": "2px 0", "borderRadius": "0 0 4px 4px"},
            position=p(x, y + h, w, 20)),
    ]
    return children

def pipe_h(x, y, w, active=True):
    """Horizontal pipe segment."""
    return lbl("", {"backgroundColor": PIPE_ACT if active else PIPE,
                    "borderRadius": "2px"},
               position=p(x, y, w, 12))

def pipe_v(x, y, h, active=True):
    """Vertical pipe segment."""
    return lbl("", {"backgroundColor": PIPE_ACT if active else PIPE,
                    "borderRadius": "2px"},
               position=p(x, y, 12, h))

def valve(tag, x, y, pos_pct, active=True):
    """Valve button (36×36). Color = open/closed/partial."""
    if pos_pct >= 85:
        color, state = GREEN, "OPEN"
    elif pos_pct <= 10:
        color, state = RED, "CLSD"
    else:
        color, state = YELLOW, f"{int(pos_pct)}%"
    script = f"\tsystem.perspective.print('{tag} toggled')"
    children = [
        lbl(tag, {"fontSize": "8px", "color": MUTED2, "textAlign": "center"},
            position=p(x - 10, y - 14, 56, 12)),
        btn(state,
            {"backgroundColor": SURF2, "border": f"2px solid {color}",
             "color": color, "fontSize": "9px", "fontWeight": "700",
             "borderRadius": "4px", "cursor": "pointer"},
            on_click=script,
            position=p(x, y, 36, 28)),
        lbl(f"{pos_pct}%", {"fontSize": "8px", "color": MUTED, "textAlign": "center"},
            position=p(x, y + 30, 36, 12)),
    ]
    return children

def pump(tag, x, y, running=True, rpm=1450):
    """Pump circle (52×52)."""
    color = GREEN if running else RED
    status = "RUN" if running else "STP"
    children = [
        lbl(tag, {"fontSize": "8px", "color": MUTED2, "textAlign": "center"},
            position=p(x - 6, y - 14, 64, 12)),
        lbl(f"◎ {status}",
            {"backgroundColor": SURF2, "border": f"2px solid {color}",
             "color": color, "fontSize": "10px", "fontWeight": "700",
             "borderRadius": "50%", "textAlign": "center",
             "display": "flex", "alignItems": "center", "justifyContent": "center"},
            position=p(x, y, 52, 52)),
        lbl(f"{rpm} RPM", {"fontSize": "8px", "color": MUTED, "textAlign": "center"},
            position=p(x - 6, y + 54, 64, 12)),
    ]
    return children

def flow_meter(tag, x, y, flow, units="L/min"):
    """Flow indicator badge."""
    children = [
        lbl(tag, {"fontSize": "8px", "color": MUTED2, "textAlign": "center"},
            position=p(x, y, 72, 12)),
        lbl(f"{flow} {units}",
            {"fontSize": "10px", "color": CYAN, "fontWeight": "700",
             "backgroundColor": SURF2, "border": f"1px solid {BORDER}",
             "borderRadius": "4px", "textAlign": "center", "padding": "2px 4px"},
            position=p(x, y + 13, 72, 20)),
    ]
    return children

# ── KPI tile ─────────────────────────────────────────────────────────────────
def kpi_tile(title, value, unit, color, sub=""):
    return flex("column", {
        "backgroundColor": SURF, "border": f"1px solid {BORDER}",
        "borderRadius": "12px", "padding": "16px 20px", "gap": "4px",
    }, [
        lbl(title, {"fontSize": "10px", "fontWeight": "700", "color": MUTED2,
                    "letterSpacing": "1.5px"}),
        flex("row", {"alignItems": "baseline", "gap": "4px"}, [
            lbl(value, {"fontSize": "28px", "fontWeight": "700", "color": color}),
            lbl(unit,  {"fontSize": "13px", "color": MUTED2}),
        ]),
        lbl(sub, {"fontSize": "11px", "color": MUTED}),
    ], position={"grow": 1})

# ═══════════════════════════════════════════════════════════════════════════════
# NAV
# ═══════════════════════════════════════════════════════════════════════════════
def build_nav():
    pages = [
        ("/", "Overview"),
        ("/tanks", "Tanks"),
        ("/trends", "Trends"),
        ("/alarms", "Alarms"),
    ]
    tabs = []
    for path, name in pages:
        is_active_expr = f"{{page.props.path}} == '{path}'"
        tabs.append(btn(
            name,
            {
                "color": TEXT, "fontSize": "13px", "fontWeight": "600",
                "padding": "6px 16px", "borderRadius": "8px",
                "backgroundColor": "transparent", "border": "none", "cursor": "pointer",
            },
            on_click=f"\tsystem.perspective.navigate('{path}')",
        ))

    return {
        "custom": {}, "params": {}, "props": {},
        "root": flex("row", {
            "backgroundColor": SURF, "borderBottom": f"1px solid {BORDER}",
            "padding": "0 24px", "alignItems": "center", "height": "56px",
            "justifyContent": "space-between",
        }, [
            flex("row", {"alignItems": "center", "gap": "10px"}, [
                lbl("⧉", {"fontSize": "22px", "color": BLUE, "fontWeight": "700"}),
                lbl("FLUIDSCADA", {"fontSize": "15px", "fontWeight": "800",
                                   "color": TEXT, "letterSpacing": "2px"}),
                lbl("| PROCESS CONTROL", {"fontSize": "11px", "color": MUTED,
                                          "letterSpacing": "1px"}),
            ]),
            flex("row", {"alignItems": "center", "gap": "4px"}, tabs),
            flex("row", {"alignItems": "center", "gap": "12px"}, [
                lbl("●", {"fontSize": "10px", "color": GREEN}),
                lbl("All Systems Online", {"fontSize": "12px", "color": MUTED2}),
            ]),
        ], meta={"name": "root"}),
    }

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def build_overview():
    # Pipe Y positions
    PIPE_Y = 248
    TANK_Y = 50

    # Build all coord children for the process diagram
    kids = []

    # ── Section header ───
    kids.append(lbl("PROCESS FLOW DIAGRAM",
        {"fontSize": "10px", "fontWeight": "700", "color": MUTED2,
         "letterSpacing": "2px"},
        position=p(0, 0, 300, 16)))
    kids.append(lbl("Live  ·  Auto-refresh 5s",
        {"fontSize": "10px", "color": MUTED},
        position=p(1050, 0, 140, 16)))

    # ── Tanks ─────────────────────────────────────────────────────────────────
    # T-101 Feed (x=60)
    kids += tank_card("T-101", TANKS["T-101"])
    # T-102 Mix (x=545)
    kids += tank_card("T-102", TANKS["T-102"])
    # T-103 Product (x=1050)
    kids += tank_card("T-103", TANKS["T-103"])
    # T-104 Chemical (below T-102, x=545)
    kids += tank_card("T-104", TANKS["T-104"], is_chem=True)

    # ── Main horizontal pipe ───────────────────────────────────────────────────
    kids.append(pipe_h(105, PIPE_Y, 950))  # T-101 outlet → T-103 inlet

    # ── Vertical drop pipes (tank bottom → main pipe) ─────────────────────────
    kids.append(pipe_v(99, 230, PIPE_Y - 230 + 12))    # T-101 → pipe
    kids.append(pipe_v(584, 230, PIPE_Y - 230 + 12))   # T-102 → pipe
    kids.append(pipe_v(1089, 230, PIPE_Y - 230 + 12))  # T-103 → pipe

    # ── Chemical feed: vertical T-104 top → main pipe, then down ─────────────
    # (T-104 top is at y=360, main pipe at y=248; pipe goes from 260 down to 360)
    kids.append(pipe_v(587, PIPE_Y + 12, 360 - PIPE_Y - 12, active=False))
    # FV-105 junction
    kids += valve("FV-105", 572, 296, 100)

    # ── Valves ────────────────────────────────────────────────────────────────
    kids += valve("FV-101", 148, PIPE_Y - 8, 100)   # T-101 outlet
    kids += valve("FV-102", 446, PIPE_Y - 8, 100)   # T-102 inlet
    kids += valve("FV-103", 650, PIPE_Y - 8, 65)    # T-102 outlet
    kids += valve("FV-104", 888, PIPE_Y - 8, 100)   # T-103 inlet

    # ── Pumps ─────────────────────────────────────────────────────────────────
    kids += pump("P-101", 278, PIPE_Y - 20, running=True, rpm=1450)
    kids += pump("P-102", 756, PIPE_Y - 20, running=True, rpm=1480)

    # ── Flow meters ──────────────────────────────────────────────────────────
    kids += flow_meter("FI-101", 360, PIPE_Y - 34, 125.3)
    kids += flow_meter("FI-102", 960, PIPE_Y - 34, 118.7)

    # ── Pipe segment labels ──────────────────────────────────────────────────
    kids.append(lbl("1.2 bar", {"fontSize": "9px", "color": CYAN, "textAlign": "center"},
                    position=p(200, PIPE_Y + 14, 60, 12)))
    kids.append(lbl("1.8 bar", {"fontSize": "9px", "color": CYAN, "textAlign": "center"},
                    position=p(700, PIPE_Y + 14, 60, 12)))

    process_diagram = coord(
        {"width": "1190px", "height": "520px", "flexShrink": "0"},
        kids,
        meta={"name": "ProcessDiagram"},
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    kpi_row = flex("row", {"gap": "16px", "alignItems": "stretch"}, [
        kpi_tile("TOTAL FLOW RATE",  "244.0", "L/min", BLUE_LT, "Combined FI-101 + FI-102"),
        kpi_tile("MIX TANK LEVEL",   "45.8",  "%",     PURPLE,  "T-102 · 38.5 °C"),
        kpi_tile("ACTIVE ALARMS",    "2",     "",      YELLOW,  "1 High · 1 Warning"),
        kpi_tile("PRODUCT TANK",     "85.2",  "%",     GREEN,   "T-103 · Ready"),
    ], meta={"name": "KPIRow"})

    # ── Alarm strip ───────────────────────────────────────────────────────────
    def alarm_row(sev, tag, msg, ts, color):
        return flex("row", {
            "alignItems": "center", "gap": "12px",
            "padding": "10px 16px",
            "backgroundColor": SURF, "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
        }, [
            lbl(sev, {"backgroundColor": color, "color": BG, "fontSize": "9px",
                      "fontWeight": "700", "padding": "2px 8px", "borderRadius": "4px"}),
            lbl(tag, {"fontSize": "12px", "fontWeight": "700", "color": color,
                      "minWidth": "80px"}),
            lbl(msg, {"fontSize": "12px", "color": MUTED2}, position={"grow": 1}),
            lbl(ts,  {"fontSize": "11px", "color": MUTED}),
            btn("ACK", {"fontSize": "10px", "fontWeight": "700", "color": BLUE_LT,
                        "backgroundColor": "transparent", "border": f"1px solid {BLUE}",
                        "borderRadius": "4px", "padding": "3px 10px", "cursor": "pointer"}),
        ])

    alarm_strip = flex("column", {"gap": "8px"}, [
        flex("row", {"alignItems": "center", "justifyContent": "space-between"}, [
            lbl("ACTIVE ALARMS", {"fontSize": "10px", "fontWeight": "700",
                                  "color": MUTED2, "letterSpacing": "1.5px"}),
            btn("View All →", {"fontSize": "11px", "color": BLUE_LT,
                                    "backgroundColor": "transparent", "border": "none",
                                    "cursor": "pointer"},
                on_click="\tsystem.perspective.navigate('/alarms')"),
        ]),
        alarm_row("HIGH", "T-102", "Mix tank temperature exceeds 40 °C setpoint", "14:31", YELLOW),
        alarm_row("WARN", "P-101", "Pump P-101 current draw above nominal 18 A", "14:28", MUTED2),
    ], meta={"name": "AlarmStrip"})

    root = flex("column", {
        "backgroundColor": BG, "minHeight": "100vh",
    }, [
        view_embed("Components/Nav", meta={"name": "Nav"},
                   position={"basis": "56px", "shrink": 0}),
        flex("column", {
            "padding": "24px 28px", "gap": "20px",
            "overflowY": "auto", "overflowX": "auto",
        }, [
            # Page header
            flex("row", {"alignItems": "center", "justifyContent": "space-between"}, [
                flex("column", {"gap": "2px"}, [
                    lbl("PROCESS OVERVIEW", {"fontSize": "22px", "fontWeight": "700",
                                             "color": TEXT, "letterSpacing": "0.5px"}),
                    lbl("Fluid Processing Unit  ·  Jun 13, 2026  ·  14:32 UTC",
                        {"fontSize": "12px", "color": MUTED}),
                ]),
                lbl("● Online · Auto", {"fontSize": "12px", "color": GREEN,
                                                   "backgroundColor": "rgba(16,185,129,0.1)",
                                                   "border": "1px solid rgba(16,185,129,0.3)",
                                                   "borderRadius": "20px", "padding": "4px 14px"}),
            ]),
            kpi_row,
            # Process diagram card
            flex("column", {
                "backgroundColor": SURF, "border": f"1px solid {BORDER}",
                "borderRadius": "16px", "padding": "20px", "gap": "12px",
                "overflowX": "auto",
            }, [process_diagram]),
            alarm_strip,
        ], position={"grow": 1}),
    ], meta={"name": "root"})

    return {"custom": {}, "params": {}, "props": {"defaultSize": {"width": 1440}}, "root": root}

# ═══════════════════════════════════════════════════════════════════════════════
# TANKS DETAIL
# ═══════════════════════════════════════════════════════════════════════════════
def build_tanks():
    def tank_detail(tag, data):
        lv = data["level"]
        fill_h = int(280 * lv / 100)
        empty_h = 280 - fill_h
        fill_color = data["fill"]
        return flex("column", {
            "backgroundColor": SURF, "border": f"1px solid {BORDER}",
            "borderRadius": "16px", "padding": "20px", "gap": "14px",
        }, [
            flex("row", {"alignItems": "center", "justifyContent": "space-between"}, [
                flex("column", {"gap": "2px"}, [
                    lbl(tag, {"fontSize": "22px", "fontWeight": "700", "color": TEXT}),
                    lbl(data["name"], {"fontSize": "12px", "color": MUTED}),
                ]),
                lbl("ONLINE", {"fontSize": "10px", "fontWeight": "700",
                               "backgroundColor": GREEN, "color": BG,
                               "borderRadius": "20px", "padding": "3px 12px"}),
            ]),
            # Tall tank visual
            flex("column", {
                "height": "280px", "border": f"2px solid {BORDER}",
                "borderRadius": "8px", "backgroundColor": SURF2,
                "overflow": "hidden",
            }, [
                # Empty portion
                flex("column", {"alignItems": "center", "justifyContent": "center"},
                     [lbl(f"{lv}%", {"fontSize": "32px", "fontWeight": "700",
                                     "color": fill_color})],
                     position={"grow": 1}),
                # Fill portion
                lbl("", {"backgroundColor": fill_color, "opacity": "0.25"},
                    position={"basis": f"{fill_h}px", "shrink": 0}),
            ]),
            # Sensor readings
            flex("row", {"gap": "12px"}, [
                flex("column", {
                    "backgroundColor": SURF2, "border": f"1px solid {BORDER}",
                    "borderRadius": "10px", "padding": "12px", "gap": "4px",
                    "alignItems": "center",
                }, [
                    lbl("TEMPERATURE", {"fontSize": "9px", "color": MUTED2,
                                        "letterSpacing": "1px", "fontWeight": "700"}),
                    lbl(f"{data['temp']} °C", {"fontSize": "20px", "fontWeight": "700",
                                                     "color": YELLOW}),
                ], position={"grow": 1}),
                flex("column", {
                    "backgroundColor": SURF2, "border": f"1px solid {BORDER}",
                    "borderRadius": "10px", "padding": "12px", "gap": "4px",
                    "alignItems": "center",
                }, [
                    lbl("PRESSURE", {"fontSize": "9px", "color": MUTED2,
                                     "letterSpacing": "1px", "fontWeight": "700"}),
                    lbl(f"{data['pres']} bar", {"fontSize": "20px", "fontWeight": "700",
                                                "color": CYAN}),
                ], position={"grow": 1}),
                flex("column", {
                    "backgroundColor": SURF2, "border": f"1px solid {BORDER}",
                    "borderRadius": "10px", "padding": "12px", "gap": "4px",
                    "alignItems": "center",
                }, [
                    lbl("LEVEL", {"fontSize": "9px", "color": MUTED2,
                                  "letterSpacing": "1px", "fontWeight": "700"}),
                    lbl(f"{lv} %", {"fontSize": "20px", "fontWeight": "700",
                                    "color": fill_color}),
                ], position={"grow": 1}),
            ]),
        ], position={"grow": 1})

    tank_grid = flex("row", {"gap": "16px", "flexWrap": "wrap"}, [
        tank_detail("T-101", TANKS["T-101"]),
        tank_detail("T-102", TANKS["T-102"]),
        tank_detail("T-103", TANKS["T-103"]),
        tank_detail("T-104", TANKS["T-104"]),
    ])

    root = flex("column", {"backgroundColor": BG, "minHeight": "100vh"}, [
        view_embed("Components/Nav", meta={"name": "Nav"},
                   position={"basis": "56px", "shrink": 0}),
        flex("column", {"padding": "24px 28px", "gap": "20px",
                        "overflowY": "auto"}, [
            flex("row", {"alignItems": "center", "justifyContent": "space-between"}, [
                flex("column", {"gap": "2px"}, [
                    lbl("TANK STATUS", {"fontSize": "22px", "fontWeight": "700",
                                        "color": TEXT}),
                    lbl("Level, Temperature & Pressure · Live",
                        {"fontSize": "12px", "color": MUTED}),
                ]),
            ]),
            tank_grid,
        ], position={"grow": 1}),
    ], meta={"name": "root"})

    return {"custom": {}, "params": {}, "props": {"defaultSize": {"width": 1440}}, "root": root}

# ═══════════════════════════════════════════════════════════════════════════════
# ALARMS
# ═══════════════════════════════════════════════════════════════════════════════
def build_alarms():
    ALARMS = [
        ("HIGH",    "T-102-TEMP",  "Mix tank temperature exceeds 40 °C setpoint",  "Jun 13 · 14:31", YELLOW),
        ("WARNING", "P-101-CURR",  "Pump P-101 current draw above nominal 18 A",         "Jun 13 · 14:28", MUTED2),
        ("HIGH",    "T-101-LEVLO", "Feed tank level below 20% — refill required",   "Jun 13 · 13:55", RED),
        ("INFO",    "FV-103-POS",  "Valve FV-103 position drift detected (set 65%)",     "Jun 13 · 13:40", BLUE_LT),
        ("INFO",    "FI-101-FLOW", "Flow rate FI-101 reduced 8% below setpoint",         "Jun 13 · 13:22", BLUE_LT),
    ]

    def alarm_row(sev, tag, msg, ts, color):
        return flex("row", {
            "alignItems": "center", "gap": "14px",
            "padding": "12px 16px",
            "backgroundColor": SURF, "border": f"1px solid {BORDER}",
            "borderRadius": "10px",
        }, [
            lbl(sev, {"backgroundColor": color, "color": BG if color != MUTED2 else SURF,
                      "fontSize": "9px", "fontWeight": "700",
                      "padding": "3px 10px", "borderRadius": "4px", "minWidth": "64px",
                      "textAlign": "center"}),
            lbl(tag, {"fontSize": "12px", "fontWeight": "700", "color": color,
                      "minWidth": "110px", "fontFamily": "monospace"}),
            lbl(msg, {"fontSize": "12px", "color": MUTED2}, position={"grow": 1}),
            lbl(ts,  {"fontSize": "11px", "color": MUTED, "minWidth": "110px",
                      "textAlign": "right"}),
            btn("ACK", {"fontSize": "10px", "fontWeight": "700", "color": BLUE_LT,
                        "backgroundColor": "transparent",
                        "border": f"1px solid {BLUE}", "borderRadius": "4px",
                        "padding": "4px 12px", "cursor": "pointer"}),
        ])

    root = flex("column", {"backgroundColor": BG, "minHeight": "100vh"}, [
        view_embed("Components/Nav", meta={"name": "Nav"},
                   position={"basis": "56px", "shrink": 0}),
        flex("column", {"padding": "24px 28px", "gap": "20px",
                        "overflowY": "auto"}, [
            flex("row", {"alignItems": "center", "justifyContent": "space-between"}, [
                flex("column", {"gap": "2px"}, [
                    lbl("ALARM MANAGEMENT", {"fontSize": "22px", "fontWeight": "700",
                                              "color": TEXT}),
                    lbl("Active alarms require acknowledgement",
                        {"fontSize": "12px", "color": MUTED}),
                ]),
                flex("row", {"gap": "8px"}, [
                    lbl("2 HIGH", {"fontSize": "11px", "fontWeight": "700",
                                   "backgroundColor": RED, "color": TEXT,
                                   "borderRadius": "20px", "padding": "4px 14px"}),
                    lbl("1 WARNING", {"fontSize": "11px", "fontWeight": "700",
                                      "backgroundColor": YELLOW, "color": BG,
                                      "borderRadius": "20px", "padding": "4px 14px"}),
                    lbl("2 INFO", {"fontSize": "11px", "fontWeight": "700",
                                   "backgroundColor": SURF2, "color": MUTED2,
                                   "border": f"1px solid {BORDER}",
                                   "borderRadius": "20px", "padding": "4px 14px"}),
                ]),
            ]),
            flex("column", {"gap": "8px"}, [alarm_row(*a) for a in ALARMS]),
        ], position={"grow": 1}),
    ], meta={"name": "root"})

    return {"custom": {}, "params": {}, "props": {"defaultSize": {"width": 1440}}, "root": root}

# ═══════════════════════════════════════════════════════════════════════════════
# TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
def build_trends():
    def sparkline_card(tag, value, unit, color, points, note=""):
        """Fake sparkline using flex bars."""
        bars = []
        max_v = max(points)
        for v in points:
            h = int(60 * v / max_v) if max_v > 0 else 0
            bars.append(lbl("", {
                "backgroundColor": color, "opacity": "0.7",
                "borderRadius": "2px 2px 0 0", "width": "10px",
            }, position={"basis": f"{h}px", "shrink": 0, "alignSelf": "flex-end"}))

        return flex("column", {
            "backgroundColor": SURF, "border": f"1px solid {BORDER}",
            "borderRadius": "14px", "padding": "18px 20px", "gap": "12px",
        }, [
            flex("row", {"justifyContent": "space-between", "alignItems": "flex-start"}, [
                flex("column", {"gap": "2px"}, [
                    lbl(tag, {"fontSize": "10px", "fontWeight": "700", "color": MUTED2,
                              "letterSpacing": "1.5px"}),
                    flex("row", {"alignItems": "baseline", "gap": "4px"}, [
                        lbl(str(value), {"fontSize": "28px", "fontWeight": "700", "color": color}),
                        lbl(unit, {"fontSize": "13px", "color": MUTED2}),
                    ]),
                    lbl(note, {"fontSize": "11px", "color": MUTED}),
                ]),
                lbl("24h", {"fontSize": "10px", "color": MUTED2,
                             "backgroundColor": SURF2,
                             "border": f"1px solid {BORDER}",
                             "borderRadius": "6px", "padding": "3px 10px"}),
            ]),
            flex("row", {
                "height": "64px", "alignItems": "flex-end", "gap": "3px",
                "borderTop": f"1px solid {BORDER}", "paddingTop": "8px",
            }, bars),
        ], position={"grow": 1})

    CHARTS = [
        ("T-101 LEVEL",  72.5, "%",     BLUE_LT, [65,68,70,72,71,74,73,72,75,72], "Feed Tank"),
        ("T-102 LEVEL",  45.8, "%",     PURPLE,  [50,48,46,45,44,46,47,45,46,46], "Mix Tank"),
        ("T-103 LEVEL",  85.2, "%",     GREEN,   [78,80,82,83,84,85,86,85,85,85], "Product Tank"),
        ("T-102 TEMP",   38.5, "°C", YELLOW, [34,35,36,37,37,38,38,38,39,39], "Mix Tank"),
        ("FI-101 FLOW",  125.3,"L/min", CYAN,    [120,122,124,125,126,125,125,124,125,125], "Line 1"),
        ("FI-102 FLOW",  118.7,"L/min", BLUE,    [115,116,118,117,119,118,119,118,119,119], "Line 2"),
    ]

    chart_grid = flex("row", {"gap": "16px", "flexWrap": "wrap"}, [
        sparkline_card(*c) for c in CHARTS
    ])

    root = flex("column", {"backgroundColor": BG, "minHeight": "100vh"}, [
        view_embed("Components/Nav", meta={"name": "Nav"},
                   position={"basis": "56px", "shrink": 0}),
        flex("column", {"padding": "24px 28px", "gap": "20px",
                        "overflowY": "auto"}, [
            flex("row", {"alignItems": "center", "justifyContent": "space-between"}, [
                flex("column", {"gap": "2px"}, [
                    lbl("PROCESS TRENDS", {"fontSize": "22px", "fontWeight": "700",
                                           "color": TEXT}),
                    lbl("24-hour historical overview · All process variables",
                        {"fontSize": "12px", "color": MUTED}),
                ]),
                flex("row", {"gap": "8px"}, [
                    btn("1H",  {"fontSize": "11px", "color": BLUE_LT, "backgroundColor": SURF2,
                                "border": f"1px solid {BORDER}", "borderRadius": "6px",
                                "padding": "4px 14px", "cursor": "pointer"}),
                    btn("6H",  {"fontSize": "11px", "color": BLUE_LT, "backgroundColor": SURF2,
                                "border": f"1px solid {BORDER}", "borderRadius": "6px",
                                "padding": "4px 14px", "cursor": "pointer"}),
                    btn("24H", {"fontSize": "11px", "color": TEXT, "backgroundColor": BLUE,
                                "border": f"1px solid {BLUE}", "borderRadius": "6px",
                                "padding": "4px 14px", "cursor": "pointer"}),
                    btn("7D",  {"fontSize": "11px", "color": BLUE_LT, "backgroundColor": SURF2,
                                "border": f"1px solid {BORDER}", "borderRadius": "6px",
                                "padding": "4px 14px", "cursor": "pointer"}),
                ]),
            ]),
            chart_grid,
        ], position={"grow": 1}),
    ], meta={"name": "root"})

    return {"custom": {}, "params": {}, "props": {"defaultSize": {"width": 1440}}, "root": root}

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & PROJECT
# ═══════════════════════════════════════════════════════════════════════════════
def build_page_config():
    return {
        "paths": {
            "/":        {"view": "Overview"},
            "/tanks":   {"view": "Tanks"},
            "/trends":  {"view": "Trends"},
            "/alarms":  {"view": "Alarms"},
        },
        "defaultPath": "/"
    }

def build_project():
    return {
        "title": "FluidSCADA",
        "description": "Fluid Process SCADA — tanks, pumps, valves, flow control",
        "parent": "global",
        "enabled": True,
        "inheritable": False
    }

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Building FluidSCADA views...")

    write(os.path.join(BASE, "project.json"), build_project())
    write(os.path.join(BASE, "com.inductiveautomation.perspective",
                       "page-config", "config.json"), build_page_config())
    write(os.path.join(VIEWS, "Components", "Nav", "view.json"), build_nav())
    write(os.path.join(VIEWS, "Overview",   "view.json"), build_overview())
    write(os.path.join(VIEWS, "Tanks",      "view.json"), build_tanks())
    write(os.path.join(VIEWS, "Alarms",     "view.json"), build_alarms())
    write(os.path.join(VIEWS, "Trends",     "view.json"), build_trends())

    print("Done.")
