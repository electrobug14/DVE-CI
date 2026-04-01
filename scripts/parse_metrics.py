#!/usr/bin/env python3
"""
parse_metrics.py — Extracts hardware metrics from Yosys synthesis output.

Outputs a structured JSON with:
  - Cell counts (AND, OR, NOT, DFF, MUX, etc.)
  - Estimated transistor count
  - Logic density estimate
  - Wire count
  - Port count
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── Transistor equivalents per cell type (rough CMOS estimates) ──
TRANSISTOR_MAP = {
    # 2-input gates
    "$_AND_":   6,
    "$_NAND_":  4,
    "$_OR_":    6,
    "$_NOR_":   4,
    "$_XOR_":   12,
    "$_XNOR_":  12,
    # Inverter
    "$_NOT_":   2,
    # Buffer
    "$_BUF_":   2,
    # Flip-Flops (D-type)
    "$_DFF_P_": 20,
    "$_DFF_N_": 20,
    "$_DFFE_PP_": 24,
    # Mux
    "$_MUX_":   12,
    "$_NMUX_":  10,
    # Latch
    "$_DLATCH_P_": 12,
    # Generic fallback
    "default":  6,
}


def parse_yosys_log(log_text: str) -> dict:
    """Parse the Yosys stdout log for cell stats."""
    cells = {}
    wires = 0
    ports = 0

    in_stat = False
    for line in log_text.splitlines():
        line = line.strip()

        if "=== design hierarchy ===" in line or "Number of cells:" in line:
            in_stat = True

        if in_stat:
            # Wire count
            m = re.match(r"Number of wires:\s+(\d+)", line)
            if m:
                wires = int(m.group(1))

            # Port count
            m = re.match(r"Number of ports:\s+(\d+)", line)
            if m:
                ports = int(m.group(1))

            # Cell counts — e.g.   $_AND_                     3
            m = re.match(r"(\$\w+)\s+(\d+)", line)
            if m:
                cells[m.group(1)] = int(m.group(2))

    return {"cells": cells, "wires": wires, "ports": ports}


def parse_stat_json(json_path: Path) -> dict:
    """Parse the Yosys JSON stat output if available."""
    try:
        with open(json_path) as f:
            return json.load(f)
    except Exception:
        return {}


def compute_transistors(cells: dict) -> int:
    total = 0
    for cell, count in cells.items():
        tx = TRANSISTOR_MAP.get(cell, TRANSISTOR_MAP["default"])
        total += tx * count
    return total


def compute_logic_density(cells: dict, transistors: int) -> dict:
    """
    Returns logic density metrics.
    We use a 7nm CMOS node reference: ~100M transistors / mm²
    (purely educational estimate — not a real layout).
    """
    TRANSISTORS_PER_MM2 = 100_000_000  # 7nm node reference

    area_mm2 = transistors / TRANSISTORS_PER_MM2 if transistors > 0 else 0
    area_um2 = area_mm2 * 1_000_000

    total_cells = sum(cells.values())

    return {
        "estimated_area_mm2":      round(area_mm2, 8),
        "estimated_area_um2":      round(area_um2, 4),
        "estimated_transistors":   transistors,
        "total_cells":             total_cells,
        "reference_node":          "7nm CMOS (educational estimate)",
        "transistor_density_note": "Actual silicon area depends on PDK & place-and-route",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yosys-log",  default="yosys_log.txt")
    parser.add_argument("--stat-json",  default="synth_stats.json")
    parser.add_argument("--output",     default="hardware_metrics.json")
    args = parser.parse_args()

    # ── Read Yosys log ───────────────────────────────────────
    log_text = ""
    if Path(args.yosys_log).exists():
        log_text = Path(args.yosys_log).read_text()
    else:
        print(f"⚠ Yosys log not found: {args.yosys_log}", file=sys.stderr)

    parsed = parse_yosys_log(log_text)
    cells  = parsed["cells"]
    wires  = parsed["wires"]
    ports  = parsed["ports"]

    # ── Transistor & density estimates ──────────────────────
    transistors = compute_transistors(cells)
    density     = compute_logic_density(cells, transistors)

    # ── Cell-type breakdown ──────────────────────────────────
    cell_breakdown = []
    for ctype, count in sorted(cells.items(), key=lambda x: -x[1]):
        tx_each = TRANSISTOR_MAP.get(ctype, TRANSISTOR_MAP["default"])
        cell_breakdown.append({
            "cell_type":          ctype,
            "count":              count,
            "transistors_each":   tx_each,
            "transistors_total":  tx_each * count,
        })

    # ── Final output ─────────────────────────────────────────
    output = {
        "summary": density,
        "wire_count":  wires,
        "port_count":  ports,
        "cell_breakdown": cell_breakdown,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Hardware metrics written to: {args.output}")
    print(f"   Cells: {density['total_cells']}  |  "
          f"Transistors (est.): {transistors}  |  "
          f"Area (est.): {density['estimated_area_um2']} µm²")


if __name__ == "__main__":
    main()
