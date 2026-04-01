// ============================================================
// Ternary Buffer Demo — HDL Ecosystem
//
// Represents a 3-state (ternary) logic buffer using 2-bit encoding:
//   2'b00 → Ternary 0
//   2'b01 → Ternary 1
//   2'b10 → Ternary 2
//   2'b11 → Error/Invalid
//
// Top module MUST be named 'dut' for the universal testbench.
// ============================================================
module dut (
    input  wire [1:0] trit_in,
    output reg  [1:0] trit_out
);

    always @(*) begin
        case (trit_in)
            2'b00: trit_out = 2'b00;   // Ternary 0
            2'b01: trit_out = 2'b01;   // Ternary 1
            2'b10: trit_out = 2'b10;   // Ternary 2
            default: trit_out = 2'b11; // Error / unknown
        endcase
    end

endmodule

// retrigger
//==
