#!/usr/bin/env python3
"""
vcd_to_png.py — Converts a VCD file to a waveform PNG using matplotlib.
No GTKWave needed. Works perfectly headless in GitHub Actions.
"""

import argparse
import re
import sys
from pathlib import Path


def parse_vcd(vcd_path: str):
    """Parse a VCD file and return signal names + time/value data."""
    signals = {}      # id -> name
    values  = {}      # id -> [(time, value)]
    time    = 0
    scope   = []

    with open(vcd_path) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Variable declaration: $var wire 2 ! tb_trit_in $end
        if line.startswith("$var"):
            parts = line.split()
            if len(parts) >= 5:
                sig_id   = parts[3]
                sig_name = parts[4]
                signals[sig_id]  = sig_name
                values[sig_id]   = []
        
        # Timstep
        elif line.startswith("#"):
            try:
                time = int(line[1:])
            except ValueError:
                pass

        # Vector value change: b01 !
        elif line.startswith("b") or line.startswith("B"):
            parts = line.split()
            if len(parts) >= 2:
                val   = parts[0][1:]   # strip 'b'
                sig_id = parts[1]
                if sig_id in values:
                    values[sig_id].append((time, val))

        # Scalar value change: 0! or 1!
        elif len(line) >= 2 and line[0] in "01xzXZ":
            val    = line[0]
            sig_id = line[1:]
            if sig_id in values:
                values[sig_id].append((time, val))

        i += 1

    return signals, values


def bin_to_int(b: str) -> int:
    try:
        return int(b, 2)
    except ValueError:
        return -1


def plot_waveform(signals, values, end_time, output_path: str):
    import matplotlib
    matplotlib.use("Agg")   # headless backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    sig_ids   = [sid for sid in signals if values.get(sid)]
    sig_names = [signals[sid] for sid in sig_ids]
    n         = len(sig_ids)

    if n == 0:
        print("⚠ No signals found in VCD.", file=sys.stderr)
        return False

    fig, axes = plt.subplots(n, 1, figsize=(12, 2.2 * n), sharex=True)
    if n == 1:
        axes = [axes]

    fig.patch.set_facecolor("#1e1e2e")
    colors = ["#89dceb", "#a6e3a1", "#fab387", "#f38ba8", "#cba6f7"]

    for idx, (sid, ax) in enumerate(zip(sig_ids, axes)):
        name   = signals[sid]
        events = values[sid]
        color  = colors[idx % len(colors)]

        ax.set_facecolor("#181825")
        ax.set_ylabel(name, color="#cdd6f4", fontsize=9,
                      rotation=0, labelpad=60, va="center")
        ax.tick_params(colors="#585b70", labelcolor="#585b70")
        for spine in ax.spines.values():
            spine.set_edgecolor("#313244")

        if not events:
            continue

        # Build step plot data
        times  = [0]
        vals   = [bin_to_int(events[0][1]) if events else 0]
        for t, v in events:
            times.append(t)
            vals.append(bin_to_int(v))
        times.append(end_time)
        vals.append(vals[-1])

        max_val = max(v for v in vals if v >= 0) or 1
        ax.step(times, vals, where="post", color=color, linewidth=1.8)
        ax.fill_between(times, vals, step="post",
                        alpha=0.15, color=color)
        ax.set_ylim(-0.3, max_val + 0.5)
        ax.set_yticks(range(max_val + 1))

        # Value labels at each transition
        for t, v in events:
            ax.annotate(f"{bin_to_int(v)}",
                        xy=(t, bin_to_int(v)),
                        xytext=(0, 6), textcoords="offset points",
                        fontsize=7, color=color, ha="center")

    axes[-1].set_xlabel("Time (ps)", color="#cdd6f4", fontsize=9)
    axes[-1].tick_params(axis="x", colors="#585b70", labelcolor="#cdd6f4")

    fig.suptitle("Simulation Waveform", color="#cdd6f4",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"✅ Waveform saved: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcd",    default="dump.vcd")
    parser.add_argument("--output", default="waveform.png")
    args = parser.parse_args()

    if not Path(args.vcd).exists():
        print(f"❌ VCD file not found: {args.vcd}", file=sys.stderr)
        sys.exit(1)

    signals, values = parse_vcd(args.vcd)

    # Find end time
    end_time = 0
    for evts in values.values():
        if evts:
            end_time = max(end_time, evts[-1][0])
    end_time = max(end_time, 1) * 1.1

    ok = plot_waveform(signals, values, end_time, args.output)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
