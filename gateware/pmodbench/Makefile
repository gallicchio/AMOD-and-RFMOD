# pmodbench: the ECP5-2ADC-2DAC board's two Pmod sockets from the PC.  Tools: the oss-cad-suite (yosys,
# nextpnr-ecp5, ecppack, iverilog, vvp); set OSS_CAD_SUITE if it is not at the default path.  Nothing here
# touches hardware: loading the bitstream is a command for a person at the board (see README.md).
OSS ?= $(HOME)/mudd/133electronics/icepi-zero-dac-adc/tools/oss-cad-suite
IV = $(OSS)/bin/iverilog
VVP = $(OSS)/bin/vvp
RTL = rtl/pmodbench.v rtl/pmod_port.v rtl/capture.v rtl/vendor/uart.v rtl/vendor/regbus.v
SIM = sim/models.v sim/tiles.v sim/bench.vh

all: sim test bit

bit:                        ## build/pmodbench.bit (yosys, nextpnr-ecp5, ecppack): utilisation and timing at the end
	./build.sh

sim: build/tb_pmodbench.vvp ## the self-checking testbench (half a minute): PASS or the failures
	cd build && $(VVP) -n tb_pmodbench.vvp | grep -v 'VCD info' | tail -100
build/tb_pmodbench.vvp: sim/tb_pmodbench.v $(RTL) $(SIM)
	mkdir -p build && $(IV) -g2012 -I sim -o $@ -s tb_pmodbench sim/tb_pmodbench.v $(RTL) sim/models.v sim/tiles.v

test:                       ## host/pmodbench.py against the RTL (the Python drives the simulated UART), with sigrok-cli if installed
	python3 host/max2871.py 915e6 3 > /dev/null && python3 host/trf3722.py 915e6 > /dev/null
	python3 host/test_sim.py

mutants:                    ## plant each bug of host/test_mutants.py in a copy and see that the tests catch it
	python3 host/test_mutants.py

clean:                      ## the intermediate files; build/pmodbench.bit stays
	rm -rf build/*.json build/*.config build/*.log build/*.vvp build/*.vcd build/*.py build/*.out host/__pycache__ host/vendor/__pycache__

.PHONY: all bit sim test mutants clean
