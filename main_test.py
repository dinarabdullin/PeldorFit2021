''' Main file of osPDSFit : test version'''

import argparse
from datetime import time

from input.read_config import read_config
from simulation.simulator import Simulator
from output.make_output_directory import make_output_directory 
from output.save_epr_spectrum import save_epr_spectrum
from output.save_bandwidth import save_bandwidth
from output.save_time_trace import save_time_trace
from plots.plot_epr_spectrum import plot_epr_spectrum
from plots.plot_time_trace import plot_time_trace
from plots.keep_figures_visible import keep_figures_visible

if __name__ == '__main__':
	# Read out the config file 
	#parser = argparse.ArgumentParser()
	#parser.add_argument('filepath', help='Path to the configuration file')
	#args = parser.parse_args()
	#filepath_config = args.filepath
	filepath_config = 'examples/example01_nitroxide_biradical_Wband_PELDOR/config_ex01.cfg'
	#filepath_config = 'examples/example01_nitroxide_biradical_Wband_PELDOR/config_ex01_grids.cfg'
	mode, experiments, spins, simulation_settings, calculation_settings, output_settings = read_config(filepath_config)

	# Make an output directory
	make_output_directory(output_settings, filepath_config)

	# Init simulator
	simulator = Simulator(calculation_settings)

	# Simulate the EPR spectrum of the spin system
	spectrum = simulator.epr_spectrum(spins, experiments[0].magnetic_field)
	save_epr_spectrum(spectrum, output_settings['directory'])

	# Test the Peldor_4p_rect class: calculate the bandwidths of pump and detection pulses
	detection_bandwidth = experiments[0].get_detection_bandwidth()
	pump_bandwidth = experiments[0].get_pump_bandwidth()
	save_bandwidth(detection_bandwidth, output_settings['directory'], 'detection_bandwidth_'+experiments[0].name)
	save_bandwidth(pump_bandwidth, output_settings['directory'], 'pump_bandwidth_'+experiments[0].name)

	# Plot the EPR spectrum of the spin system overlaid with the pump and detection bandwidth profiles
	#plot_epr_spectrum(spectrum, save_figure=True, directory=output_settings['directory'])
	plot_epr_spectrum(spectrum, detection_bandwidth, pump_bandwidth, 
        save_figure=True, directory=output_settings['directory'], filename='epr_spectrum_'+experiments[0].name)
	
    # Test the Peldor_4p_rect class: calculate the PELDOR time trace
	simulated_time_trace = simulator.compute_time_trace(experiments[0], spins, simulation_settings['parameters'])
	save_time_trace(simulated_time_trace['t'], simulated_time_trace['s'], experiments[0].s, output_settings['directory'], filename='timetrace_'+experiments[0].name)
	plot_time_trace(simulated_time_trace['t'], simulated_time_trace['s'], experiments[0].s, 
        save_figure=True, directory=output_settings['directory'], filename='timetrace_'+experiments[0].name)

	keep_figures_visible()