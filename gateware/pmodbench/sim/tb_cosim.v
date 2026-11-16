// The PC's side of the UART driven by another process, so host/pmodbench.py itself runs against the RTL
// (host/simlink.py, host/test_sim.py).  Two named pipes: commands in (one a line), replies out.
//   S xx          send the byte xx (hex) to the board
//   W n           let n ns pass
//   R n           run until the board has sent n bytes in all (or 200 ms have passed), then answer "r <bytes> <ns>"
//   Y             answer "r <bytes> <ns>" now
//   P p b         plug tile b (tiles.v's numbers) into Pmod p (0 = A, 1 = B)
//   V p name x    set the knob `name` of Pmod p's models to x (tile_socket.set_param)
//   Q             print the state of both sockets' models and checkers as "q ..." lines, then "q end"
//   E             end the run
// Every byte the board sends is written at once as "u xx".
`timescale 1ns/1ps
module tb_cosim;
`include "bench.vh"
    integer fi, fo, r, n, b, p, total = 0;
    real    x;
    reg [8*12:1] name;
    reg [8*8:1]  kind;
    reg [1023:0] cmd_path, resp_path;

    // the board's replies
    reg [7:0] rb; integer i;
    always begin
        @(negedge uart_tx); #(BIT * 1.5);
        for (i = 0; i < 8; i = i + 1) begin rb[i] = uart_tx; #(BIT); end
        total = total + 1;
        if (^rb === 1'bx) $fwrite(fo, "u xx\n"); else $fwrite(fo, "u %02x\n", rb);
    end

    realtime t0;
    initial begin
        if (!$value$plusargs("cmd=%s", cmd_path)) cmd_path = "cmd.fifo";
        if (!$value$plusargs("resp=%s", resp_path)) resp_path = "resp.fifo";
        fi = $fopen(cmd_path, "r");
        fo = $fopen(resp_path, "w");
        if (fi == 0 || fo == 0) begin $display("tb_cosim: cannot open the pipes"); $finish; end
        #2000;
        while (!$feof(fi)) begin
            r = $fscanf(fi, "%s", kind);
            // anything but a byte waits for the last byte sent to have done its work in the board (a write acts
            // half a bit into its stop bit, the pins follow two clocks later)
            if (r == 1 && kind[8:1] != "S" && $realtime - t_sent < 2.0 * BIT) #(2.0 * BIT - ($realtime - t_sent));
            if (r == 1) case (kind[8:1])
            "S": begin r = $fscanf(fi, "%h", b); send_byte(b); end
            "W": begin r = $fscanf(fi, "%d", n); #(n); end
            "R": begin
                r = $fscanf(fi, "%d", n); t0 = $realtime;
                while (total < n && $realtime - t0 < 200.0e6) #(BIT);
                #(BIT * 0.6);
                $fwrite(fo, "r %0d %0.0f\n", total, $realtime); $fflush(fo);
            end
            "Y": begin $fwrite(fo, "r %0d %0.0f\n", total, $realtime); $fflush(fo); end
            "P": begin r = $fscanf(fi, "%d %d", p, b); if (p == 0) board_a = b; else board_b = b; end
            "V": begin r = $fscanf(fi, "%d %s %f", p, name, x); if (p == 0) sa.set_param(name, x); else sb.set_param(name, x); end
            "Q": begin sa.report(fo, "A"); sb.report(fo, "B"); $fwrite(fo, "q end\n"); $fflush(fo); end
            "E": begin #(BIT * 20); $fclose(fo); $finish; end
            default: $display("tb_cosim: unknown command %0s", kind);
            endcase
        end
        $fclose(fo); $finish;
    end
endmodule
