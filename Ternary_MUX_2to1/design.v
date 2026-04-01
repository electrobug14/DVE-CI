// ============================================================
// Ternary 2-to-1 Multiplexer
//
// Uses the same 2-bit ternary encoding as the testbench:
//   2'b00 → Ternary 0
//   2'b01 → Ternary 1
//   2'b10 → Ternary 2
//   2'b11 → Error/Invalid
//
// trit_in[1] acts as the SELECT line:
//   trit_in[1] = 0  → trit_out mirrors trit_in[0] (pass-low)
//   trit_in[1] = 1  → trit_out outputs Ternary 2   (pass-high)
//
// This lets both bits of the 2-bit bus drive the MUX logic,
// fitting the universal testbench without any changes.
// ============================================================
module dut (
    input  wire [1:0] trit_in,
    output reg  [1:0] trit_out
);

    wire sel;
    wire [1:0] data_a;

    // sel = trit_in[1] (MSB is the select line)
    assign sel    = trit_in[1];
    // data_a carries the lower trit
    assign data_a = {1'b0, trit_in[0]};

    always @(*) begin
        case (sel)
            1'b0: begin
                // Select A: pass trit_in[0] as ternary value
                case (trit_in[0])
                    1'b0:    trit_out = 2'b00;   // Ternary 0
                    1'b1:    trit_out = 2'b01;   // Ternary 1
                    default: trit_out = 2'b11;
                endcase
            end
            1'b1: begin
                // Select B: always output Ternary 2
                trit_out = 2'b10;
            end
            default: trit_out = 2'b11;
        endcase
    end

endmodule
// trigger
