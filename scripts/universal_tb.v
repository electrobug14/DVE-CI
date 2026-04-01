// ============================================================
// Universal Testbench — HDL Ecosystem
// Expects the design module to be named: dut
// ============================================================
`timescale 1ns/1ps

module universal_tb;

    // ── Generic 2-bit ternary I/O (expand as needed) ────────
    reg  [1:0] tb_trit_in;
    wire [1:0] tb_trit_out;

    // ── Instantiate Unit Under Test ──────────────────────────
    dut uut (
        .trit_in  (tb_trit_in),
        .trit_out (tb_trit_out)
    );

    // ── VCD Dump for GTKWave ─────────────────────────────────
    initial begin
        $dumpfile("dump.vcd");
        $dumpvars(0, universal_tb);
    end

    // ── Stimulus & Monitoring ────────────────────────────────
    initial begin
        $display("================================================");
        $display("  HDL Ecosystem — Simulation Start");
        $display("  Module: dut  |  Timescale: 1ns/1ps");
        $display("================================================");

        $monitor("  [%0t ns] trit_in=%b (%0d) | trit_out=%b (%0d)",
                 $time,
                 tb_trit_in,  tb_trit_in,
                 tb_trit_out, tb_trit_out);

        // ── Test Vector: all 4 combinations ─────────────────
        tb_trit_in = 2'b00; #10;   // State 0
        tb_trit_in = 2'b01; #10;   // State 1
        tb_trit_in = 2'b10; #10;   // State 2
        tb_trit_in = 2'b11; #10;   // Invalid / Error state

        $display("================================================");
        $display("  Simulation Finished at %0t ps", $time);
        $display("================================================");
        $finish;
    end

endmodule
