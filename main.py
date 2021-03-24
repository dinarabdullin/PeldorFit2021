import argparse
from functools import partial
import multiprocessing
from input.read_config import read_config
from fitting.objective_function import objective_function, fit_function
from output.fitting.print_fitting_parameters import print_fitting_parameters
from output.fitting.print_modulation_depth_scale_factors import print_modulation_depth_scale_factors
from plots.keep_figures_visible import keep_figures_visible


if __name__ == '__main__':
    multiprocessing.freeze_support()

    # Read out the config file 
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', help="Path to the configuration file")
    args = parser.parse_args()
    filepath_config = args.filepath
    mode, experiments, spins, simulation_parameters, fitting_parameters, optimizer, \
    error_analysis_parameters, error_analyzer, simulator, data_saver, plotter = read_config(filepath_config)
    
    # Run precalculations
    simulator.precalculations(experiments, spins)
    
    # Run simulations
    if mode['simulation']:
    
        # Simulate the EPR spectrum of the spin system
        epr_spectra = simulator.epr_spectra(spins, experiments)
        
        # Compute the bandwidths of the detection and pump pulses
        bandwidths = simulator.bandwidths(experiments)
        
        # Simulate the PDS time traces
        simulated_time_traces, modulation_depth_scale_factors = simulator.compute_time_traces(experiments, spins, simulation_parameters)
        
        # Save the simulation output
        data_saver.save_simulation_output(epr_spectra, bandwidths, simulated_time_traces, experiments)
        
        # Plot the simulation output
        plotter.plot_simulation_output(epr_spectra, bandwidths, simulated_time_traces, experiments)

    # Run fitting
    if mode['fitting']:
        
        # Set the fit and objective functions
        partial_fit_function = partial(fit_function, simulator=simulator, experiments=experiments, spins=spins, 
                                       fitting_parameters=fitting_parameters)
        partial_objective_function = partial(objective_function, simulator=simulator, experiments=experiments, spins=spins, 
                                             fitting_parameters=fitting_parameters, goodness_of_fit=optimizer.goodness_of_fit)
        optimizer.set_fit_function(partial_fit_function)
        optimizer.set_objective_function(partial_objective_function)
        
        # Optimize the fitting parameters
        optimized_parameters, score = optimizer.optimize(fitting_parameters['ranges'])                                                         
        
        # Display the fitted and fixed parameters
        print_fitting_parameters(fitting_parameters['indices'], optimized_parameters, fitting_parameters['values'])
        
        # Compute the fit to the experimental PDS time traces
        simulated_time_traces, modulation_depth_scale_factors = optimizer.get_fit()
        
        # Display the scale factors of modulation depths
        if simulator.fit_modulation_depth:
            print_modulation_depth_scale_factors(modulation_depth_scale_factors, experiments)

        # Save the fitting output
        data_saver.save_fitting_output(score, optimized_parameters, [], simulated_time_traces, fitting_parameters, experiments)
        
        # Plot the fitting output
        plotter.plot_fitting_output(score, optimizer.goodness_of_fit, simulated_time_traces, experiments)       
    
    # Run error analysis
    if mode['error_analysis']:
        
        if not mode['fitting']:
            optimized_parameters, parameter_errors = error_analyzer.load_optimized_parameters(fitting_parameters['indices'])
            print_fitting_parameters(fitting_parameters['indices'], optimized_parameters, fitting_parameters['values'], parameter_errors)
        
        # Set the objective function: the goodness-of-fit has to be set to 'chi2'
        partial_objective_function = partial(objective_function, simulator=simulator, experiments=experiments, spins=spins, 
                                             fitting_parameters=fitting_parameters, goodness_of_fit='chi2')
        error_analyzer.set_objective_function(partial_objective_function)
        
        # Run the error analysis
        score_vs_parameter_subsets, score_vs_parameters, numerical_error, score_threshold, parameter_errors = \
        error_analyzer.run_error_analysis(error_analysis_parameters, fitting_parameters, optimized_parameters)
        
        # Display the fitted and fixed parameters with the corresponding confidence intervals
        print_fitting_parameters(fitting_parameters['indices'], optimized_parameters, fitting_parameters['values'], parameter_errors)
        
        # Save the optimized values of fitting parameters with their error estimates
        data_saver.save_fitting_parameters(fitting_parameters['indices'], optimized_parameters, fitting_parameters['values'], parameter_errors)

        # Plot the error analysis output
        plotter.plot_error_analysis_output(score_vs_parameter_subsets, score_vs_parameters, error_analysis_parameters, 
                                           fitting_parameters, optimized_parameters, score_threshold, numerical_error)
    
    print('\nDONE!')
    keep_figures_visible()