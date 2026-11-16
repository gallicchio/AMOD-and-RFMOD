// The logic analyser: both ports' sixteen pins (synchronised) into a block RAM, a sample every
// (div + 1) clocks, started by a register write or, with a trigger mask, by the first change on a
// masked pin after that write.  Two samples a word (the earlier in bits 15:0), read out through
// regbus's dump stream.  With a trigger, sample 0 is the pins one clock before the change, so the
// edge that started the capture is in it.  2^(AW+1) samples: 16384 at AW = 13 (sixteen DP16KD).
`default_nettype none

module capture #(parameter AW = 13) (
    input  wire        clk,
    input  wire [15:0] pins,            // {port B, port A}, synchronised
    input  wire        start, abort,    // one-clock strobes
    input  wire [23:0] div,
    input  wire [AW+1:0] len,           // samples to take, 1 .. 2^(AW+1)
    input  wire [15:0] trig_mask,
    output reg         busy = 0,
    output reg         done = 0,
    output reg         trig = 0,
    output reg  [AW+1:0] count = 0,
    input  wire [15:0] dump_addr,
    output reg  [31:0] dump_data = 0    // two clocks after dump_addr
);
    reg [31:0] mem [0:(1<<AW)-1];
    reg [31:0] mem_rd = 0;
    reg        mem_we = 0;
    reg [AW-1:0] mem_wa = 0;
    reg [31:0] mem_wd = 0;
    always @(posedge clk) begin
        if (mem_we) mem[mem_wa] <= mem_wd;
        mem_rd <= mem[dump_addr[AW-1:0]];
        dump_data <= mem_rd;
    end

    reg [15:0] prev = 0, lo = 0;
    reg [23:0] dcnt = 0;
    reg        armed = 0;
    wire       hit = trig_mask == 0 || ((pins ^ prev) & trig_mask) != 0;
    wire       take = busy && (armed ? hit : dcnt == 0);
    always @(posedge clk) begin
        prev <= pins;
        mem_we <= 1'b0;
        if (start) begin busy <= 1'b1; done <= 1'b0; trig <= 1'b0; armed <= 1'b1; count <= 0; dcnt <= 0; end
        else if (abort) begin busy <= 1'b0; armed <= 1'b0; end
        else if (busy) begin
            if (armed && hit) begin armed <= 1'b0; trig <= 1'b1; dcnt <= trig_mask == 0 ? div : 24'd0; end
            else if (!armed) dcnt <= dcnt == 0 ? div : dcnt - 24'd1;
            if (take) begin                              // an even sample opens a word, the odd one completes it
                mem_we <= 1'b1; mem_wa <= count[AW:1];
                mem_wd <= count[0] ? {prev, lo} : {16'h0000, prev};
                if (!count[0]) lo <= prev;
                count <= count + 1'b1;
                if (count + 1'b1 == len) begin busy <= 1'b0; done <= 1'b1; end
            end
        end
    end
endmodule
`default_nettype wire
