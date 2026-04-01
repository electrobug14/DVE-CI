#!/usr/bin/env python3
"""
build_report.py — Assembles simulation_log.md with inline SVG/PNG.

GitHub renders images in .md files via relative paths ONLY when the
image file is committed into the same repo folder. SVG files render
natively; PNG needs to be committed too.
"""

import argparse
import base64
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


def embed_png_as_base64(png_path: str) -> str:
    """Embed PNG as base64 data URI so it renders in GitHub Markdown."""
    p = Path(png_path)
    if p.exists():
        data = base64.b64encode(p.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{data}" alt="Waveform" width="100%"/>'
    return "_Waveform image not available._"


def embed_svg_inline(svg_path: str) -> str:
    """
    For SVG: GitHub Markdown does NOT render <img src="x.svg"> from repo.
    We use a relative markdown image link — this works when the SVG is
    committed to the same directory and viewed on github.com.
    """
    p = Path(svg_path)
    if p.exists():
        name = p.name
        return f'![Schematic]({name})\n\n> *Click to open full schematic. File: `{name}`*'
    return "_Schematic not available._"


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
    has_waveform: bool,
    has_schematic: bool,
) -> str:

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    metrics_section = build_metrics_table(metrics)

    # Waveform — embed as base64 PNG so it renders even without clicking
    if has_waveform and Path("waveform.png").exists():
        waveform_section = (
            "### Signal Waveform\n\n"
            + embed_png_as_base64("waveform.png")
            + "\n"
        )
    else:
        waveform_section = "> ⚠️ Waveform export was skipped or failed.\n"

    # Schematic — relative path link (works on github.com when file is committed)
    if has_schematic and Path("schematic.svg").exists():
        schematic_section = (
            "### Gate-Level Schematic (netlistsvg)\n\n"
            + embed_svg_inline("schematic.svg")
            + "\n"
        )
        if Path("schematic_gates.svg").exists():
            schematic_section += (
                "\n### Yosys Gate Diagram\n\n"
                + embed_svg_inline("schematic_gates.svg")
                + "\n"
            )
    else:
        schematic_section = "> ⚠️ Schematic generation skipped.\n"

    report = f"""# 📊 EDA Report: `{project}`

> **Generated:** {now}
> **Toolchain:** Icarus Verilog · GTKWave · Yosys · Netlistsvg
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

| File | Description |
|------|-------------|
| `simulation_log.md` | This report |
| `waveform.png` | GTKWave timing diagram |
| `schematic.svg` | Gate-level schematic (netlistsvg) |
| `schematic_gates.svg` | Yosys gate diagram |
| `timing_report.txt` | Timing analysis / critical path |
| `hardware_metrics.json` | Structured metrics (JSON) |
| `synth_netlist.v` | Post-synthesis Verilog netlist |

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
        project       = args.project,
        sim_output    = load_text(args.sim_output),
        compile_log   = load_text(args.compile_log),
        metrics       = load_json(args.metrics),
        timing_text   = load_text(args.timing),
        has_waveform  = args.has_waveform.lower() == "true",
        has_schematic = args.has_schematic.lower() == "true",
    )

    Path(args.output).write_text(report)
    print(f"✅ Report written to: {args.output}")


if __name__ == "__main__":
    main()
