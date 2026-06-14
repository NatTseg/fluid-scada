#!/usr/bin/env python3
"""Generate FluidSCADA tags JSON and import into Ignition via REST API."""
import json, os, urllib.request, urllib.error, base64

BASE = os.path.dirname(__file__)

# ── Tag tree ─────────────────────────────────────────────────────────────────
def mem(name, dtype, value, engUnit="", hi_hi=None, hi=None, lo=None, lo_lo=None):
    t = {
        "name": name,
        "tagType": "AtomicTag",
        "dataType": dtype,
        "value": value,
        "valueSource": "memory",
    }
    if engUnit:
        t["engUnit"] = engUnit
    alarms = []
    if hi_hi is not None:
        alarms.append({"name": "HiHi", "mode": "AboveValue", "setpointA": hi_hi, "priority": "Critical"})
    if hi is not None:
        alarms.append({"name": "Hi",   "mode": "AboveValue", "setpointA": hi,    "priority": "High"})
    if lo is not None:
        alarms.append({"name": "Lo",   "mode": "BelowValue", "setpointA": lo,    "priority": "High"})
    if lo_lo is not None:
        alarms.append({"name": "LoLo", "mode": "BelowValue", "setpointA": lo_lo, "priority": "Critical"})
    if alarms:
        t["alarms"] = alarms
    return t

def folder(name, *children):
    return {"name": name, "tagType": "Folder", "tags": list(children)}

