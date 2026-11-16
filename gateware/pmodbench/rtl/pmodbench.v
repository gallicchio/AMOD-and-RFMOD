// pmodbench: the ECP5-2ADC-2DAC rev A board as a remote pair of hands on its two Pmod sockets.
// A PC drives and reads the sixteen Pmod pins over the FT2232H's serial channel (1 Mbaud, the register
// bus of the board's own bring-up gateware), so a tile board of the AMOD / RF-MOD family plugged into
// a Pmod can be brought up without anyone at the bench.  It uses as little of the host board as it can:
// the 25 MHz TCXO (no PLL), the UART, the LEDs and the Pmod pins.  The converters' static pins and the
// PHY's reset are held where the board's blink.v holds them (ADC powered down, DAC asleep, PHY out of
// reset, USB pull-up off), and CLK OUT carries the TCXO as it does there (IQ-MOD's q3 and RF-MOD's r10
// take their 25 MHz reference from it); every other pin is left out of the design.
//
// Register map (32-bit registers, 7-bit addresses; host/pmodbench.py has the same table):
//   00 ID        ro  0x504D4231 ("PMB1")
//   01 VERSION   ro  BUILD_ID (the build's date, 0xYYYYMMDD)
//   02 SCRATCH   rw
//   03 CONTROL   rw  [0] CLK OUT carries the TCXO (default 1; 0 = low)
//                wo  [8] restart every generator of both ports on the same clock  [9] SAFE: every Pmod pin
//                    high-Z, OUT and SRC cleared, generators off (the LOCK bits stay)
//   04 LEDS      rw  [7:1] LED1-7 (1 = on; LED0 is the heartbeat, 1.5 Hz)  [8] red [9] green [10] blue (1 = on)
//   05 GATE      ro  the frequency counters' gate in TCXO cycles (25000000 = 1 s on the board)
//   06 PINS      ro  [7:0] port A's pins [15:8] port B's pins [23:16] A's enables in force [31:24] B's
//   10 CAP_CTRL  wo  [0] start a capture  [1] abort it
//   11 CAP_DIV   rw  [23:0] a sample every (div + 1) clocks of 40 ns
//   12 CAP_LEN   rw  samples to take, 1 .. 16384
//   13 CAP_TRIG  rw  [15:0] trigger mask ([7:0] port A, [15:8] port B): 0 = start at once, else at the first
//                    change of a masked pin (sample 0 is then the pins one clock before the change)
//   14 CAP_STAT  ro  [0] busy (armed or running)  [1] done  [2] triggered  [30:16] samples taken
//   20-3F        port A's registers, 40-5F port B's: see rtl/pmod_port.v
//   7E DUMP_LEN  rw  words a read of 7F streams (two samples a word)
//   7F DUMP      ro  the capture from word 0: [15:0] the earlier sample, [31:16] the later; a sample is
//                    [7:0] port A IO1-8, [15:8] port B IO1-8
`default_nettype none

module pmodbench #(parameter BUILD_ID = 32'h20261115, UART_DIV = 25, GATE_CYCLES = 25_000_000, CAP_AW = 13) (
    input  wire       clk_tcxo,
    output wire       clk_out,
    output wire       led0, led1, led2, led3, led4, led5, led6, led7,
    output wire       led_r, led_g, led_b,
    input  wire       uart_rx,
    output wire       uart_tx,
    output wire       adc_pdwn_a, adc_pdwn_b, adc_dcs, adc_dfs, dac_mode, dac_sleep, eth_rst_n, usb_pullup,
    inout  wire [7:0] pmoda, pmodb
);
    wire clk = clk_tcxo;

    // ---- the rest of the board, as blink.v leaves it ------------------------------------------------
    assign adc_pdwn_a = 1'b1; assign adc_pdwn_b = 1'b1; assign adc_dcs = 1'b0; assign adc_dfs = 1'b0;
    assign dac_mode = 1'b1; assign dac_sleep = 1'b1; assign eth_rst_n = 1'b1; assign usb_pullup = 1'b0;

    // ---- UART and the register bus --------------------------------------------------------------------
    wire [7:0] rx_data; wire rx_valid;
    wire [7:0] tx_data; wire tx_start, tx_busy;
    uart_rx #(.DIV(UART_DIV)) urx (.clk(clk), .rx(uart_rx), .data(rx_data), .valid(rx_valid));
    uart_tx #(.DIV(UART_DIV)) utx (.clk(clk), .data(tx_data), .start(tx_start), .busy(tx_busy), .tx(uart_tx));
    wire [6:0]  addr; wire [31:0] wdata; wire we; reg [31:0] rdata;
    wire [15:0] dump_addr; wire [31:0] dump_data; wire bus_active;
    reg  [15:0] dump_len = 0;
    regbus bus (.clk(clk), .rx_data(rx_data), .rx_valid(rx_valid), .tx_data(tx_data), .tx_start(tx_start), .tx_busy(tx_busy),
                .addr(addr), .wdata(wdata), .we(we), .rdata(rdata), .dump_len(dump_len), .dump_addr(dump_addr), .dump_data(dump_data),
                .active(bus_active));

    // ---- the global registers ---------------------------------------------------------------------------
    reg [31:0] scratch = 0;
    reg        clkout_en = 1'b1;
    reg [10:1] leds_r = 0;
    reg [23:0] cap_div = 0;
    reg [CAP_AW+1:0] cap_len = 1 << (CAP_AW + 1);
    reg [15:0] cap_trig = 0;
    reg        restart_all = 0, safe = 0, cap_start = 0, cap_abort = 0;
    always @(posedge clk) begin
        restart_all <= 1'b0; safe <= 1'b0; cap_start <= 1'b0; cap_abort <= 1'b0;
        if (we) case (addr)
            7'h02: scratch <= wdata;
            7'h03: begin clkout_en <= wdata[0]; restart_all <= wdata[8]; safe <= wdata[9]; end
            7'h04: leds_r <= wdata[10:1];
            7'h10: begin cap_start <= wdata[0]; cap_abort <= wdata[1]; end
            7'h11: cap_div <= wdata[23:0];
            7'h12: cap_len <= (wdata == 0) ? 1 : (wdata > (1 << (CAP_AW + 1))) ? (1 << (CAP_AW + 1)) : wdata[CAP_AW+1:0];
            7'h13: cap_trig <= wdata[15:0];
            7'h7e: dump_len <= wdata[15:0];
            default: ;
        endcase
    end

    // ---- the one-second gate of the frequency counters ---------------------------------------------------
    reg [31:0] gate_cnt = 0;
    reg        gate = 0;
    always @(posedge clk) begin
        gate <= 1'b0;
        if (gate_cnt == GATE_CYCLES - 1) begin gate_cnt <= 0; gate <= 1'b1; end
        else gate_cnt <= gate_cnt + 32'd1;
    end

    // ---- the two ports ---------------------------------------------------------------------------------------
    wire [31:0] a_rdata, b_rdata;
    wire [7:0]  a_o, a_oe, a_s, b_o, b_oe, b_s;
    pmod_port pa (.clk(clk), .addr(addr[4:0]), .wdata(wdata), .we(we && addr[6:5] == 2'b01), .rdata(a_rdata),
                  .restart_all(restart_all), .safe(safe), .gate(gate), .pin_i(pmoda), .pin_o(a_o), .pin_oe(a_oe), .pin_s(a_s));
    pmod_port pb (.clk(clk), .addr(addr[4:0]), .wdata(wdata), .we(we && addr[6:5] == 2'b10), .rdata(b_rdata),
                  .restart_all(restart_all), .safe(safe), .gate(gate), .pin_i(pmodb), .pin_o(b_o), .pin_oe(b_oe), .pin_s(b_s));
    genvar i;
    generate for (i = 0; i < 8; i = i + 1) begin : pads
        assign pmoda[i] = a_oe[i] ? a_o[i] : 1'bz;
        assign pmodb[i] = b_oe[i] ? b_o[i] : 1'bz;
    end endgenerate

    // ---- the logic analyser -------------------------------------------------------------------------------
    wire cap_busy, cap_done, cap_trigd; wire [CAP_AW+1:0] cap_count;
    capture #(.AW(CAP_AW)) cap (.clk(clk), .pins({b_s, a_s}), .start(cap_start), .abort(cap_abort), .div(cap_div), .len(cap_len),
                                .trig_mask(cap_trig), .busy(cap_busy), .done(cap_done), .trig(cap_trigd), .count(cap_count),
                                .dump_addr(dump_addr), .dump_data(dump_data));

    always @(*) case (addr[6:5])
        2'b01: rdata = a_rdata;
        2'b10: rdata = b_rdata;
        default: case (addr)
            7'h00: rdata = 32'h504D4231;
            7'h01: rdata = BUILD_ID;
            7'h02: rdata = scratch;
            7'h03: rdata = {31'b0, clkout_en};
            7'h04: rdata = {21'b0, leds_r, 1'b0};
            7'h05: rdata = GATE_CYCLES;
            7'h06: rdata = {b_oe, a_oe, b_s, a_s};
            7'h11: rdata = {8'b0, cap_div};
            7'h12: rdata = cap_len;
            7'h13: rdata = {16'b0, cap_trig};
            7'h14: rdata = {cap_count, 13'b0, cap_trigd, cap_done, cap_busy} | 32'h0;
            7'h7e: rdata = {16'b0, dump_len};
            default: rdata = 32'hDEAD0000 | {25'b0, addr};
        endcase
    endcase

    // ---- LEDs and CLK OUT -------------------------------------------------------------------------------------
    reg [23:0] hb = 0;
    always @(posedge clk) hb <= hb + 24'd1;
    assign led0 = hb[23];                                    // 25 MHz / 2^24 = 1.5 Hz: the bitstream is alive
    assign {led7, led6, led5, led4, led3, led2, led1} = leds_r[7:1];
    assign led_r = ~leds_r[8]; assign led_g = ~leds_r[9]; assign led_b = ~leds_r[10];      // common anode: 0 lights
    assign clk_out = clkout_en ? clk_tcxo : 1'b0;
endmodule
`default_nettype wire
