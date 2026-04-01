# ============================================================
# wave_export.tcl — GTKWave Headless PNG Exporter
# Called by: xvfb-run gtkwave dump.vcd --script wave_export.tcl
# ============================================================

# ── Load all signals from the VCD ───────────────────────────
set nfacs [gtkwave::getNumFacs]
set wl     [list]

for {set i 0} {$i < $nfacs} {incr i} {
    lappend wl [gtkwave::getFacName $i]
}

gtkwave::addSignalsFromList $wl

# ── Signal display formatting ────────────────────────────────
# Show values as binary (clearest for hardware signals)
set num_traces [gtkwave::getVisibleNumTraces]
for {set i 0} {$i < $num_traces} {incr i} {
    gtkwave::setTraceHighlightFromIndex $i on
}
gtkwave::setAllTraceHighlightFromList [gtkwave::getVisibleNumTraces]

# ── Zoom to fit entire simulation timespan ───────────────────
gtkwave::/Time/Zoom/Zoom_Full

# ── Set window size before capture ──────────────────────────
gtkwave::setWindowStartTime 0

# ── Export PNG ───────────────────────────────────────────────
# Format: PNG, Landscape Letter (11" x 8.5")
gtkwave::/File/Print_To_File PNG {Landscape Letter} 0 waveform.png

# ── Done ─────────────────────────────────────────────────────
gtkwave::/File/Quit
