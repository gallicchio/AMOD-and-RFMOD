// The bench both testbenches share (included inside the testbench module): the 25 MHz TCXO, the design, a
// tile socket on each Pmod, and the PC's side of the UART as tasks.  A floating Pmod line reads 0 here (a
// weak keeper, weaker than the tiles' own pull resistors); the frequency counters' gate is 1 ms.
    localparam real BIT = 1000.0;                               // 1 Mbaud
    localparam [3:0] NONE = 0, AMOD_A = 1, AMOD_N = 2, AMOD_C = 3, AMOD_M = 4, AMOD_B = 5, RF_MOD = 6, PHMOD = 7, IQ_MOD = 8, SPI_JIG = 9, LOOP_JIG = 10;
    localparam [6:0] PA = 7'h20, PB = 7'h40;                     // the ports' bases, and their registers' offsets
    localparam [6:0] R_OUT = 0, R_OE = 1, R_IN = 2, R_SET = 3, R_CLR = 4, R_SRC = 5, R_GEN = 6, R_SPICFG = 7, R_SPI = 8, R_STAT = 9,
                     R_SAMP = 10, R_ONES = 11, R_SEQ = 12, R_MEAS = 13, R_FREQ = 14, R_QUAD = 15, R_G1 = 16;
    reg clk_tcxo = 0; always #20 clk_tcxo = ~clk_tcxo;
    reg uart_rx = 1; wire uart_tx;
    wire clk_out; wire [7:0] leds; wire led_r, led_g, led_b;
    wire adc_pdwn_a, adc_pdwn_b, adc_dcs, adc_dfs, dac_mode, dac_sleep, eth_rst_n, usb_pullup;
    wire [7:0] pmoda, pmodb;
    reg  [3:0] board_a = NONE, board_b = NONE;
    pmodbench #(.UART_DIV(25), .GATE_CYCLES(25000), .BUILD_ID(32'h20261115)) dut (
        .clk_tcxo(clk_tcxo), .clk_out(clk_out),
        .led0(leds[0]), .led1(leds[1]), .led2(leds[2]), .led3(leds[3]), .led4(leds[4]), .led5(leds[5]), .led6(leds[6]), .led7(leds[7]),
        .led_r(led_r), .led_g(led_g), .led_b(led_b), .uart_rx(uart_rx), .uart_tx(uart_tx),
        .adc_pdwn_a(adc_pdwn_a), .adc_pdwn_b(adc_pdwn_b), .adc_dcs(adc_dcs), .adc_dfs(adc_dfs), .dac_mode(dac_mode), .dac_sleep(dac_sleep),
        .eth_rst_n(eth_rst_n), .usb_pullup(usb_pullup), .pmoda(pmoda), .pmodb(pmodb));
    tile_socket sa (.io(pmoda), .board(board_a), .host_oe(dut.pa.pin_oe));
    tile_socket sb (.io(pmodb), .board(board_b), .host_oe(dut.pb.pin_oe));
    genvar gk;
    generate for (gk = 0; gk < 8; gk = gk + 1) begin : keeper
        assign (weak1, weak0) pmoda[gk] = 1'b0;
        assign (weak1, weak0) pmodb[gk] = 1'b0;
    end endgenerate

    // send_byte returns as the stop bit begins (and lets the line idle one bit before the next start)
    realtime t_sent = 0;
    task send_byte(input [7:0] b); integer i; begin
        if ($realtime - t_sent < BIT) #(BIT - ($realtime - t_sent));
        uart_rx = 0; #(BIT);
        for (i = 0; i < 8; i = i + 1) begin uart_rx = b[i]; #(BIT); end
        uart_rx = 1; t_sent = $realtime;
    end endtask
    task wr(input [6:0] a, input [31:0] d); begin
        send_byte({1'b1, a}); send_byte(d[7:0]); send_byte(d[15:8]); send_byte(d[23:16]); send_byte(d[31:24]);
        #(BIT * 1.2);                                           // the board acts on a write half a bit into the stop bit
    end endtask
