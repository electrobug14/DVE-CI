#!/usr/bin/env python3
"""
vcd_to_wavedrom.py — Converts VCD to WaveDrom JSON, then renders to SVG.

Pipeline:
  dump.vcd → wavedrom JSON → wavedrom CLI → waveform.svg

WaveDrom SVG looks professional and renders natively in GitHub Markdown
when committed to the repo (same as schematic.svg).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


# ── VCD Parser ───────────────────────────────────────────────

def parse_vcd(vcd_path: str):
    signals = {}   # id -> name
    values  = {}   # id -> [(time, value_str)]
    time    = 0

    with open(vcd_path) as f:
        content = f.read()

    # Variable declarations
    for m in re.finditer(
        r'\$var\s+\w+\s+(\d+)\s+(\S+)\s+(\S+)\s*(?:\[\S+\])?\s*\$end',
        content
    ):
        width, sig_id, name = m.group(1), m.group(2), m.group(3)
        signals[sig_id] = {"name": name, "width": int(width)}
        values[sig_id]  = []

    # Value changes
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            try:
                time = int(line[1:])
            except ValueError:
                pass
        elif line.startswith("b") or line.startswith("B"):
            parts = line.split()
            if len(parts) >= 2:
                val, sid = parts[0][1:], parts[1]
                if sid in values:
                    values[sid].append((time, val))
        elif len(line) >= 2 and line[0] in "01xzXZ":
            val, sid = line[0], line[1:]
            if sid in values:
                values[sid].append((time, val))

    return signals, values


# ── WaveDrom JSON Builder ────────────────────────────────────

def build_wavedrom(signals: dict, values: dict) -> dict:
    """
    Build a WaveDrom JSON object.
    For multi-bit signals, uses '=' (data) wave type with hex labels.
    For 1-bit signals, uses '0'/'1' wave type.
    """

    # Collect all timestamps
    all_times = sorted({t for evts in values.values() for t, _ in evts})
    if not all_times:
        all_times = [0]

    wave_signals = []

    for sid, info in signals.items():
        evts  = sorted(values.get(sid, []), key=lambda x: x[0])
        name  = info["name"]
        width = info["width"]

        if not evts:
            continue

        # Build a value at each timestamp
        # Fill forward (hold last value)
        time_val = {}
        last = "x"
        for t in all_times:
            # find most recent event at or before t
            for et, ev in reversed(evts):
                if et <= t:
                    last = ev
                    break
            time_val[t] = last

        if width == 1:
            # Binary wave: '0', '1', 'x'
            wave_str = ""
            data     = []
            prev     = None
            for t in all_times:
                v = time_val[t]
                c = {"0": "0", "1": "1"}.get(v, "x")
                if c == prev:
                    wave_str += "."
                else:
                    wave_str += c
                    prev = c
        else:
            # Data wave: '=' with label
            wave_str = ""
            data     = []
            prev_val = None
            for t in all_times:
                v = time_val[t]
                try:
                    label = str(int(v, 2))
                except ValueError:
                    label = "x"

                if v == prev_val:
                    wave_str += "."
                else:
                    wave_str += "="
                    data.append(label)
                    prev_val = v

        entry = {"name": name, "wave": wave_str}
        if data:
            entry["data"] = data

        wave_signals.append(entry)

    # Build time labels (in ns, divide ps by 1000)
    period = (all_times[1] - all_times[0]) if len(all_times) > 1 else 10000
    period_ns = period // 1000 if period >= 1000 else period

    wavedrom = {
        "signal": wave_signals,
        "config": {
            "hscale": max(1, min(4, len(all_times) // 4)),
            "skin":   "default"
        },
        "head": {
            "text": "Simulation Waveform",
            "tick": 0,
            "every": 1
        },
        "foot": {
            "text": f"1 tick = {period_ns} ns  |  HDL Ecosystem Pipeline",
            "tock": 0
        }
    }

    return wavedrom


# ── Render via WaveDrom CLI ──────────────────────────────────

def render_wavedrom(wd_json: dict, output_svg: str) -> bool:
    """
    Uses the wavedrom-cli npm package to render JSON → SVG.
    Install: npm install -g wavedrom-cli
    """
    json_path = Path(output_svg).with_suffix(".wavedrom.json")
    json_path.write_text(json.dumps(wd_json, indent=2))

    # Try wavedrom-cli first, then npx wavedrom-cli
    for cmd in [
        ["wavedrom-cli", "-i", str(json_path), "-s", output_svg],
        ["npx", "--yes", "wavedrom-cli", "-i", str(json_path), "-s", output_svg],
    ]:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0 and Path(output_svg).exists():
                print(f"✅ WaveDrom SVG saved: {output_svg}")
                json_path.unlink(missing_ok=True)
                return True
            else:
                print(f"⚠ {cmd[0]} failed: {result.stderr[:200]}", file=sys.stderr)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    print("❌ wavedrom-cli not available.", file=sys.stderr)
    json_path.unlink(missing_ok=True)
    return False


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcd",    default="dump.vcd")
    parser.add_argument("--output", default="waveform.svg")
    args = parser.parse_args()

    if not Path(args.vcd).exists():
        print(f"❌ VCD not found: {args.vcd}", file=sys.stderr)
        sys.exit(1)

    signals, values = parse_vcd(args.vcd)
    wd_json = build_wavedrom(signals, values)
    ok = render_wavedrom(wd_json, args.output)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
