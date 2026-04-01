#!/usr/bin/env python3
"""
estimate_timing.py — Estimates critical path timing from Yosys output.

Uses gate delay models (educational, not process-accurate).
For real timing, OpenSTA with a Liberty file should be used.
"""

import argparse
import re
from pathlib import Path


# ── Typical gate delays (ns) — generic 7nm CMOS rough estimates ──
GATE_DELAY_NS = {
    "$_AND_":   0.05,
    "$_NAND_":  0.04,
    "$_OR_":    0.05,
    "$_NOR_":   0.04,
    "$_XOR_":   0.09,
    "$_XNOR_":  0.09,
    "$_NOT_":   0.02,
    "$_BUF_":   0.02,
    "$_MUX_":   0.07,
    "$_DFF_P_": 0.10,   # Clk-to-Q delay
    "$_DFF_N_": 0.10,
    "default":  0.05,
}

SETUP_TIME_NS   = 0.03   # DFF setup time
HOLD_TIME_NS    = 0.01   # DFF hold time


def parse_cells_from_log(log_path: Path) -> dict:
    """Re-parse Yosys log for cell counts."""
    cells = {}
    if not log_path.exists():
        return cells
    for line in log_path.read_text().splitlines():
        line = line.strip()
        m = re.match(r"(\$\w+)\s+(\d+)", line)
        if m:
            cells[m.group(1)] = int(m.group(2))
    return cells


def estimate_critical_path(cells: dict) -> dict:
    """
    Very rough critical path estimate:
    Assumes worst case = DFF → (all combinational cells in series) → DFF
    Real tools do graph traversal on the actual netlist.
    """
    combo_delay = sum(
        GATE_DELAY_NS.get(c, GATE_DELAY_NS["default"]) * cnt
        for c, cnt in cells.items()
        if "DFF" not in c and "DLATCH" not in c
    )

    dff_delay = GATE_DELAY_NS["$_DFF_P_"]
    critical_path_ns = dff_delay + combo_delay + SETUP_TIME_NS

    max_freq_mhz = (1.0 / critical_path_ns) * 1000 if critical_path_ns > 0 else float("inf")

    return {
        "combinational_delay_ns": round(combo_delay, 4),
        "dff_clk_to_q_ns":        round(dff_delay, 4),
        "setup_time_ns":          round(SETUP_TIME_NS, 4),
        "hold_time_ns":           round(HOLD_TIME_NS, 4),
        "critical_path_ns":       round(critical_path_ns, 4),
        "max_frequency_mhz":      round(max_freq_mhz, 2),
        "note": (
            "Educational estimate using generic 7nm gate delays. "
            "For accurate timing, use OpenSTA with a process-specific Liberty (.lib) file."
        ),
    }


def format_report(cells: dict, timing: dict) -> str:
    lines = [
        "╔══════════════════════════════════════════════╗",
        "║       Timing Analysis Report (Estimated)     ║",
        "╚══════════════════════════════════════════════╝",
        "",
        "⚙ Reference Node  : Generic 7nm CMOS (educational)",
        "⚙ Analysis Method : Gate-level delay accumulation",
        "",
        "── Critical Path ───────────────────────────────",
        f"  DFF Clk-to-Q delay   : {timing['dff_clk_to_q_ns']} ns",
        f"  Combinational delay   : {timing['combinational_delay_ns']} ns",
        f"  Setup time            : {timing['setup_time_ns']} ns",
        f"  ─────────────────────────────────────────────",
        f"  Critical path total   : {timing['critical_path_ns']} ns",
        f"  Max frequency (est.)  : {timing['max_frequency_mhz']} MHz",
        "",
        "── Hold Time ───────────────────────────────────",
        f"  Hold time             : {timing['hold_time_ns']} ns",
        "",
        "── Gate Delay Breakdown ────────────────────────",
    ]

    for ctype, count in sorted(cells.items(), key=lambda x: -x[1]):
        d = GATE_DELAY_NS.get(ctype, GATE_DELAY_NS["default"])
        lines.append(f"  {ctype:<20} x{count:>4}  →  delay/gate: {d} ns")

    lines += [
        "",
        "── Note ────────────────────────────────────────",
        f"  {timing['note']}",
        "",
        "  For production-grade timing: add OpenSTA +",
        "  a Liberty file (.lib) from your target PDK.",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--netlist",  default="synth_netlist.v")
    parser.add_argument("--output",   default="timing_report.txt")
    parser.add_argument("--yosys-log", default="yosys_log.txt")
    args = parser.parse_args()

    cells  = parse_cells_from_log(Path(args.yosys_log))
    timing = estimate_critical_path(cells)
    report = format_report(cells, timing)

    Path(args.output).write_text(report)
    print(report)
    print(f"\n✅ Timing report written to: {args.output}")


if __name__ == "__main__":
    main()
