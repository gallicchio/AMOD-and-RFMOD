#!/bin/sh
# Synthesise, place, route and pack pmodbench for the ECP5-2ADC-2DAC rev A board (LFE5U-25F-6BG256).
#   ./build.sh        -> build/pmodbench.bit
# The tools are the oss-cad-suite's; set OSS_CAD_SUITE if yours is elsewhere.  This script touches no hardware.
# Load the result (by hand, at the board) with
#   openFPGALoader -c ft2232 build/pmodbench.bit          (into the FPGA, until the next power cycle)
#   openFPGALoader -c ft2232 -f build/pmodbench.bit       (into the flash: it boots by itself from then on)
set -e
cd "$(dirname "$0")"
OSS=${OSS_CAD_SUITE:-$HOME/mudd/133electronics/icepi-zero-dac-adc/tools/oss-cad-suite}
PATH="$OSS/bin:$PATH"; export PATH
NAME=pmodbench
SRC="rtl/pmodbench.v rtl/pmod_port.v rtl/capture.v rtl/vendor/uart.v rtl/vendor/regbus.v"
BUILD_ID=${BUILD_ID:-$(date +%Y%m%d)}
mkdir -p build
yosys -q -l build/$NAME.yosys.log -p "read_verilog -defer $SRC; chparam -set BUILD_ID 32'h$BUILD_ID $NAME; synth_ecp5 -top $NAME -json build/$NAME.json" \
    || { tail -30 build/$NAME.yosys.log; exit 1; }
# two constraint files: the board's own (vendored, untouched) and pmodbench's Pmod pin settings on top of it;
# the board's pins this design does not use are left out of it (--lpf-allow-unconstrained), as in the host's bring-up
nextpnr-ecp5 --25k --package CABGA256 --speed 6 --json build/$NAME.json \
    --lpf constraints/vendor/ecp5_2adc_2dac.lpf --lpf constraints/pmodbench.lpf --lpf-allow-unconstrained \
    --textcfg build/$NAME.config --seed 1 > build/$NAME.pnr.log 2>&1 || { tail -40 build/$NAME.pnr.log; exit 1; }
ecppack --compress build/$NAME.config build/$NAME.bit
echo "build id $BUILD_ID"
grep -E "Max frequency for clock|Info: Device utilisation|TRELLIS_COMB:|TRELLIS_FF:|TRELLIS_IO:|DP16KD:|TRELLIS_RAMW:" build/$NAME.pnr.log | sed 's/^Info: *//' | tail -8
grep -ci "warning" build/$NAME.pnr.log | sed 's/^/warnings in the place-and-route log: /'
ls -la build/$NAME.bit
