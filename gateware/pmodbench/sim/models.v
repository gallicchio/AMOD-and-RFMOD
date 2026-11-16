// Behavioural models of what the tile boards hang on a Pmod, for iverilog: the serial ports of the
// MAX2871, the PE43711 and the TRF3722, the MT6701's SSI, the LSM6DSO's SPI, AMOD-A's comparator and
// RC integrator, AMOD-C's clocked modulator, a quadrature encoder, a generic SPI slave with a set
// clock-to-output delay, and a non-overlap checker (the pulse meters are in tiles.v).  Each model
// counts what its datasheet forbids in `viol` (and friends) rather than stopping the run.
//
// Where each came from: MAX2871.pdf (SPI timing table, "4-Wire Serial Interface", Tables 3-8),
// PE43711B-Z_C470929.pdf (Figure 2, Figure 3, Tables 5-7), TRF3722IRGZR_C1850395.pdf (section 7.1,
// Tables 5-15) in ../../../datasheets.  The MT6701's and the LSM6DSO's datasheets are NOT in that
// directory: their models follow the task's description (24 clocks: 14-bit angle, 4 status bits, CRC-6;
// WHO_AM_I 0x0F = 0x6C, SPI mode 3) and the author's memory of the parts (CRC polynomial x^6 + x + 1 over
// the first 18 bits; DO changes on SCK's rising edge; the IMU drives SDO on the falling edge), so a
// pass against them proves the driver against this description, not against the silicon.
`timescale 1ns/1ps

// ---------------------------------------------------------------------------------------- MAX2871 --
// 32-bit words, MSB first, shifted on CLK's rising edge while LE is low, latched on LE's rising edge
// into the register the three LSBs name.  MUX follows register 2 bits 28:26 and register 5 bit 18:
// 0000 three-state, 0001 high, 0010 low, 0110 digital lock detect.  "Locked" needs what the datasheet
// asks after power-up: registers 5, 4, 3, 2, 1, 0 in that order, twice, the later pass starting at
// least PAUSE_NS (20 ms) after the one before it began, a VCO frequency of 3-6 GHz from the words, and then
// LOCK_NS for the loop to settle (short here; the part takes about 100 ms with VAS_TEMP set).
module max2871_model #(parameter real LOCK_NS = 200_000.0, PAUSE_NS = 20_000_000.0, REF_HZ = 25.0e6) (
    input wire clk, input wire data, input wire le,
    output wire mux, output wire mux_en
);
    reg  [31:0] sh = 0;
    integer     nclk = 0;
    reg  [31:0] r [0:7];
    reg  [31:0] log [0:255];              // every word latched, in order
    integer     n = 0;                    // how many
    integer     viol = 0, bad_len = 0, rfb_on = 0, passes = 0, want = 5;
    reg         locked = 0, pause_ok = 0;
    realtime    t_clk_r = 0, t_clk_f = 0, t_data = 0, t_le_f = 0, t_le_r = 0, t_pass1 = 0, t_pass2 = 0, t_r5 = 0;
    real        f_vco = 0, f_out = 0, f_pfd = 0;
    integer     i;
    initial for (i = 0; i < 8; i = i + 1) r[i] = 0;

    always @(data) begin
        if (!le && t_clk_r != 0 && $realtime - t_clk_r < 25.0 && $realtime != t_clk_r) viol = viol + 1;     // tDH
        t_data = $realtime;
    end
    always @(negedge le) t_le_f = $realtime;
    always @(negedge clk) begin
        if (!le && $realtime - t_clk_r < 25.0) viol = viol + 1;                                           // tCH
        t_clk_f = $realtime;
    end
    always @(posedge clk) begin
        if (le === 1'b0) begin
            if ($realtime - t_data < 25.0) viol = viol + 1;                                               // tDS
            if (nclk > 0 && $realtime - t_clk_f < 25.0) viol = viol + 1;                                  // tCL
            if (nclk == 0 && $realtime - t_le_f < 20.0) viol = viol + 1;                                  // tLES
            sh = {sh[30:0], data}; nclk = nclk + 1;
        end
        t_clk_r = $realtime;
    end
    always @(negedge le) if ($realtime - t_le_r < 20.0 && t_le_r != 0) viol = viol + 1;                   // tLEW
    always @(posedge le) begin
        t_le_r = $realtime;
        if (nclk != 0) begin
            if (nclk != 32) bad_len = bad_len + 1;
            if ($realtime - t_clk_r < 10.0) viol = viol + 1;                                              // tLEH
            if (n < 256) log[n] = sh;
            n = n + 1;
            if (sh[2:0] <= 3'd5) r[sh[2:0]] = sh;
            if (sh[2:0] == 3'd4 && sh[8]) rfb_on = rfb_on + 1;            // RFOUTB is open on the tiles: never enable it
            // the power-up order: 5 4 3 2 1 0, twice
            if (sh[2:0] == 3'd5 && want != 5) want = 5;               // a 5 always starts a pass
            if ({29'b0, sh[2:0]} == want) begin
                if (want == 5) t_r5 = $realtime;
                if (want == 0) begin
                    passes = passes + 1; want = 5;
                    t_pass1 = t_pass2; t_pass2 = t_r5;                     // this pass's register 5 and the one before's
                    if (passes >= 2) begin pause_ok = (t_pass2 - t_pass1) >= PAUSE_NS; evaluate; end
                end else want = want - 1;
            end else if (sh[2:0] != 3'd4 || passes < 2) want = 5;       // (register 4 alone, to turn the output on, is allowed)
        end
        nclk = 0;
    end
    // f = fPFD x (N + F / M) / 2^DIVA with FB = 1; fPFD = REF x (1 + DBR) / (R x (1 + RDIV2))
    integer  ev = 0;
    reg      lock_pending = 0;
    realtime t_lock_at = 0;
    task evaluate; real nn; begin
        f_pfd = REF_HZ * (1 + r[2][25]) / (r[2][23:14] * (1 + r[2][24]));
        nn = r[0][30:15];
        if (!r[0][31] && r[1][14:3] > 1) nn = nn + (r[0][14:3] * 1.0) / r[1][14:3];
        f_vco = f_pfd * nn;
        f_out = f_vco / (1 << r[4][22:20]);
        ev = ev + 1; locked = 0;
        lock_pending = pause_ok && f_vco >= 3.0e9 && f_vco <= 6.0e9 && r[4][23] && !r[2][5] && r[0][30:15] >= 16;
        t_lock_at = $realtime + LOCK_NS;
    end endtask
    always begin
        if (!lock_pending) @(posedge lock_pending);
        #1000 if (lock_pending && $realtime >= t_lock_at) begin locked = 1; lock_pending = 0; end
    end
    wire [3:0] muxsel = {r[5][18], r[2][28:26]};
    assign mux_en = muxsel != 4'b0000;
    assign mux = muxsel == 4'b0001 ? 1'b1 : muxsel == 4'b0110 ? locked : 1'b0;
endmodule

// ---------------------------------------------------------------------------------------- PE43711 --
// An 8-bit shift register (LSB first, CLK's rising edge, to be loaded while LE is low) and a latch that
// takes it on LE's rising edge.  The word is 4 x dB; bit 7 must be 0.  Power-up: 31.75 dB.
module pe43711_model (input wire si, input wire clk, input wire le);
    reg  [7:0] sh = 8'h7f, att = 8'h7f;
    integer    nclk = 0, latches = 0, viol = 0, bad_len = 0, bad_d7 = 0, clk_while_le = 0;
    realtime   t_clk_r = 0, t_clk_f = 0, t_si = 0, t_le_r = 0;
    always @(si) begin
        if (t_clk_r != 0 && $realtime - t_clk_r < 10.0 && $realtime != t_clk_r) viol = viol + 1;          // TSIH
        t_si = $realtime;
    end
    always @(negedge clk) begin if ($realtime - t_clk_r < 30.0) viol = viol + 1; t_clk_f = $realtime; end   // TCLKH
    always @(posedge clk) begin
        if (le === 1'b1) clk_while_le = clk_while_le + 1;
        if ($realtime - t_si < 10.0) viol = viol + 1;                                                    // TSISU
        if (nclk > 0 && $realtime - t_clk_f < 30.0) viol = viol + 1;                                     // TCLKL
        sh = {si, sh[7:1]}; nclk = nclk + 1;
        t_clk_r = $realtime;
    end
    always @(posedge le) begin
        t_le_r = $realtime;
        if (nclk != 0) begin
            if (nclk != 8) bad_len = bad_len + 1;
            if ($realtime - t_clk_r < 10.0) viol = viol + 1;                                             // TLESU
            if (sh[7]) bad_d7 = bad_d7 + 1;
            att = sh; latches = latches + 1;
        end
        nclk = 0;
    end
    always @(negedge le) if (t_le_r != 0 && $realtime - t_le_r < 30.0) viol = viol + 1;                   // TLEPW
endmodule

// ---------------------------------------------------------------------------------------- TRF3722 --
// 32-bit words, LSB first, read on CLK's rising edge; LE's rising edge loads the register named by
// bits 4:0 (01000 + n; registers 1-6).  A write to register 0 with bit 31 set starts a readback of the
// register in bits 30:28: the first clock after that LE is idle, each of the next 32 rising edges puts
// one bit (LSB first) on RDBK, to be read at the following falling edge.  Reset values: Tables 5-12.
module trf3722_model (input wire clk, input wire data, input wire le, output reg rdbk);
    reg  [31:0] sh = 0;
    integer     nclk = 0;
    reg  [31:0] r [0:7];
    reg  [31:0] log [0:63];
    integer     writes = 0, bad_addr = 0, short_words = 0, readbacks = 0, viol = 0;
    reg         rb = 0;
    integer     rb_n = 0;
    reg  [31:0] rb_word = 0;
    realtime    t_clk_r = 0, t_clk_f = 0, t_data = 0, t_le_r = 0;
    initial begin
        rdbk = 0;
        r[0] = 32'h00500028;              // readback only: chip ID 01, VCO_TRIM 32, VCO_SEL 2 (made up)
        r[1] = 32'h41500029; r[2] = 32'h08A0100A; r[3] = 32'h0000000B;
        r[4] = 32'h4A00F80C; r[5] = 32'hAA2AA28D; r[6] = 32'h5441100E; r[7] = 0;
    end
    always @(data) begin
        if (t_clk_r != 0 && $realtime - t_clk_r < 20.0 && $realtime != t_clk_r) viol = viol + 1;          // th
        t_data = $realtime;
    end
    always @(negedge clk) begin if ($realtime - t_clk_r < 20.0) viol = viol + 1; t_clk_f = $realtime; end
    always @(posedge clk) begin
        if ($realtime - t_data < 20.0) viol = viol + 1;                                                   // tsu1
        if (t_clk_f != 0 && $realtime - t_clk_f < 20.0) viol = viol + 1;
        sh = {data, sh[31:1]}; nclk = nclk + 1;
        t_clk_r = $realtime;
        if (rb) begin
            if (rb_n >= 1 && rb_n <= 32) rdbk <= #10 rb_word[rb_n - 1];                                   // td
            if (rb_n == 33) begin rb = 0; rdbk <= #10 1'b0; end
            rb_n = rb_n + 1;
        end
    end
    always @(posedge le) begin
        t_le_r = $realtime;
        if (nclk != 0) begin
            if ($realtime - t_clk_r < 20.0) viol = viol + 1;                                              // tsu2
            if (nclk < 32) short_words = short_words + 1;
            else if (sh[4:3] != 2'b01 || sh[2:0] == 3'd7) bad_addr = bad_addr + 1;
            else if (sh[2:0] == 3'd0) begin
                if (sh[31]) begin rb = 1; rb_n = 0; rb_word = r[sh[30:28]]; readbacks = readbacks + 1; end
            end else begin
                r[sh[2:0]] = sh;
                if (sh[2:0] == 3'd2) r[2][31] = 1'b0;                     // EN_CAL resets itself
                if (writes < 64) log[writes] = sh;
                writes = writes + 1;
            end
        end
        nclk = 0;
    end
    always @(negedge le) if (t_le_r != 0 && $realtime - t_le_r < 50.0) viol = viol + 1;                   // tw
endmodule

// ----------------------------------------------------------------------------------------- MT6701 --
// SSI: CSN low, then 24 clocks; each rising edge of CLK puts the next bit on DO (TCO later), MSB first:
// angle[13:0], status[3:0], crc[5:0] (x^6 + x + 1 over the 18 bits before it, zero start).  DO idles
// high, so a reader that samples before the first rising edge gets a wrong first bit when the angle's
// MSB is 0.  CLK is expected to idle high.  (No datasheet in the repository: see the header.)
module mt6701_model #(parameter real TCO = 20.0) (input wire csn, input wire clk, output reg dout);
    reg  [13:0] angle = 14'h1A5C;
    reg  [3:0]  status = 4'b0000;
    reg  [23:0] sh = 0, sent = 0;
    integer     nclk = 0, reads = 0, mode_viol = 0;
    function [5:0] crc6(input [17:0] d);
        integer i; reg [5:0] c; reg fb;
        begin
            c = 0;
            for (i = 17; i >= 0; i = i - 1) begin fb = c[5] ^ d[i]; c = {c[4:0], 1'b0} ^ (fb ? 6'h03 : 6'h00); end
            crc6 = c;
        end
    endfunction
    initial dout = 1'b1;
    always @(negedge csn) begin
        sh = {angle, status, crc6({angle, status})}; sent = sh; nclk = 0; reads = reads + 1;
        if (clk !== 1'b1) mode_viol = mode_viol + 1;
    end
    always @(posedge csn) dout <= 1'b1;
    always @(posedge clk) if (csn === 1'b0) begin
        dout <= #(TCO) sh[23]; sh = {sh[22:0], 1'b0}; nclk = nclk + 1;
    end
endmodule

// ---------------------------------------------------------------------------------------- LSM6DSO --
// 4-wire SPI, mode 3: SDI read on SPC's rising edge, SDO changed on its falling edge; the first byte
// is RW (1 = read) and a 7-bit address, the data follow MSB first, the address incrementing.
// WHO_AM_I (0x0F) = 0x6C.  SDO is driven only while CS is low.  (No datasheet in the repository.)
module lsm6dso_model #(parameter real TCO = 15.0) (input wire cs, input wire spc, input wire sdi, output reg sdo, output wire sdo_en);
    reg  [7:0] regs [0:127];
    reg  [7:0] cmd = 0, wsh = 0, osh = 0;
    reg  [6:0] a = 0;
    reg        rw = 0;
    integer    n = 0, i, frames = 0, mode_viol = 0, wr_count = 0;
    initial begin for (i = 0; i < 128; i = i + 1) regs[i] = 8'h00; regs[7'h0f] = 8'h6c; regs[7'h12] = 8'h04; sdo = 1'b1; end
    assign sdo_en = cs === 1'b0;
    always @(negedge cs) begin n = 0; frames = frames + 1; if (spc !== 1'b1) mode_viol = mode_viol + 1; end
    always @(posedge spc) if (cs === 1'b0) begin
        if (n < 8) begin
            cmd = {cmd[6:0], sdi};
            if (n == 7) begin rw = cmd[7]; a = cmd[6:0]; end
        end else if (!rw) begin
            wsh = {wsh[6:0], sdi};
            if (n % 8 == 7) begin regs[a] = wsh; a = a + 1; wr_count = wr_count + 1; end
        end
        n = n + 1;
    end
    always @(negedge spc) if (cs === 1'b0 && n >= 8 && rw) begin
        if (n % 8 == 0) begin osh = regs[a]; a = a + 1; end
        sdo <= #(TCO) osh[7]; osh = {osh[6:0], 1'b0};
    end
endmodule

// --------------------------------------------------------------------- AMOD-A a6: comparator and RC --
// The integrator node: IN through 10 k, the FPGA's feedback bit through 10 k, 10 nF to ground; a TLV3501
// (+IN the node, -IN 1.65 V, 4.5 ns) gives the bit.  `vin` is the voltage on IN.  The loop is closed
// when the feedback is the INVERTED registered bit; the ones-density of the bit is then vin / 3.3 V.
module dsm_a6_model #(parameter real R = 10.0e3, C = 10.0e-9, STEP_NS = 50.0) (input wire en, input wire fb, output reg bit_o);
    real vin = 1.65, v = 1.65, vfb;
    initial bit_o = 0;
    always begin
        if (!en) @(posedge en);                  // (asleep while the tile is not in the socket)
        #(STEP_NS);
        if (en) begin
            vfb = fb === 1'b1 ? 3.3 : 0.0;
            v = v + ((vin - v) + (vfb - v)) / (R * C) * (STEP_NS * 1.0e-9);
            bit_o <= #4.5 (v > 1.65);
        end
    end
endmodule

// ------------------------------------------------------------- AMOD-C c6: a clocked one-bit modulator --
// The modulator closes its own loop on the tile; the FPGA only clocks its register (IO1) and reads the
// bit (IO7).  A first-order stand-in: the density of ones is `level` (0 to 1).
module dsm_clocked_model #(parameter real TCO = 6.0) (input wire clk, output reg bit_o);
    real level = 0.5, integ = 0.0;
    initial bit_o = 0;
    always @(posedge clk) begin
        integ = integ + level;
        if (integ >= 1.0) begin integ = integ - 1.0; bit_o <= #(TCO) 1'b1; end
        else bit_o <= #(TCO) 1'b0;
    end
endmodule

// ------------------------------------------------------------------------- a quadrature encoder --
// `steps` (signed) quarter-cycles, one every `step_ns`; up means A leads B.  `glitch` flips both lines.
module quad_encoder_model (output reg a, output reg b);
    integer steps = 0, pos = 0;
    real    step_ns = 2000.0;
    initial begin a = 0; b = 0; end
    always begin
        if (steps == 0) @(steps);
        #(step_ns);
        if (steps > 0) begin pos = pos + 1; steps = steps - 1; end
        else if (steps < 0) begin pos = pos - 1; steps = steps + 1; end
        case (pos & 3) 0: {b, a} = 2'b00; 1: {b, a} = 2'b01; 2: {b, a} = 2'b11; default: {b, a} = 2'b10; endcase
    end
    task glitch; begin {b, a} = ~{b, a}; pos = pos + 2; end endtask
endmodule

// ------------------------------------------------------- a generic SPI slave with a set output delay --
// For the SPI engine's own tests: any mode, either bit order, `nbits` long.  It sends `tx` and records
// what it received in `rx`; its output changes TCO after the shifting edge and is the WRONG value
// (the complement of the coming bit) until then, so a master that samples early reads garbage.
module spi_slave_model (input wire sck, input wire mosi, input wire cs_n, output reg miso);
    reg         cpol = 0, cpha = 0, lsb = 0;
    integer     nbits = 32, n = 0, frames = 0;
    real        tco = 30.0;
    reg  [31:0] tx = 32'hA5C3F00D, rx = 0, osh = 0;
    wire        lead = sck ^ cpol;            // 1 after the leading edge
    initial miso = 0;
    task put; begin miso = lsb ? ~osh[0] : ~osh[nbits - 1]; miso <= #(tco) (lsb ? osh[0] : osh[nbits - 1]); osh = lsb ? osh >> 1 : osh << 1; end endtask
    always @(negedge cs_n) begin n = 0; rx = 0; osh = tx; frames = frames + 1; if (!cpha) put; end
    always @(posedge lead) if (cs_n === 1'b0) begin
        if (cpha) put;                         // CPHA 1: shift out on the leading edge
        else begin if (lsb) rx[n] = mosi; else rx = {rx[30:0], mosi}; n = n + 1; end
    end
    always @(negedge lead) if (cs_n === 1'b0) begin
        if (!cpha) begin if (n < nbits) put; end
        else begin if (lsb) rx[n] = mosi; else rx = {rx[30:0], mosi}; n = n + 1; end
    end
endmodule

// ------------------------------------------------------------------------------ a measuring head --
// Two phases that must never be high together: how often they were, and the shortest dead time seen.
module nonoverlap_checker (input wire a, input wire b);
    integer  overlaps = 0, edges = 0;
    realtime t_a_fall = 0, t_b_fall = 0, min_gap = 1.0e18;
    always @(a or b) if (a === 1'b1 && b === 1'b1) overlaps = overlaps + 1;
    always @(negedge a) t_a_fall = $realtime;
    always @(negedge b) t_b_fall = $realtime;
    always @(posedge a) begin edges = edges + 1; if (t_b_fall != 0 && $realtime - t_b_fall < min_gap) min_gap = $realtime - t_b_fall; end
    always @(posedge b) begin edges = edges + 1; if (t_a_fall != 0 && $realtime - t_a_fall < min_gap) min_gap = $realtime - t_a_fall; end
    task clear; begin overlaps = 0; edges = 0; min_gap = 1.0e18; t_a_fall = 0; t_b_fall = 0; end endtask
endmodule
