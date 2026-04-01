# ⚡ HDL Verification Ecosystem

> **Automated Design Verification, Synthesis, Timing Analysis & Waveform Export**  
> Triggered on every `design.v` push via GitHub Actions.

---

## 🗂 Repository Structure

```
.
├── .devcontainer/
│   ├── Dockerfile              # Custom EDA tool image
│   └── devcontainer.json       # VS Code DevContainer config
├── .github/workflows/
│   └── verify.yml              # Full EDA Pipeline
├── scripts/
│   ├── universal_tb.v          # Universal Verilog testbench
│   ├── wave_export.tcl         # GTKWave headless PNG export
│   ├── parse_metrics.py        # Yosys metrics parser
│   ├── estimate_timing.py      # Critical path estimator
│   └── build_report.py         # Markdown report builder
├── Ternary_Buffer_Demo/        # Example project
│   ├── design.v                # Your Verilog design (module: dut)
│   ├── simulation_log.md       # ← Auto-generated report
│   ├── waveform.png            # ← Auto-generated waveform
│   ├── schematic.svg           # ← Auto-generated schematic
│   └── timing_report.txt       # ← Auto-generated timing
└── README.md
```

---

## 🚀 How to Use

### 1. Create a new project
```bash
mkdir My_New_Design
```

### 2. Add your Verilog file
```bash
# design.v — your top module MUST be named 'dut'
# The universal testbench drives:  trit_in [1:0]
# And monitors:                    trit_out [1:0]
```

### 3. Push to GitHub
```bash
git add My_New_Design/design.v
git commit -m "feat: add My_New_Design"
git push
```

### 4. Wait ~60 seconds
The pipeline will automatically generate inside your folder:
- `simulation_log.md` — Full report with embedded images
- `waveform.png`       — Timing diagram
- `schematic.svg`      — Gate-level schematic
- `timing_report.txt`  — Critical path & frequency estimate
- `hardware_metrics.json` — Cell count, transistors, area

---

## 🛠 Toolchain

| Tool | Purpose |
|------|---------|
| Icarus Verilog (`iverilog`) | RTL Simulation |
| GTKWave + xvfb | Waveform → PNG export (headless) |
| Yosys | Logic Synthesis |
| Netlistsvg | Gate schematic → SVG |
| Python 3 | Metrics parsing & report generation |

---

## 📐 Design Conventions

| Convention | Value |
|------------|-------|
| Top module name | `dut` |
| Design filename | `design.v` |
| Timescale | `1ns / 1ps` |
| Input bus | `trit_in [1:0]` |
| Output bus | `trit_out [1:0]` |

> To add more ports, update `scripts/universal_tb.v` accordingly.

---

## 🧪 Running Locally (DevContainer)

Open this repo in VS Code with the **Dev Containers** extension.  
The container auto-installs all EDA tools.

```bash
# Inside the container:
cd Ternary_Buffer_Demo
iverilog -g2012 -o sim.vvp design.v ../scripts/universal_tb.v
vvp sim.vvp
gtkwave dump.vcd
```

---

<sub>Built with the HDL Ecosystem Pipeline · GitHub Actions + Icarus + Yosys + GTKWave</sub>
