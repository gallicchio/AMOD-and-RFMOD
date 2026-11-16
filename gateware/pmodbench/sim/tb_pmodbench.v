// Self-checking testbench for pmodbench: the PC's side of the UART as tasks, a tile socket with the
// models of the tiles' chips on each Pmod (tiles.v, models.v).  `make sim` runs it; it ends with PASS
// or the count of failures.  The frequency counters' gate is 1 ms here.  The MAX2871 words are those
// host/max2871.py prints for 915 MHz at +5 dBm; the TRF3722 word is host/trf3722.py's register 1.
`timescale 1ns/1ps
module tb_pmodbench;
`include "bench.vh"
    task recv_byte(output [7:0] b); integer i; begin
        if (uart_tx !== 1'b0) @(negedge uart_tx);
        #(BIT * 1.5);
        for (i = 0; i < 8; i = i + 1) begin b[i] = uart_tx; #(BIT); end
    end endtask
    task rd(input [6:0] a, output [31:0] d); reg [7:0] b0, b1, b2, b3; begin
        send_byte({1'b0, a}); recv_byte(b0); recv_byte(b1); recv_byte(b2); recv_byte(b3); d = {b3, b2, b1, b0};
    end endtask
    reg [31:0] dump [0:8191];
    task dump_words(input integer n); integer i; reg [7:0] b0, b1, b2, b3; begin
        wr(7'h7e, n); send_byte(8'h7f);
        for (i = 0; i < n; i = i + 1) begin recv_byte(b0); recv_byte(b1); recv_byte(b2); recv_byte(b3); dump[i] = {b3, b2, b1, b0}; end
    end endtask
    function [15:0] sample(input integer i); sample = i[0] ? dump[i >> 1][31:16] : dump[i >> 1][15:0]; endfunction

    integer fails = 0, checks = 0;
    task check(input [799:0] what, input ok); begin
        checks = checks + 1;
        if (ok !== 1'b1) begin fails = fails + 1; $display("FAIL: %0s at %t", what, $time); end
        else $display("  ok: %0s", what);
    end endtask

    // ---- SPI through the engine, as the driver does it --------------------------------------------------
    reg [31:0] v, v2, raw;
    task spi_cfg(input [6:0] base, input integer nbits, input lsb, input cpol, input cpha, input integer miso_io, input late, input integer half); begin
        wr(base + R_SPICFG, (nbits - 1) | (lsb << 5) | (cpol << 6) | (cpha << 7) | ((miso_io - 1) << 8) | (late << 11) | (half << 16));
    end endtask
    task spi_xfer(input [6:0] base, input [31:0] w, output [31:0] r); reg [31:0] st; begin
        wr(base + R_SPI, w);
        st = 1; while (st[0]) rd(base + R_STAT, st);
        rd(base + R_SPI, r);
    end endtask
    task max_word(input [31:0] w); reg [31:0] r; begin                     // RF-MOD in Pmod A: LE on IO4
        spi_xfer(PA, w, r); wr(PA + R_SET, 8'h08); wr(PA + R_CLR, 8'h08);
    end endtask
    task trf_word(input [31:0] w); reg [31:0] r; begin                     // LE on IO6
        spi_xfer(PA, w, r); wr(PA + R_SET, 8'h20); wr(PA + R_CLR, 8'h20);
    end endtask
    task trf_read(input integer n, output [31:0] w); reg [31:0] r; begin
        spi_cfg(PA, 32, 1, 0, 0, 5, 0, 24);
        spi_xfer(PA, 32'h80000008 | (n << 28), r); wr(PA + R_SET, 8'h20);
        spi_cfg(PA, 1, 1, 0, 0, 5, 0, 24); spi_xfer(PA, 0, r);             // the idle clock, LE still high
        wr(PA + R_CLR, 8'h20);
        spi_cfg(PA, 32, 1, 0, 1, 5, 0, 24); spi_xfer(PA, 0, w);            // 32 clocks, RDBK read at each falling edge
        spi_cfg(PA, 32, 1, 0, 0, 5, 0, 24);
    end endtask
    function [5:0] crc6(input [17:0] d); integer i; reg [5:0] c; reg fb; begin
        c = 0;
        for (i = 17; i >= 0; i = i - 1) begin fb = c[5] ^ d[i]; c = {c[4:0], 1'b0} ^ (fb ? 6'h03 : 6'h00); end
        crc6 = c;
    end endfunction
    function [31:0] inc_of(input real f); inc_of = $rtoi(f / 25.0e6 * 4294967296.0 + 0.5); endfunction
    task gen_set(input [6:0] base, input integer n, input [31:0] inc, input [31:0] duty, input [31:0] phase, input [31:0] burst); begin
        wr(base + R_G1 + 4 * (n - 1), inc); wr(base + R_G1 + 4 * (n - 1) + 1, duty);
        wr(base + R_G1 + 4 * (n - 1) + 2, phase); wr(base + R_G1 + 4 * (n - 1) + 3, burst);
    end endtask

    // ---- the tests ----------------------------------------------------------------------------------------
    integer i, k, m, n, errs, mode, lsbf, cse, nb, hf, n0;
    realtime t1, t2, avg;
    reg [31:0] seq0, mask, word, exp_w;
    reg [31:0] maxw [0:12];
    real dens;
    integer cedges = 0; always @(posedge clk_out) cedges = cedges + 1;
    initial begin
`ifdef VCD
        $dumpfile("tb_pmodbench.vcd"); $dumpvars(0, tb_pmodbench);
`endif
        #5000;
        // ---- 1. power-up, the board's other pins, the global registers
        check("power-up: every Pmod pin is high-Z", dut.pa.pin_oe === 8'h00 && dut.pb.pin_oe === 8'h00);
        check("the board's other pins are where blink.v leaves them (ADC down, DAC asleep, PHY out of reset, USB pull-up off)",
              adc_pdwn_a === 1'b1 && adc_pdwn_b === 1'b1 && adc_dcs === 1'b0 && adc_dfs === 1'b0 && dac_mode === 1'b1 && dac_sleep === 1'b1 &&
              eth_rst_n === 1'b1 && usb_pullup === 1'b0);
        cedges = 0; #4000; check("CLK OUT carries the 25 MHz TCXO", cedges == 100);
        rd(7'h00, v); check("ID = 0x504D4231, not the host design's 0xEC5BA2D2", v == 32'h504D4231);
        rd(7'h01, v); check("VERSION is the build date", v == 32'h20261115);
        wr(7'h02, 32'hCAFE1234); rd(7'h02, v); check("SCRATCH reads back", v == 32'hCAFE1234);
        rd(7'h05, v); check("GATE = the gate in clocks (25000 here)", v == 25000);
        rd(7'h33 + 7'h40, v); check("an unmapped register answers DEAD00xx", v == 32'hDEAD0073);
        wr(7'h04, 32'h5AA); #200;
        check("LEDS: LED1-7 from the register, RGB active low, LED0 the heartbeat",
              leds[7:1] === 7'b1010101 && led_r === 1'b0 && led_g === 1'b1 && led_b === 1'b0 && leds[0] === dut.hb[23]);
        wr(7'h03, 0); cedges = 0; #2000; check("CONTROL[0] = 0 holds CLK OUT low", cedges == 0 && clk_out === 1'b0);
        wr(7'h03, 1);

        // ---- 2. plain pins: the loopback jig on Pmod A (IO1-4 buffered onto IO5-8)
        board_a = LOOP_JIG;
        wr(PA + R_OUT, 8'h05); wr(PA + R_OE, 8'h0F); #300;
        rd(PA + R_IN, v); check("OUT and OE drive IO1-4, IN reads all eight (and what is driven, and the enables)", v == 32'h000F0555);
        wr(PA + R_SET, 8'h0A); wr(PA + R_CLR, 8'h03); #300;
        rd(PA + R_IN, v); check("OUT_SET and OUT_CLR", v[7:0] == 8'hCC);
        rd(PA + R_OUT, v); check("OUT reads back", v == 32'h0000000C);
        rd(7'h06, v); check("PINS shows both ports; port B untouched", v == 32'h000F00CC && dut.pb.pin_oe === 8'h00);
        check("no contention so far", sa.contention == 0);
        wr(PA + R_OE, 8'h1F); #300;
        check("the bench notices the FPGA enabling a pin the tile drives (IO5)", sa.contention == 1 && sa.clash_pins == 8'b0001_0000);
        wr(PA + R_OE, 16'hF0FF); #300;
        rd(PA + R_IN, v); check("LOCK keeps IO5-8 undriven whatever OE says", dut.pa.pin_oe === 8'h0F && v[23:16] == 8'h0F);
        wr(7'h03, 32'h201); #300;
        rd(PA + R_OE, v); rd(PA + R_OUT, v2);
        check("CONTROL SAFE: every pin high-Z, OUT cleared, the locks kept", dut.pa.pin_oe === 8'h00 && v == 32'h0000F000 && v2 == 0);
        board_a = NONE; wr(PA + R_OE, 16'h00FF);

        // ---- 3. the generators (nothing in the sockets: the meters on the bare pins)
        gen_set(PA, 1, inc_of(1.0e6), 32'h40000000, 0, 0);                  // 1 MHz, 25 %
        gen_set(PA, 2, inc_of(1.0e6), 32'h40000000, 32'h40000000, 0);       // the same, a quarter period early
        wr(PA + R_SRC, 32'h00000521);                                       // IO1 gen 1, IO2 gen 2, IO3 gen 1 inverted
        wr(PA + R_GEN, 12'h303); sa.clear; #200000;
        check("generator: 1 MHz is 25 clocks a period, exactly", sa.m_minp[1] == 1000.0 && sa.m_maxp[1] == 1000.0 && sa.m_rises[1] >= 199);
        check("generator: 25 % duty is 6 or 7 clocks high", sa.m_minh[1] >= 240.0 && sa.m_maxh[1] <= 280.0);
        t1 = sa.m_trise[2] - sa.m_trise[1]; while (t1 < 0) t1 = t1 + 1000.0; while (t1 >= 1000.0) t1 = t1 - 1000.0;
        check("generator: PHASE 2^30 puts generator 2 a quarter period ahead of generator 1", t1 >= 720.0 && t1 <= 780.0);
        errs = 0; for (i = 0; i < 200; i = i + 1) begin @(negedge clk_tcxo); if (pmoda[2] !== ~pmoda[0]) errs = errs + 1; end
        check("generator: the inverted source is the complement while the generator runs", errs == 0);
        wr(PA + R_GEN, 4'h2); #500; check("generator: disabled, its true and its inverted outputs are both low", pmoda[0] === 1'b0 && pmoda[2] === 1'b0);
        gen_set(PA, 1, inc_of(1.0e6), 32'hFFFFFFFF, 0, 0); wr(PA + R_GEN, 4'h1); sa.clear; #50000;
        check("generator: DUTY 0xFFFFFFFF is always high", pmoda[0] === 1'b1 && sa.m_falls[1] == 0);
        gen_set(PA, 1, inc_of(1.0e6), 32'h00000000, 0, 0); sa.clear; #50000;
        check("generator: DUTY 0 is always low", pmoda[0] === 1'b0 && sa.m_rises[1] == 0);
        gen_set(PA, 1, inc_of(1234567.0), 32'h80000000, 0, 0); wr(PA + R_GEN, 12'h101); #3000; sa.clear;
        @(posedge pmoda[0]); t1 = $realtime; #1; n0 = sa.m_rises[1]; #400000; t2 = sa.m_trise[1]; avg = (t2 - t1) / (sa.m_rises[1] - n0);
        check("generator: 1.234567 MHz to 0.1 % over 400 us, each period within a clock of it",
              avg > 810.0005 * 0.999 && avg < 810.0005 * 1.001 && sa.m_minp[1] >= 800.0 && sa.m_maxp[1] <= 840.0);
        // bursts on AMOD-A's bridge: IO3 (IN1) inverted, IO4 (IN2) true, 8 cycles of 40 kHz in every 20
        wr(PA + R_GEN, 0); wr(PA + R_OE, 16'h510C); board_a = AMOD_A;       // drive IO3, IO4; lock IO1, IO5, IO7; then the tile
        gen_set(PA, 3, inc_of(40.0e3), 32'h80000000, 0, (20 << 16) | 8);
        wr(PA + R_SRC, 32'h00003700);                                       // IO3 gen 3 inverted, IO4 gen 3
        wr(PA + R_GEN, 12'h404); #250000; sa.clear;                         // into the first gap (cycles 8-19 are off)
        errs = (pmoda[3] !== 1'b0 || pmoda[2] !== 1'b0);                    // both low between bursts
        #1000000;
        check("burst: 8 cycles on in every 20, on the true and the inverted output", sa.m_rises[4] == 16 && sa.m_rises[3] == 16);
        check("burst: the gap is 12.5 periods, both outputs low in it, never both high",
              sa.m_maxl[4] >= 312400.0 && sa.m_maxl[4] <= 312600.0 && errs == 0 && sa.hb.overlaps == 0 && sa.hb.edges == 32);
        check("burst: no contention on AMOD-A (IO7 is the tile's)", sa.contention == 1);
        // restart_all: generators of both ports on one clock
        wr(PA + R_GEN, 0); board_a = NONE; wr(PA + R_OE, 16'h00FF); wr(PB + R_OE, 16'h00FF);
        gen_set(PA, 1, inc_of(333333.0), 32'h80000000, 0, 0); gen_set(PB, 1, inc_of(333333.0), 32'h80000000, 0, 0);
        wr(PA + R_SRC, 1); wr(PB + R_SRC, 1); wr(PA + R_GEN, 1); wr(PB + R_GEN, 1);
        #20000; t1 = sa.m_trise[1] - sb.m_trise[1];
        wr(7'h03, 32'h101); #50000;
        check("CONTROL restart: port A's and port B's generators rise on the same clock (they did not before)",
              sa.m_trise[1] == sb.m_trise[1] && t1 != 0);
        wr(PB + R_GEN, 0); wr(PB + R_OE, 0); wr(PB + R_SRC, 0);
        // two non-overlapping phases on AMOD-C's c5: IO4 (phi1) and IO8 (phi2), 101 kHz, at least 5 clocks apart
        wr(PA + R_GEN, 0); wr(PA + R_OE, 16'h42BD); board_a = AMOD_C;        // drive IO1, IO3-6, IO8; lock IO2, IO7
        word = inc_of(101.0e3);
        gen_set(PA, 1, word, 32'h80000000 - 6 * word, 0, 0); gen_set(PA, 2, word, 32'h80000000 - 6 * word, 32'h80000000, 0);
        wr(PA + R_SRC, 32'h20001000);                                       // IO4 gen 1, IO8 gen 2
        wr(PA + R_GEN, 12'h303); #2000; sa.clear; #3000000;
        check("two phases: never high together in 300 periods, at least 200 ns of dead time on each side",
              sa.c5.overlaps == 0 && sa.c5.edges >= 600 && sa.c5.min_gap >= 200.0 && sa.c5.min_gap <= 280.0);
        check("two phases: each is high just under half the period", sa.m_minh[4] >= 4680.0 && sa.m_maxh[4] <= 4760.0 && sa.m_minh[8] >= 4680.0 && sa.m_maxh[8] <= 4760.0);
        // the density meter on c6's bit stream: IO1 clocks the modulator, IO7 is its bit
        sa.c6.level = 0.3;
        gen_set(PA, 3, inc_of(1.0e6), 32'h80000000, 0, 0); wr(PA + R_SRC, 32'h20001003); wr(PA + R_GEN, 12'h407);
        wr(PA + R_SAMP, 6 | (2 << 4) | (10 << 8));
        rd(PA + R_SEQ, seq0); v = seq0; while (v == seq0) begin #200000; rd(PA + R_SEQ, v); end
        rd(PA + R_ONES, v); check("density meter: 0.3 of the modulator's bits are ones (1024 samples)", v >= 305 && v <= 309);
        check("AMOD-C: no contention", sa.contention == 1);
        wr(7'h03, 32'h201); board_a = NONE;

        // ---- 4. the SPI engine against a slave with a set output delay (Pmod B: IO1 MISO, IO2 MOSI, IO3 SCK, IO4 CS)
        board_b = SPI_JIG; wr(PB + R_OUT, 8'h08); wr(PB + R_OE, 16'hF10E); wr(PB + R_SRC, 32'h000009A0);
        for (mode = 0; mode < 4; mode = mode + 1) begin
            errs = 0;
            for (lsbf = 0; lsbf < 2; lsbf = lsbf + 1) for (cse = 0; cse < 5; cse = cse + 1) begin
                case (cse) 0: begin nb = 8; hf = 24; sb.jig.tco = 30.0; end
                           1: begin nb = 13; hf = 3; sb.jig.tco = 100.0; end
                           2: begin nb = 32; hf = 1; sb.jig.tco = 70.0; end      // valid only 10 ns before the sampling edge leaves
                           3: begin nb = 32; hf = 0; sb.jig.tco = 30.0; end      // 12.5 MHz
                           default: begin nb = 1; hf = 2; sb.jig.tco = 30.0; end
                endcase
                sb.jig.cpol = mode[1]; sb.jig.cpha = mode[0]; sb.jig.lsb = lsbf; sb.jig.nbits = nb;
                sb.jig.tx = 32'hA5C3F00D ^ {mode[1:0], 3'b0, lsbf[0], cse[2:0], 23'h1234AB};
                mask = nb == 32 ? 32'hFFFFFFFF : (32'h1 << nb) - 1;
                word = 32'h3C5A9612 ^ {cse[2:0], 29'h0F00F00};
                spi_cfg(PB, nb, lsbf, mode[1], mode[0], 1, 0, hf);
                wr(PB + R_CLR, 8'h08); spi_xfer(PB, word & mask, raw); wr(PB + R_SET, 8'h08);
                if (lsbf) raw = raw >> (32 - nb);
                if ((raw & mask) !== (sb.jig.tx & mask) || (sb.jig.rx & mask) !== (word & mask)) begin
                    errs = errs + 1;
                    $display("    SPI mode %0d lsb %0d case %0d: got %08x want %08x; slave got %08x want %08x", mode, lsbf, cse, raw & mask, sb.jig.tx & mask, sb.jig.rx & mask, word & mask);
                end
            end
            case (mode)
            0: check("SPI mode 0: 1 to 32 bits, either order, 500 kHz to 12.5 MHz, both directions", errs == 0);
            1: check("SPI mode 1: the same", errs == 0);
            2: check("SPI mode 2: the same", errs == 0);
            default: check("SPI mode 3: the same", errs == 0);
            endcase
        end
        check("SPI jig: no contention", sb.contention == 0);
        wr(7'h03, 32'h201); board_b = NONE;

        // ---- 5. RF-MOD in Pmod A: the MAX2871 (LE IO4, MUXOUT IO1) and the TRF3722 (LE IO6, RDBK IO5) on one SCLK / SDATA
        maxw[0] = 32'h61400005; maxw[1] = 32'h61AF425C; maxw[2] = 32'h010007D3; maxw[3] = 32'h18004E42; maxw[4] = 32'h20008029; maxw[5] = 32'h00490010;
        for (i = 0; i < 6; i = i + 1) maxw[6 + i] = maxw[i];
        maxw[12] = 32'h61AF427C;
        spi_cfg(PA, 32, 0, 0, 0, 1, 0, 24);
        board_a = RF_MOD; wr(PA + R_OUT, 0); wr(PA + R_OE, 16'hD12E); wr(PA + R_SRC, 32'h000009A0);
        for (i = 0; i < 12; i = i + 1) max_word(maxw[i]);                   // twice, but with no pause
        #400000; rd(PA + R_IN, v);
        check("MAX2871 model: programmed twice without the 20 ms pause, it does not lock (MUXOUT low)", v[0] == 1'b0 && sa.max.passes == 2 && sa.max.n == 12);
        max_word(maxw[0]); #20000000;                                       // the datasheet's sequence: 5, 20 ms, 4 (off) 3 2 1 0,
        for (i = 1; i < 6; i = i + 1) max_word(maxw[i]);
        #20000000;                                                          // 20 ms, all six again,
        for (i = 6; i < 12; i = i + 1) max_word(maxw[i]);
        #400000; rd(PA + R_IN, v);
        check("MAX2871: after the power-up sequence MUXOUT (digital lock detect) reads high on IO1", v[0] == 1'b1 && sa.max.locked);
        max_word(maxw[12]);                                                 // then register 4 with RFOUTA on
        errs = 0; for (i = 0; i < 13; i = i + 1) if (sa.max.log[12 + i] !== maxw[i]) errs = errs + 1;
        check("MAX2871: the 13 words arrive MSB first, each latched on LE's rising edge", errs == 0 && sa.max.n == 25 && sa.max.bad_len == 0);
        check("MAX2871: the words decode to 915 MHz (3660 MHz / 4), RFOUTB never enabled, no timing violation",
              sa.max.f_out > 914.9999e6 && sa.max.f_out < 915.0001e6 && sa.max.rfb_on == 0 && sa.max.viol == 0 && sa.max.r[4][5]);
        n0 = sa.max.n;
        spi_cfg(PA, 32, 1, 0, 0, 5, 0, 24);                                 // the TRF3722: LSB first
        trf_word(32'h78100029);
        check("TRF3722: a word sent LSB first lands in the register its address bits name", sa.trf.r[1] === 32'h78100029 && sa.trf.writes == 1 && sa.trf.bad_addr == 0);
        trf_read(1, v); check("TRF3722: readback of register 1 (one idle clock, then 32, LSB first)", v == 32'h78100029);
        trf_read(5, v); check("TRF3722: readback of register 5's reset value", v == 32'hAA2AA28D);
        trf_read(0, v); check("TRF3722: readback of register 0 (chip ID, calibration result)", v == 32'h00500028 && sa.trf.readbacks == 3);
        check("TRF3722: no timing violation; the MAX2871 latched nothing meanwhile and is still locked", sa.trf.viol == 0 && sa.trf.short_words == 0 && sa.max.n == n0 && sa.max.locked);
        check("RF-MOD: no contention", sa.contention == 1);
        wr(7'h03, 32'h201); board_a = NONE;

        // ---- 6. AMOD-N in Pmod B: the PE43711 (SI IO2, CLK IO3, LE IO4 with its pull-up)
        board_b = AMOD_N; #300; rd(PB + R_IN, v);
        check("PE43711: released, LE reads high (the tile's 100 k pull-up)", v[3] == 1'b1);
        spi_cfg(PB, 8, 1, 0, 0, 1, 0, 24);                                  // (first: SCK idles at CPOL, and the last user left it high)
        wr(PB + R_OUT, 0); wr(PB + R_OE, 16'hF10E); wr(PB + R_SRC, 32'h000009A0);
        spi_xfer(PB, 8'd50, raw); wr(PB + R_SET, 8'h08); wr(PB + R_CLR, 8'h08);
        check("PE43711: 12.5 dB = 50, eight bits LSB first while LE is low, latched on LE's rising edge",
              sb.pe.att == 8'd50 && sb.pe.latches == 1 && sb.pe.viol == 0 && sb.pe.bad_len == 0 && sb.pe.bad_d7 == 0 && sb.pe.clk_while_le == 0);
        wr(PB + R_SET, 8'h08); spi_xfer(PB, 8'd4, raw);
        check("PE43711 model: it notices clocks sent while LE is high", sb.pe.clk_while_le == 8);
        wr(7'h03, 32'h201); board_b = NONE;

        // ---- 7. AMOD-B in Pmod B: the MT6701's SSI and the LSM6DSO on one SCK / MISO
        // (the pins first, the tile second: with the pins floating both chip selects are undefined, see the README)
        spi_cfg(PB, 24, 0, 1, 1, 3, 1, 24);
        wr(PB + R_OUT, 8'hA8); wr(PB + R_SRC, 32'h0A009000); wr(PB + R_OE, 16'h04FB);       // SCK IO4 (idle high), MOSI IO7, both CS high
        board_b = AMOD_B; #300;
        sb.mt.angle = 14'h1A5C; sb.mt.status = 4'b0010;
        wr(PB + R_CLR, 8'h20); spi_xfer(PB, 0, raw); wr(PB + R_SET, 8'h20);
        check("MT6701: 24 clocks, each bit taken half a period after the rising edge that launched it", raw[23:0] === sb.mt.sent && sb.mt.nclk == 24 && sb.mt.mode_viol == 0);
        check("MT6701: angle, status and a CRC that checks", raw[23:10] == 14'h1A5C && raw[9:6] == 4'b0010 && raw[5:0] == crc6(raw[23:6]));
        spi_cfg(PB, 24, 0, 1, 1, 3, 0, 24);
        wr(PB + R_CLR, 8'h20); spi_xfer(PB, 0, raw); wr(PB + R_SET, 8'h20);
        check("MT6701: without the late sample (plain mode 3) every bit is one clock stale", raw[23:0] === {1'b1, sb.mt.sent[23:1]});
        spi_cfg(PB, 16, 0, 1, 1, 3, 0, 24);
        wr(PB + R_CLR, 8'h80); spi_xfer(PB, 16'h8F00, raw); wr(PB + R_SET, 8'h80);
        check("LSM6DSO: WHO_AM_I (0x0F) reads 0x6C in SPI mode 3", raw[7:0] == 8'h6C && sb.imu.mode_viol == 0 && sb.imu.frames == 1);
        check("AMOD-B: the two chip selects were never low together", sb.cs_fight == 0 && sb.contention == 0);
        wr(PB + R_CLR, 8'hA0); #300;
        check("AMOD-B bench: it notices both chip selects low", sb.cs_fight == 1);
        wr(7'h03, 32'h201); board_b = NONE;

        // ---- 8. AMOD-A in Pmod A: the first-order delta-sigma loop round a6 (bit on IO7, feedback on IO8)
        board_a = AMOD_A; wr(PA + R_OE, 16'h5180); wr(PA + R_SRC, 32'hC0000000);     // IO8 = the registered bit, inverted
        gen_set(PA, 1, inc_of(1.0e6), 32'h80000000, 0, 0); wr(PA + R_GEN, 12'h101);
        for (k = 0; k < 3; k = k + 1) begin
            sa.a6.vin = 0.825 * (k + 1);
            wr(PA + R_SAMP, 6 | (0 << 4) | (11 << 8));
            rd(PA + R_SEQ, seq0); v = seq0; while (((v - seq0) & 16'hFFFF) < 2) begin #500000; rd(PA + R_SEQ, v); end
            rd(PA + R_ONES, v); dens = v / 2048.0;
            $display("    delta-sigma: IN %0.3f V, ones density %0.4f (IN / 3.3 V = %0.4f)", sa.a6.vin, dens, sa.a6.vin / 3.3);
            case (k)
            0: check("delta-sigma loop: IN 0.825 V gives a ones density of 0.25", dens > 0.24 && dens < 0.26);
            1: check("delta-sigma loop: IN 1.65 V gives 0.50", dens > 0.49 && dens < 0.51);
            default: check("delta-sigma loop: IN 2.475 V gives 0.75", dens > 0.74 && dens < 0.76);
            endcase
        end
        wr(PA + R_SRC, 32'hB0000000); wr(PA + R_SAMP, 6 | (11 << 8));       // the bit fed back true: positive feedback
        rd(PA + R_SEQ, seq0); v = seq0; while (((v - seq0) & 16'hFFFF) < 2) begin #500000; rd(PA + R_SEQ, v); end
        rd(PA + R_ONES, v); check("delta-sigma loop: with the feedback not inverted the loop latches up (density 0 or 1)", v < 20 || v > 2028);
        rd(PA + R_STAT, v); check("STATUS shows the sampler's registered bit", v[1] === dut.pa.samp_bit && v[1] === (sa.a6.v > 1.65));
        check("AMOD-A: no contention", sa.contention == 1);
        wr(7'h03, 32'h201); board_a = NONE;

        // ---- 9. the frequency counter (loopback jig) and the quadrature decoder (AMOD-M's encoder)
        board_a = LOOP_JIG; wr(PA + R_OE, 16'hF001); wr(PA + R_SRC, 1);
        gen_set(PA, 1, inc_of(1.0e6), 32'h80000000, 0, 0); wr(PA + R_GEN, 12'h101);
        wr(PA + R_MEAS, 4 | (4 << 4) | (5 << 8));                           // count IO5
        rd(PA + R_STAT, seq0); v = seq0; while (((v[15:8] - seq0[15:8]) & 8'hFF) < 2) begin #300000; rd(PA + R_STAT, v); end
        rd(PA + R_FREQ, v); check("frequency counter: 1 MHz on IO5 reads 1000 in a 1 ms gate", v >= 999 && v <= 1001);
        wr(7'h03, 32'h201); board_a = NONE;
        board_b = AMOD_M; wr(PB + R_OE, 16'h3000); wr(PB + R_MEAS, 0 | (4 << 4) | (5 << 8) | (1 << 16));
        sb.enc.step_ns = 2000.0; sb.enc.steps = 1000; #2100000;
        rd(PB + R_QUAD, v); check("quadrature: 1000 quarter-cycles up count +1000", v == 32'd1000);
        sb.enc.steps = -300; #700000;
        rd(PB + R_QUAD, v); rd(PB + R_STAT, v2); check("quadrature: 300 down leave 700, no errors", v == 32'd700 && v2[31:16] == 0);
        sb.enc.steps = -1000; #2100000;
        rd(PB + R_QUAD, v); check("quadrature: the count is signed (-300)", v == 32'hFFFFFED4);
        sb.enc.glitch; #1000;
        rd(PB + R_QUAD, v); rd(PB + R_STAT, v2); check("quadrature: both lines changing at once is an error, not a count", v == 32'hFFFFFED4 && v2[31:16] == 1);
        wr(PB + R_MEAS, 0 | (4 << 4) | (5 << 8) | (1 << 16)); rd(PB + R_QUAD, v); rd(PB + R_STAT, v2);
        check("quadrature: the clear bit zeroes the count and the errors", v == 0 && v2[31:16] == 0 && sb.contention == 0);
        wr(7'h03, 32'h201); board_b = NONE;

        // ---- 10. the logic analyser
        wr(PA + R_OE, 16'h0001); wr(PA + R_SRC, 1); wr(PB + R_OUT, 8'hA5); wr(PB + R_OE, 16'h00FF);
        gen_set(PA, 1, 32'h40000000, 32'h80000000, 0, 0); wr(PA + R_GEN, 12'h101);          // 6.25 MHz: two clocks high, two low
        wr(7'h11, 0); wr(7'h12, 64); wr(7'h13, 0); wr(7'h10, 1); #10000;
        rd(7'h14, v); check("capture: 64 samples at 25 MS/s, done", v == {1'b0, 15'd64, 13'b0, 3'b110});
        dump_words(32);
        errs = 0; for (i = 0; i < 60; i = i + 1) begin
            if (sample(i) >> 8 != 8'hA5) errs = errs + 1;
            if ((sample(i) & 1) != (sample(i + 4) & 1)) errs = errs + 1;
            if (((sample(i) & 1) + (sample(i + 1) & 1) + (sample(i + 2) & 1) + (sample(i + 3) & 1)) != 2) errs = errs + 1;
        end
        check("capture: port B's byte and port A's 6.25 MHz clock, sample by sample, through the dump stream", errs == 0);
        gen_set(PA, 1, inc_of(1.0e6), 32'h80000000, 0, 0); wr(PA + R_GEN, 12'h101);
        wr(7'h11, 4); wr(7'h12, 61); wr(7'h10, 1); #20000;
        rd(7'h14, v); dump_words(31);
        errs = 0; n = 0; for (i = 0; i < 55; i = i + 1) begin if ((sample(i) & 1) != (sample(i + 5) & 1)) errs = errs + 1; n = n + (sample(i) & 1); end
        check("capture: with div = 4 a 1 MHz clock repeats every 5 samples; an odd length", errs == 0 && n >= 20 && n <= 35 && v[30:16] == 61 && v[1]);
        wr(PA + R_GEN, 0);
        wr(7'h11, 0); wr(7'h12, 5); wr(7'h13, 16'h0100); wr(7'h10, 1); #100000;
        rd(7'h14, v); check("capture: with a trigger mask it waits for a change on that pin", v[2:0] == 3'b001 && v[30:16] == 0);
        wr(PB + R_CLR, 8'h01); #5000;
        rd(7'h14, v); dump_words(3);
        check("capture: triggered by port B IO1 falling; sample 0 is the pins just before, sample 1 after",
              v[2:0] == 3'b110 && v[30:16] == 5 && sample(0) == 16'hA500 && sample(1) == 16'hA400 && sample(4) == 16'hA400);
        wr(7'h12, 100000); rd(7'h12, v); wr(7'h12, 0); rd(7'h12, v2);
        check("capture: the length is held to 1 .. 16384", v == 16384 && v2 == 1);

        // ---- 11. a last look
        wr(7'h03, 32'h201); #300;
        check("SAFE at the end: every pin high-Z again", dut.pa.pin_oe === 8'h00 && dut.pb.pin_oe === 8'h00);
        $display("%0d checks, %0d failures", checks, fails);
        if (fails == 0) $display("PASS: tb_pmodbench, %0d checks", checks); else $display("FAIL: tb_pmodbench, %0d of %0d checks failed", fails, checks);
        $finish;
    end
    initial begin #400_000_000; $display("FAIL: tb_pmodbench TIMEOUT"); $finish; end
endmodule
