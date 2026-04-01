#!/usr/bin/env python3
"""
build_report.py — Assembles simulation_log.md.

Images are referenced by relative path (same directory).
GitHub renders committed SVG/PNG via relative markdown links.
Waveform is now SVG from WaveDrom (falls back to PNG if SVG missing).
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_text(path: str, fallback: str = "_Not available._") -> str:
    p = Path(path)
    if p.exists() and p.stat().st_size > 0:
        return p.read_text().strip()
    return fallback


def load_json(path: str) -> dict:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def image_link(path: str, alt: str) -> str:
    """
    Relative markdown image link — works on GitHub when file is committed
    to the same directory as simulation_log.md.
    """
    return f"![{alt}]({path})"


def build_waveform_section() -> str:
    # Prefer WaveDrom SVG, fallback to PNG
    if Path("waveform.svg").exists():
        return (
            "### Signal Waveform\n\n"
            + image_link("waveform.svg", "Waveform")
            + "\n\n> *Rendered by WaveDrom · "
              "Click image to open full view*\n"
        )
    elif Path("waveform.png").exists():
        return (
            "### Signal Waveform\n\n"
            + image_link("waveform.png", "Waveform")
            + "\n"
        )
    return "> ⚠️ Waveform export was skipped or failed.\n"


def build_schematic_section() -> str:
    out = ""
    if Path("schematic.svg").exists():
        out += (
            "### Gate-Level Schematic (netlistsvg)\n\n"
            + image_link("schematic.svg", "Schematic")
            + "\n\n> *Click to open full schematic.*\n"
        )
    if Path("schematic_gates.svg").exists():
        out += (
            "\n### Yosys Gate Diagram\n\n"
            + image_link("schematic_gates.svg", "Gate Diagram")
            + "\n\n> *Click to open full gate diagram.*\n"
        )
    if not out:
        out = "> ⚠️ Schematic generation skipped.\n"
    return out


def build_metrics_table(metrics: dict) -> str:
    if not metrics:
        return "_Metrics not available._"

    summary   = metrics.get("summary", {})
    breakdown = metrics.get("cell_breakdown", [])

    lines = [
        "### Hardware Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Cells | **{summary.get('total_cells', 'N/A')}** |",
        f"| Estimated Transistors | **{summary.get('estimated_transistors', 0):,}** |",
        f"| Estimated Die Area | **{summary.get('estimated_area_um2', 'N/A')} µm²** |",
        f"| Reference Node | {summary.get('reference_node', 'N/A')} |",
        f"| Wire Count | {metrics.get('wire_count', 'N/A')} |",
        f"| Port Count | {metrics.get('port_count', 'N/A')} |",
        "",
        "> ⚠️ Area & transistor counts are **educational estimates** based on generic "
        "7nm CMOS assumptions. Actual values require PDK-specific P&R.",
        "",
    ]

    if breakdown:
        lines += [
            "### Cell-Level Breakdown",
            "",
            "| Cell Type | Count | Transistors Each | Transistors Total |",
            "|-----------|------:|-----------------:|------------------:|",
        ]
        for row in breakdown:
            lines.append(
                f"| `{row['cell_type']}` "
                f"| {row['count']} "
                f"| {row['transistors_each']} "
                f"| {row['transistors_total']} |"
            )
        lines.append("")

    return "\n".join(lines)


def build_report(
    project: str,
    sim_output: str,
    compile_log: str,
    metrics: dict,
    timing_text: str,
) -> str:

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    waveform_section  = build_waveform_section()
    schematic_section = build_schematic_section()
    metrics_section   = build_metrics_table(metrics)

    # Artifacts table — only list files that actually exist
    artifact_rows = [
        ("simulation_log.md",    "This report"),
        ("waveform.svg",         "WaveDrom timing diagram (SVG)"),
        ("waveform.png",         "Timing diagram (PNG fallback)"),
        ("schematic.svg",        "Gate-level schematic (netlistsvg)"),
        ("schematic_gates.svg",  "Yosys gate diagram"),
        ("timing_report.txt",    "Timing analysis / critical path"),
        ("hardware_metrics.json","Structured metrics (JSON)"),
        ("synth_netlist.v",      "Post-synthesis Verilog netlist"),
    ]
    artifact_table = "| File | Description |\n|------|-------------|\n"
    for fname, desc in artifact_rows:
        if Path(fname).exists():
            artifact_table += f"| [`{fname}`]({fname}) | {desc} |\n"

    report = f"""# 📊 EDA Report: `{project}`

> **Generated:** {now}
> **Toolchain:** Icarus Verilog · WaveDrom · Yosys · Netlistsvg
> **Pipeline:** GitHub Actions — HDL Ecosystem

---

## 1. Simulation Log

```text
{sim_output}
```

---

## 2. Compilation Output

```text
{compile_log}
```

---

## 3. Waveform Analysis

{waveform_section}

---

## 4. Gate-Level Synthesis

{schematic_section}

---

## 5. Hardware Metrics

{metrics_section}

---

## 6. Timing Analysis

```text
{timing_text}
```

---

## 7. Generated Files

{artifact_table}

---

<sub>🤖 Auto-generated by the HDL Ecosystem Pipeline · Do not edit manually</sub>
"""
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project",       required=True)
    parser.add_argument("--sim-output",    default="sim_output.txt")
    parser.add_argument("--compile-log",   default="compile_log.txt")
    parser.add_argument("--metrics",       default="hardware_metrics.json")
    parser.add_argument("--timing",        default="timing_report.txt")
    parser.add_argument("--has-waveform",  default="false")
    parser.add_argument("--has-schematic", default="false")
    parser.add_argument("--output",        default="simulation_log.md")
    args = parser.parse_args()

    report = build_report(
        project     = args.project,
        sim_output  = load_text(args.sim_output),
        compile_log = load_text(args.compile_log),
        metrics     = load_json(args.metrics),
        timing_text = load_text(args.timing),
    )

    Path(args.output).write_text(report)
    print(f"✅ Report written to: {args.output}")


if __name__ == "__main__":
    main()
