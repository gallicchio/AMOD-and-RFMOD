// A Pmod socket with a tile board plugged into it, for the testbenches.  `board` says which tile
// (or test jig) is in the socket; the models of its chips (models.v) are wired to the eight lines as the
// tile wires them, with the tile's own pull resistors, and everything the bench should know is counted:
// a pulse meter on every line, the checkers each tile needs, and `contention`, which counts every time
// the FPGA enables a pin the tile drives (host_oe is the FPGA's enables, taken from inside the design).
//   io[k] is the tile's IOk = pmod[k-1].
`timescale 1ns/1ps
module tile_socket (inout wire [8:1] io, input wire [3:0] board, input wire [8:1] host_oe);
    localparam NONE = 0, AMOD_A = 1, AMOD_N = 2, AMOD_C = 3, AMOD_M = 4, AMOD_B = 5, RF_MOD = 6, PHMOD = 7, IQ_MOD = 8,
               SPI_JIG = 9,      // a generic SPI slave: IO1 MISO, IO2 MOSI, IO3 SCK, IO4 CS
               LOOP_JIG = 10;    // IO1-4 buffered onto IO5-8
    wire [8:1] p;                                   // the lines as logic (a floating or contended line reads 0)
    genvar k;
    generate for (k = 1; k <= 8; k = k + 1) begin : clean assign p[k] = io[k] === 1'b1; end endgenerate
    wire is_a = board == AMOD_A, is_n = board == AMOD_N, is_c = board == AMOD_C, is_m = board == AMOD_M, is_b = board == AMOD_B;
    wire is_rf = board == RF_MOD, is_iq = board == IQ_MOD, is_jig = board == SPI_JIG, is_loop = board == LOOP_JIG;
    wire is_max = is_rf || is_iq;

    // ---- the tiles' pull resistors -------------------------------------------------------------------
    assign (pull1, pull0) io[4] = is_n ? 1'b1 : is_max ? 1'b0 : 1'bz;     // n8: LE 100 k up; r10, q3: LE 100 k down
    assign (pull1, pull0) io[6] = is_a ? 1'b0 : 1'bz;                     // a8: 10 k down on the heater FET's gate

    // ---- the chips ---------------------------------------------------------------------------------------
    wire max_mux, max_mux_en;
    max2871_model max (.clk(is_max & p[3]), .data(p[2]), .le(is_max & p[4]), .mux(max_mux), .mux_en(max_mux_en));
    wire trf_rdbk;
    trf3722_model trf (.clk(is_rf & p[3]), .data(p[2]), .le(is_rf & p[6]), .rdbk(trf_rdbk));
    pe43711_model pe (.si(p[2]), .clk(is_n & p[3]), .le(is_n & p[4]));
    wire enc_do, imu_sdo, imu_en;
    wire cs_enc_n = !is_b || p[6], cs_imu_n = !is_b || p[8];
    mt6701_model mt (.csn(cs_enc_n), .clk(!is_b || p[4]), .dout(enc_do));
    lsm6dso_model imu (.cs(cs_imu_n), .spc(!is_b || p[4]), .sdi(p[7]), .sdo(imu_sdo), .sdo_en(imu_en));
    wire a6_bit;
    dsm_a6_model a6 (.en(is_a), .fb(p[8]), .bit_o(a6_bit));
    wire c6_bit;
    dsm_clocked_model c6 (.clk(is_c & p[1]), .bit_o(c6_bit));
    reg  c8_bit = 0;                                 // c8's comparator: set from the bench
    wire enc_a, enc_b;
    quad_encoder_model enc (.a(enc_a), .b(enc_b));
    wire jig_miso;
    spi_slave_model jig (.sck(is_jig & p[3]), .mosi(p[2]), .cs_n(!is_jig || p[4]), .miso(jig_miso));

    // ---- what the tile drives ------------------------------------------------------------------------------
    reg [8:1] t_en, t_val, t_out;                    // t_out: the lines that are the tile's outputs (for `contention`)
    always @(*) begin
        t_en = 0; t_val = 0; t_out = 0;
        case (board)
        AMOD_A:   begin t_out = 8'b0100_0000; t_en = t_out; t_val[7] = a6_bit; end
        AMOD_C:   begin t_out = 8'b0100_0010; t_en = t_out; t_val[7] = c6_bit; t_val[2] = c8_bit; end
        AMOD_M:   begin t_out = 8'b0011_0000; t_en = t_out; t_val[5] = enc_a; t_val[6] = enc_b; end
        AMOD_B:   begin t_out = 8'b0000_0100; t_en[3] = !cs_enc_n || imu_en; t_val[3] = !cs_enc_n ? enc_do : imu_sdo; end   // the '125, else the IMU
        RF_MOD:   begin t_out = 8'b0001_0001; t_en[1] = max_mux_en; t_val[1] = max_mux; t_en[5] = 1'b1; t_val[5] = trf_rdbk; end
        IQ_MOD:   begin t_out = 8'b0000_0001; t_en[1] = max_mux_en; t_val[1] = max_mux; end
        SPI_JIG:  begin t_out = 8'b0000_0001; t_en = t_out; t_val[1] = jig_miso; end
        LOOP_JIG: begin t_out = 8'b1111_0000; t_en = t_out; t_val[8:5] = p[4:1]; end
        default: ;
        endcase
    end
    generate for (k = 1; k <= 8; k = k + 1) begin : drive assign io[k] = t_en[k] ? t_val[k] : 1'bz; end endgenerate

    // ---- the checkers ---------------------------------------------------------------------------------------
    integer    contention = 0;
    reg  [8:1] clash_pins = 0;
    wire [8:1] clash = host_oe & t_out;
    always @(clash) if (clash != 0) begin contention = contention + 1; clash_pins = clash_pins | clash; end
    integer cs_fight = 0;                            // b6: both chip selects driven low together
    wire    both_cs = is_b && host_oe[6] && host_oe[8] && !p[6] && !p[8];
    always @(posedge both_cs) begin #1; if (both_cs) cs_fight = cs_fight + 1; end      // (not the instant an enable and its pad settle)
    integer sw_equal = 0;                            // q11: V1 and V2 driven to the same level
    always @(p[5] or p[8]) if (is_iq && host_oe[5] && host_oe[8]) begin #2; if (p[5] == p[8]) sw_equal = sw_equal + 1; end
    nonoverlap_checker hb (.a(is_a & p[4]), .b(is_a & p[3]));           // a11: IN1, IN2 never high together
    nonoverlap_checker c5 (.a(is_c & p[4]), .b(is_c & p[8]));           // c5: phi1, phi2

    // a pulse meter on every line (ns)
    integer  m_rises [1:8], m_falls [1:8];
    realtime m_trise [1:8], m_tfall [1:8], m_period [1:8], m_high [1:8], m_low [1:8];
    realtime m_minp [1:8], m_maxp [1:8], m_minh [1:8], m_maxh [1:8], m_minl [1:8], m_maxl [1:8];
    integer j;
    task clear; begin
        for (j = 1; j <= 8; j = j + 1) begin
            m_rises[j] = 0; m_falls[j] = 0; m_trise[j] = 0; m_tfall[j] = 0; m_period[j] = 0; m_high[j] = 0; m_low[j] = 0;
            m_minp[j] = 1.0e18; m_maxp[j] = 0; m_minh[j] = 1.0e18; m_maxh[j] = 0; m_minl[j] = 1.0e18; m_maxl[j] = 0;
        end
        hb.clear; c5.clear;
    end endtask
    initial clear;
    generate for (k = 1; k <= 8; k = k + 1) begin : meter
        always @(posedge p[k]) begin
            if (m_rises[k] > 0) begin
                m_period[k] = $realtime - m_trise[k];
                if (m_period[k] < m_minp[k]) m_minp[k] = m_period[k];
                if (m_period[k] > m_maxp[k]) m_maxp[k] = m_period[k];
            end
            if (m_falls[k] > 0) begin
                m_low[k] = $realtime - m_tfall[k];
                if (m_low[k] < m_minl[k]) m_minl[k] = m_low[k];
                if (m_low[k] > m_maxl[k]) m_maxl[k] = m_low[k];
            end
            m_trise[k] = $realtime; m_rises[k] = m_rises[k] + 1;
        end
        always @(negedge p[k]) begin
            if (m_rises[k] > 0) begin
                m_high[k] = $realtime - m_trise[k];
                if (m_high[k] < m_minh[k]) m_minh[k] = m_high[k];
                if (m_high[k] > m_maxh[k]) m_maxh[k] = m_high[k];
            end
            m_tfall[k] = $realtime; m_falls[k] = m_falls[k] + 1;
        end
    end endgenerate

    // ---- for the co-simulation: set a model's knob by name, and print everything ---------------------------
    task set_param(input [8*12:1] name, input real val); begin
        if      (name == "vin")     a6.vin = val;
        else if (name == "level")   c6.level = val;
        else if (name == "cmp")     c8_bit = val != 0.0;
        else if (name == "steps")   enc.steps = val;
        else if (name == "step_ns") enc.step_ns = val;
        else if (name == "glitch")  enc.glitch;
        else if (name == "angle")   mt.angle = val;
        else if (name == "status")  mt.status = val;
        else if (name == "jig_mode") begin jig.cpol = (val >= 2.0 && val < 4.0) || val >= 6.0; jig.cpha = $rtoi(val) % 2 == 1; jig.lsb = val >= 4.0; end
        else if (name == "jig_nbits") jig.nbits = val;
        else if (name == "jig_tco") jig.tco = val;
        else if (name == "clear")   clear;
        else $display("tile_socket: no knob called %0s", name);
    end endtask
    task report(input integer fd, input [7:0] nm); integer i; begin
        $fwrite(fd, "q %s.sock board=%0d contention=%0d clash_pins=%0d cs_fight=%0d sw_equal=%0d c8=%0d\n", nm, board, contention, clash_pins, cs_fight, sw_equal, c8_bit);
        for (i = 1; i <= 8; i = i + 1)
            $fwrite(fd, "q %s.m%0d rises=%0d falls=%0d period=%0.3f high=%0.3f low=%0.3f min_period=%0.3f max_period=%0.3f min_high=%0.3f max_high=%0.3f min_low=%0.3f max_low=%0.3f t_rise=%0.3f t_fall=%0.3f\n",
                    nm, i, m_rises[i], m_falls[i], m_period[i], m_high[i], m_low[i], m_minp[i], m_maxp[i], m_minh[i], m_maxh[i], m_minl[i], m_maxl[i], m_trise[i], m_tfall[i]);
        $fwrite(fd, "q %s.max n=%0d viol=%0d bad_len=%0d rfb_on=%0d passes=%0d locked=%0d pause_ok=%0d f_out=%0.3f f_vco=%0.3f\n",
                nm, max.n, max.viol, max.bad_len, max.rfb_on, max.passes, max.locked, max.pause_ok, max.f_out, max.f_vco);
        for (i = 0; i < max.n && i < 256; i = i + 1) $fwrite(fd, "q %s.max.w%0d v=0x%08x\n", nm, i, max.log[i]);
        $fwrite(fd, "q %s.pe att=%0d latches=%0d viol=%0d bad_len=%0d bad_d7=%0d clk_while_le=%0d\n", nm, pe.att, pe.latches, pe.viol, pe.bad_len, pe.bad_d7, pe.clk_while_le);
        $fwrite(fd, "q %s.trf writes=%0d bad_addr=%0d short_words=%0d readbacks=%0d viol=%0d r1=0x%08x r2=0x%08x r3=0x%08x r4=0x%08x r5=0x%08x r6=0x%08x\n",
                nm, trf.writes, trf.bad_addr, trf.short_words, trf.readbacks, trf.viol, trf.r[1], trf.r[2], trf.r[3], trf.r[4], trf.r[5], trf.r[6]);
        for (i = 0; i < trf.writes && i < 64; i = i + 1) $fwrite(fd, "q %s.trf.w%0d v=0x%08x\n", nm, i, trf.log[i]);
        $fwrite(fd, "q %s.mt reads=%0d nclk=%0d mode_viol=%0d sent=0x%06x angle=%0d status=%0d\n", nm, mt.reads, mt.nclk, mt.mode_viol, mt.sent, mt.angle, mt.status);
        $fwrite(fd, "q %s.imu frames=%0d mode_viol=%0d wr_count=%0d\n", nm, imu.frames, imu.mode_viol, imu.wr_count);
        $fwrite(fd, "q %s.a6 vin=%0.6f v=%0.6f\n", nm, a6.vin, a6.v);
        $fwrite(fd, "q %s.hb overlaps=%0d edges=%0d min_gap=%0.3f\n", nm, hb.overlaps, hb.edges, hb.min_gap);
        $fwrite(fd, "q %s.c5 overlaps=%0d edges=%0d min_gap=%0.3f\n", nm, c5.overlaps, c5.edges, c5.min_gap);
        $fwrite(fd, "q %s.enc pos=%0d steps=%0d\n", nm, enc.pos, enc.steps);
        $fwrite(fd, "q %s.jig frames=%0d n=%0d rx=0x%08x\n", nm, jig.frames, jig.n, jig.rx);
    end endtask
endmodule
