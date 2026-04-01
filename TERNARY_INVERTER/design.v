// ============================================================
// Design: Ternary Inverter (Base-3 Logic)
// Fits: universal_tb.v
// ============================================================

module dut (
    input  wire [1:0] trit_in,
    output reg  [1:0] trit_out
);

    always @(*) begin
        case (trit_in)
            2'b00:   trit_out = 2'b10; // Input 0 -> Output 2
            2'b01:   trit_out = 2'b01; // Input 1 -> Output 1
            2'b10:   trit_out = 2'b00; // Input 2 -> Output 0
            2'b11:   trit_out = 2'b00; // Invalid state -> Default to 0
            default: trit_out = 2'b00;
        endcase
    end

endmodule
