// One Pmod socket of pmodbench: eight pins, each an output register bit, an output enable and a
// synchronised input, with a source select that can hand the pin to one of four clock generators,
// the SPI engine or the one-bit sampler's feedback.  Instantiated twice (port A, port B) behind the
// register bus; everything runs on the 25 MHz TCXO.  Pin k of the vectors is the tile boards' IO(k+1)
// (pmod[0..3] = Pmod pins 1-4, pmod[4..7] = Pmod pins 7-10).
//
// Registers (offsets from the port's base: 0x20 port A, 0x40 port B; host/pmodbench.py has the same table):
//   00 OUT       rw  [7:0] the output register, bit k = IO(k+1)
//   01 OE        rw  [7:0] 1 = drive the pin (power-up 0: every pin high-Z)
//                    [15:8] LOCK: 1 = this pin is never driven, whatever OE says (the driver locks a tile's inputs)
//   02 IN        ro  [7:0] the pins, synchronised  [15:8] what the port would drive (after the source select)
//                    [23:16] the enables in force (OE and not LOCK)
//   03 OUT_SET   wo  [7:0] ones set OUT bits      04 OUT_CLR  wo  [7:0] ones clear OUT bits
//   05 SRC       rw  four bits a pin, [3:0] IO1 ... [31:28] IO8:
//                    0 the OUT bit   1-4 generator 1-4   5-8 generator 1-4 inverted (low outside a burst, like the true one)
//                    9 SPI SCK   10 SPI MOSI   11 the sampler's registered bit   12 that bit inverted   13-15 low
//   06 GEN_CTRL  rw  [3:0] enable generators 1-4 (a disabled generator's outputs, true and inverted, are low)
//                wo  [11:8] restart generators 1-4: phase accumulator and burst counter to 0 on the same clock
//   07 SPI_CFG   rw  [4:0] bits - 1 (1 to 32 bits)  [5] LSB first  [6] CPOL  [7] CPHA  [10:8] MISO pin (0 = IO1)
//                    [11] late sample (with CPHA = 1: half a period after the trailing edge, for SSI encoders)
//                    [31:16] half period in clocks, minus 1 (0 = 12.5 MHz SCK; 24 = 500 kHz)
//   08 SPI_DATA  wo  the word (right-aligned; MSB first sends bit n-1 first): writing it starts the transfer
//                ro  the raw receive shift register: MSB first, the word is its low n bits; LSB first, its top n bits
//   09 STATUS    ro  [0] SPI busy  [1] the sampler's registered bit  [15:8] frequency counter sequence number
//                    [31:16] quadrature errors (both lines changed at once; saturates)
//   0A SAMP_CFG  rw  [2:0] input pin  [5:4] generator whose rising edge samples it  [12:8] log2 of the window (0-31)
//                    (writing it restarts the window)
//   0B SAMP_ONES ro  ones among the last complete window's 2^log2 samples
//   0C SAMP_SEQ  ro  [15:0] windows completed
//   0D MEAS_CFG  rw  [2:0] frequency counter's pin  [6:4] quadrature A pin  [10:8] quadrature B pin
//                wo  [16] clear the quadrature count and its errors
//   0E FREQ      ro  rising edges of the pin in the last gate (the gate is the top level's GATE register, in clocks);
//                    the pin is sampled at 25 MHz, so this counts up to 12 MHz
//   0F QUAD      ro  signed 32-bit position, four counts a cycle, up when A leads B
//   10-13 GEN1   rw  INC (f = INC x 25 MHz / 2^32), DUTY (high while phase < DUTY; 0xFFFFFFFF = always high),
//                    PHASE (added to the accumulator), BURST ([15:0] N cycles on, [31:16] of every M; N = 0 continuous)
//   14-17 GEN2, 18-1B GEN3, 1C-1F GEN4 the same
//
// Timing notes.  A generator's output is the registered comparison of (accumulator + PHASE) with DUTY, so
// generators restarted together and given the same INC keep an exact phase relation: two of them with
// PHASES 0 and 2^31 and DUTY below 2^31 never overlap.  The burst gate counts the accumulator's own cycles
// (before PHASE), so generators restarted together gate together.  Pins leave through one more register.
// The SPI engine samples MISO SPI_SKEW clocks after it moves SCK: its own two output registers and the
// two-flop input synchroniser, so the sample is the pin as it stood when the SCK edge left the FPGA.
`default_nettype none

module pmod_port #(parameter SPI_SKEW = 3) (
    input  wire        clk,
    input  wire [4:0]  addr,
    input  wire [31:0] wdata,
    input  wire        we,              // a write to this port's register `addr`
    output reg  [31:0] rdata,           // combinational from addr
    input  wire        restart_all,     // restart every generator (the top level's CONTROL strobe, both ports)
    input  wire        safe,            // every pin high-Z, the generators off
    input  wire        gate,            // one clock in every gate period
    input  wire [7:0]  pin_i,           // the pads (asynchronous)
    output reg  [7:0]  pin_o = 0,
    output reg  [7:0]  pin_oe = 0,
    output wire [7:0]  pin_s            // the pads, synchronised (two clocks late)
);
    // ---- the pins ------------------------------------------------------------------------------------
    reg [7:0] s1 = 0, s2 = 0;
    always @(posedge clk) begin s1 <= pin_i; s2 <= s1; end
    assign pin_s = s2;

    reg [7:0]  out_r = 0, oe_r = 0, lock_r = 0;
    reg [31:0] src = 0;
    reg [3:0]  gen_en = 0;
    reg [3:0]  gen_restart = 0;

    // ---- the four generators ---------------------------------------------------------------------------
    reg  [3:0]   g = 0, gn = 0;          // true and inverted outputs, both low when disabled or outside a burst
    wire [127:0] g_rd;                   // each generator's register at addr[1:0], for the read mux
    genvar gi;
    generate for (gi = 0; gi < 4; gi = gi + 1) begin : gen
        reg  [31:0] inc = 0, duty = 32'h80000000, phase = 0, burst = 0;
        reg  [31:0] acc = 0;
        reg  [15:0] bcnt = 0;            // the burst's cycle counter: 0 .. M-1
        wire [32:0] sum = {1'b0, acc} + {1'b0, inc};
        wire [15:0] bn = burst[15:0], bm = burst[31:16];
        wire [31:0] ph = acc + phase;
        wire        hi = (ph < duty) || (&duty);
        wire        on = gen_en[gi] && (bn == 0 || bcnt < bn);
        always @(posedge clk) begin
            if (we && addr[4] && addr[3:2] == gi) case (addr[1:0])
                2'd0: inc <= wdata;
                2'd1: duty <= wdata;
                2'd2: phase <= wdata;
                2'd3: burst <= wdata;
            endcase
            if (restart_all || gen_restart[gi]) begin acc <= 0; bcnt <= 0; end
            else begin
                acc <= sum[31:0];
                if (sum[32]) bcnt <= (bcnt + 16'd1 >= bm) ? 16'd0 : bcnt + 16'd1;
            end
            g[gi]  <= on && hi;
            gn[gi] <= on && !hi;
        end
        assign g_rd[32*gi +: 32] = addr[1:0] == 2'd0 ? inc : addr[1:0] == 2'd1 ? duty : addr[1:0] == 2'd2 ? phase : burst;
    end endgenerate

    // ---- the SPI engine --------------------------------------------------------------------------------
    reg  [4:0]  spi_n = 5'd31;           // bits - 1
    reg         spi_lsb = 0, spi_cpol = 0, spi_cpha = 0, spi_late = 0;
    reg  [2:0]  spi_miso = 0;
    reg  [15:0] spi_half = 16'd24;       // 500 kHz
    reg         spi_run = 0, sck = 0, mosi = 0;
    reg  [1:0]  spi_ph = 0;              // 0 before the leading edge, 1 before the trailing edge, 2 the tail
    reg  [15:0] spi_cnt = 0;
    reg  [5:0]  spi_left = 0;
    reg  [31:0] tx_sh = 0, rx_sh = 0;
    reg  [SPI_SKEW-1:0] stb = 0;         // the sample strobe on its way to meet the synchronised MISO
    wire        spi_start = we && addr == 5'h08 && !spi_run;
    wire        tx_bit = spi_lsb ? tx_sh[0] : tx_sh[31];
    wire [31:0] tx_next = spi_lsb ? {1'b0, tx_sh[31:1]} : {tx_sh[30:0], 1'b0};
    wire [31:0] tx_load = spi_lsb ? wdata : wdata << (5'd31 - spi_n);          // MSB first: the first bit to bit 31
    wire        tx_first = spi_lsb ? wdata[0] : wdata[spi_n];
    wire        spi_busy = spi_run || (|stb);
    // sample now: CPHA 0 on the leading edge; CPHA 1 on the trailing edge or, late, at the end of the bit's cell
    // (the next leading edge, and half a period after the last trailing edge)
    wire        spi_edge = spi_run && spi_cnt == 0;
    wire        spi_stb = spi_edge && (spi_ph == 2'd0 ? (spi_cpha ? (spi_late && spi_left != {1'b0, spi_n} + 6'd1) : 1'b1) :
                                       spi_ph == 2'd1 ? (spi_cpha && !spi_late) : (spi_cpha && spi_late));
    always @(posedge clk) begin
        stb <= {stb, spi_stb};
        if (stb[SPI_SKEW-1]) rx_sh <= spi_lsb ? {s2[spi_miso], rx_sh[31:1]} : {rx_sh[30:0], s2[spi_miso]};
        if (spi_start) begin
            spi_run <= 1'b1; spi_ph <= 0; spi_cnt <= spi_half; spi_left <= {1'b0, spi_n} + 6'd1;
            sck <= spi_cpol; rx_sh <= 0;
            if (spi_cpha) begin tx_sh <= tx_load; mosi <= 1'b0; end
            else begin tx_sh <= spi_lsb ? {1'b0, wdata[31:1]} : (wdata << (5'd31 - spi_n)) << 1; mosi <= tx_first; end
        end else if (spi_run) begin
            if (spi_cnt != 0) spi_cnt <= spi_cnt - 16'd1;
            else begin
                spi_cnt <= spi_half;
                case (spi_ph)
                2'd0: begin                                  // the leading edge
                    sck <= ~spi_cpol; spi_ph <= 2'd1;
                    if (spi_cpha) begin mosi <= tx_bit; tx_sh <= tx_next; end
                end
                2'd1: begin                                  // the trailing edge
                    sck <= spi_cpol; spi_left <= spi_left - 6'd1;
                    spi_ph <= spi_left == 6'd1 ? 2'd2 : 2'd0;
                    if (!spi_cpha) begin mosi <= spi_left == 6'd1 ? 1'b0 : tx_bit; tx_sh <= tx_next; end
                end
                default: begin spi_run <= 1'b0; mosi <= 1'b0; end      // half a period after the last edge
                endcase
            end
        end else sck <= spi_cpol;
    end

    // ---- the one-bit sampler: ones in 2^N samples, and the registered bit as a pin source -----------------
    reg  [2:0]  samp_pin = 0; reg [1:0] samp_gen = 0; reg [4:0] samp_log2 = 5'd10;
    reg         samp_d = 0, samp_bit = 0;
    reg  [31:0] samp_cnt = 0, samp_acc = 0, samp_ones = 0;
    reg  [15:0] samp_seq = 0;
    wire        samp_stb = g[samp_gen] && !samp_d;
    wire [31:0] samp_mask = ~(32'hFFFFFFFF << samp_log2);
    wire        samp_in = s2[samp_pin];
    always @(posedge clk) begin
        samp_d <= g[samp_gen];
        if (we && addr == 5'h0a) begin samp_cnt <= 0; samp_acc <= 0; end
        else if (samp_stb) begin
            samp_bit <= samp_in;
            if ((samp_cnt & samp_mask) == samp_mask) begin
                samp_ones <= samp_acc + {31'b0, samp_in}; samp_acc <= 0; samp_cnt <= 0; samp_seq <= samp_seq + 16'd1;
            end else begin samp_acc <= samp_acc + {31'b0, samp_in}; samp_cnt <= samp_cnt + 32'd1; end
        end
    end

    // ---- the frequency counter and the quadrature decoder ------------------------------------------------
    reg  [2:0]  f_pin = 0, qa_pin = 3'd4, qb_pin = 3'd5;
    reg         f_d = 0;
    reg  [31:0] f_cnt = 0, f_res = 0;
    reg  [7:0]  f_seq = 0;
    wire        f_rise = s2[f_pin] && !f_d;
    reg  [1:0]  q_d = 0;
    reg  [31:0] q_cnt = 0;
    reg  [15:0] q_err = 0;
    wire [1:0]  q_now = {s2[qb_pin], s2[qa_pin]};
    wire        q_clear = we && addr == 5'h0d && wdata[16];
    always @(posedge clk) begin
        f_d <= s2[f_pin];
        if (gate) begin f_res <= f_cnt; f_cnt <= {31'b0, f_rise}; f_seq <= f_seq + 8'd1; end
        else if (f_rise) f_cnt <= f_cnt + 32'd1;
        q_d <= q_now;
        if (q_clear) begin q_cnt <= 0; q_err <= 0; end
        else case ({q_d, q_now})                     // {B, A} before, {B, A} now; A leads B going up: 00 01 11 10
            4'b0001, 4'b0111, 4'b1110, 4'b1000: q_cnt <= q_cnt + 32'd1;
            4'b0010, 4'b1011, 4'b1101, 4'b0100: q_cnt <= q_cnt - 32'd1;
            4'b0011, 4'b0110, 4'b1001, 4'b1100: if (!(&q_err)) q_err <= q_err + 16'd1;
            default: ;
        endcase
    end

    // ---- the registers ------------------------------------------------------------------------------------
    always @(posedge clk) begin
        gen_restart <= 0;
        if (we) case (addr)
            5'h00: out_r <= wdata[7:0];
            5'h01: begin oe_r <= wdata[7:0]; lock_r <= wdata[15:8]; end
            5'h03: out_r <= out_r | wdata[7:0];
            5'h04: out_r <= out_r & ~wdata[7:0];
            5'h05: src <= wdata;
            5'h06: begin gen_en <= wdata[3:0]; gen_restart <= wdata[11:8]; end
            5'h07: begin spi_n <= wdata[4:0]; spi_lsb <= wdata[5]; spi_cpol <= wdata[6]; spi_cpha <= wdata[7];
                         spi_miso <= wdata[10:8]; spi_late <= wdata[11]; spi_half <= wdata[31:16]; end
            5'h0a: begin samp_pin <= wdata[2:0]; samp_gen <= wdata[5:4]; samp_log2 <= wdata[12:8]; end
            5'h0d: begin f_pin <= wdata[2:0]; qa_pin <= wdata[6:4]; qb_pin <= wdata[10:8]; end
            default: ;
        endcase
        if (safe) begin oe_r <= 0; out_r <= 0; src <= 0; gen_en <= 0; end
    end

    // what each pin would drive, and the pad registers
    wire [7:0] mux;
    genvar pk;
    generate for (pk = 0; pk < 8; pk = pk + 1) begin : sel       // sources 15 .. 0 of pin pk
        wire [15:0] srcs = {3'b000, ~samp_bit, samp_bit, mosi, sck, gn, g, out_r[pk]};
        assign mux[pk] = srcs[src[4*pk +: 4]];
    end endgenerate
    wire [7:0] oe_now = oe_r & ~lock_r;
    always @(posedge clk) begin pin_o <= mux; pin_oe <= safe ? 8'h00 : oe_now; end

    always @(*) case (addr)
        5'h00: rdata = {24'b0, out_r};
        5'h01: rdata = {16'b0, lock_r, oe_r};
        5'h02: rdata = {8'b0, oe_now, mux, s2};
        5'h05: rdata = src;
        5'h06: rdata = {28'b0, gen_en};
        5'h07: rdata = {spi_half, 4'b0, spi_late, spi_miso, spi_cpha, spi_cpol, spi_lsb, spi_n};
        5'h08: rdata = rx_sh;
        5'h09: rdata = {q_err, f_seq, 6'b0, samp_bit, spi_busy};
        5'h0a: rdata = {19'b0, samp_log2, 2'b0, samp_gen, 1'b0, samp_pin};
        5'h0b: rdata = samp_ones;
        5'h0c: rdata = {16'b0, samp_seq};
        5'h0d: rdata = {21'b0, qb_pin, 1'b0, qa_pin, 1'b0, f_pin};
        5'h0e: rdata = f_res;
        5'h0f: rdata = q_cnt;
        default: rdata = addr[4] ? g_rd[32*addr[3:2] +: 32] : 32'h0;
    endcase
endmodule
`default_nettype wire