tags_export = {
    "name": "",
    "tagType": "Folder",
    "tags": [
        folder("FluidProcess",
            folder("Tanks",
                folder("T101",
                    mem("Level",       "Float8", 72.5, "%",    hi_hi=95, hi=85, lo=20, lo_lo=10),
                    mem("Temperature", "Float8", 22.3, "°C",   hi_hi=50, hi=40),
                    mem("Pressure",    "Float8",  1.2, "bar",  hi_hi=5.0, hi=4.0, lo=0.5),
                    mem("Volume",      "Float8", 18.1, "m³"),
                    mem("FillRate",    "Float8",  2.4, "m³/h"),
                ),
                folder("T102",
                    mem("Level",           "Float8", 45.8, "%",    hi_hi=95, hi=85, lo=15, lo_lo=5),
                    mem("Temperature",     "Float8", 38.5, "°C",   hi_hi=55, hi=42, lo=25),
                    mem("Pressure",        "Float8",  1.8, "bar",  hi_hi=5.0, hi=4.0),
                    mem("AgitatorSpeed",   "Float8", 120.0,"RPM",  lo=50),
                    mem("AgitatorRunning", "Boolean", True),
                    mem("Volume",          "Float8", 11.5, "m³"),
                ),
                folder("T103",
                    mem("Level",       "Float8", 85.2, "%",    hi_hi=98, hi=90, lo=10, lo_lo=5),
                    mem("Temperature", "Float8", 23.1, "°C",   hi_hi=50, hi=40),
                    mem("Pressure",    "Float8",  1.1, "bar",  hi_hi=5.0, hi=4.0),
                    mem("Volume",      "Float8", 21.3, "m³"),
                    mem("ProductQuality", "Float8", 98.2, "%", lo=95),
                ),
                folder("T104",
                    mem("Level",       "Float8", 31.4, "%",    hi_hi=90, hi=80, lo=10, lo_lo=5),
                    mem("Temperature", "Float8", 18.0, "°C"),
                    mem("Pressure",    "Float8",  0.8, "bar"),
                    mem("Volume",      "Float8",  2.2, "m³"),
                    mem("ChemConc",    "Float8", 35.0, "%"),
                ),
            ),
            folder("Pumps",
                folder("P101",
                    mem("Running",    "Boolean", True),
                    mem("Speed",      "Float8", 1450.0, "RPM",  hi=1800, lo=500),
                    mem("Current",    "Float8",   15.2, "A",    hi_hi=22, hi=18),
                    mem("Power",      "Float8",    7.4, "kW"),
                    mem("Status",     "Int4",        1),   # 0=stop 1=run 2=fault
                    mem("Runtime",    "Float8",  2847.0, "h"),
                    mem("Command",    "Boolean", True),
                ),
                folder("P102",
                    mem("Running",    "Boolean", True),
                    mem("Speed",      "Float8", 1480.0, "RPM",  hi=1800, lo=500),
                    mem("Current",    "Float8",   14.8, "A",    hi_hi=22, hi=18),
                    mem("Power",      "Float8",    7.1, "kW"),
                    mem("Status",     "Int4",        1),
                    mem("Runtime",    "Float8",  1923.0, "h"),
                    mem("Command",    "Boolean", True),
                ),
            ),
            folder("Valves",
                folder("FV101",
                    mem("Position", "Float8", 100.0, "%"),
                    mem("Command",  "Boolean", True),
                    mem("Feedback", "Float8", 100.0, "%"),
                    mem("Status",   "Int4",       1),
                ),
                folder("FV102",
                    mem("Position", "Float8", 100.0, "%"),
                    mem("Command",  "Boolean", True),
                    mem("Feedback", "Float8", 100.0, "%"),
                    mem("Status",   "Int4",       1),
                ),
                folder("FV103",
                    mem("Position", "Float8",  65.0, "%"),
                    mem("Command",  "Boolean", True),
                    mem("Feedback", "Float8",  64.5, "%"),
                    mem("Status",   "Int4",       1),
                ),
                folder("FV104",
                    mem("Position", "Float8", 100.0, "%"),
                    mem("Command",  "Boolean", True),
                    mem("Feedback", "Float8", 100.0, "%"),
                    mem("Status",   "Int4",       1),
                ),
                folder("FV105",
                    mem("Position", "Float8", 100.0, "%"),
                    mem("Command",  "Boolean", True),
                    mem("Feedback", "Float8", 100.0, "%"),
                    mem("Status",   "Int4",       1),
                ),
            ),
            folder("FlowMeters",
                folder("FI101",
                    mem("Flow",        "Float8", 125.3, "L/min", hi_hi=200, hi=160, lo=20),
                    mem("Totalizer",   "Float8", 84203.5, "L"),
                    mem("Temperature", "Float8",   22.5, "°C"),
                ),
                folder("FI102",
                    mem("Flow",        "Float8", 118.7, "L/min", hi_hi=200, hi=160, lo=20),
                    mem("Totalizer",   "Float8", 71482.0, "L"),
                    mem("Temperature", "Float8",   22.1, "°C"),
                ),
            ),
            folder("System",
                mem("TotalFlowRate",   "Float8", 244.0,  "L/min"),
                mem("ProcessRunning",  "Boolean", True),
                mem("ActiveAlarms",    "Int4",       2),
                mem("ShiftProduction", "Float8",  8.42,  "m³"),
                mem("DailyProduction", "Float8", 31.75,  "m³"),
            ),
        )
    ]
}

# ── Write JSON ─────────────────────────────────────────────────────────────────
tags_path = os.path.join(BASE, "tags", "FluidProcess.json")
os.makedirs(os.path.dirname(tags_path), exist_ok=True)
with open(tags_path, "w") as f:
    json.dump(tags_export, f, indent=2)
print(f"Tags JSON written → {tags_path}")

# ── Import via Ignition REST API ───────────────────────────────────────────────
GW = "http://localhost:8088"
USER = "admin"
PASS = "password"

def import_tags():
    url = f"{GW}/data/tag/json/import?provider=default&baseTagPath=&importType=OVERWRITE"
    payload = json.dumps(tags_export).encode()
    creds = base64.b64encode(f"{USER}:{PASS}".encode()).decode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Basic {creds}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            print(f"Import response {resp.status}: {body[:200]}")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as ex:
        print(f"Error: {ex}")

print("Importing tags into Ignition...")
import_tags()
print("Done.")
