import argparse
import os
import sys

import ledsa.analysis.ExtinctionCoefficientsNumeric as ECN
from ledsa.analysis.Experiment import Experiment
# from ledsa.analysis.ExperimentData import create_experiment_data, load_experiment_data # Todo: remove
from ledsa.analysis.ExperimentData import ExperimentData
from ledsa.analysis.ConfigDataAnalysis import ConfigDataAnalysis
def main(argv):
    parser = argparse.ArgumentParser(description=
                                     'Calculation of the extinction coefficients.')
    parser = add_parser_argument_analysis(parser)

    args = parser.parse_args(argv)

    run_analysis_arguments(args)

    # create files with the extinction coefficients
    extionction_coefficient_calculation(args)


def add_parser_argument_analysis(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument('--analysis', action='store_true',
                        help='Activate extinction coefficient calculation if not run directly from analysis package')
    parser.add_argument('--config_analysis', '-conf_a', nargs='*', default=None,
                        help='creates the analysis configuration file.')
    parser.add_argument('--cc', '--color_correction', action='store_true',
                        help='Applies color correction matrix before calculating the extinction coefficients. Use only, if'
                             'the reference property is not already color corrected.')
    parser.add_argument('--no_mp', action='store_true',
                        help='Deactivates multi core processing.')
    parser.add_argument('--cc_channels', default=[0, 1, 2], action='extend', nargs="+", type=int,
                        help='Channels, to which color correcten gets applied. Default 0 1 2')
    return parser


def run_analysis_arguments(args):
    if args.config_analysis is not None:
        ConfigDataAnalysis(load_config_file=False)

    if args.cc:
        ex_data = ExperimentData()
        apply_cc_on_ref_property(ex_data)
def run_analysis_arguments_with_extinction_coefficient(args):
    run_analysis_arguments(args)
    if args.analysis:
        extionction_coefficient_calculation(args)


def extionction_coefficient_calculation(args):
    ex_data = ExperimentData()
    ex_data.request_config_parameters()
    for array in ex_data.arrays:
        for channel in ex_data.channels:
            out_file = os.path.join(os.getcwd(), 'analysis', 'AbsorptionCoefficients',
                                    f'absorption_coefs_numeric_channel_{channel}_{ex_data.reference_property}_led_array_{array}.csv')
            if not os.path.exists(out_file):
                ex = Experiment(ex_data.layers, led_array=array, camera=ex_data.camera, channel=channel)
                eca = ECN.ExtinctionCoefficientsNumeric(ex, reference_property=ex_data.reference_property, num_ref_imgs=ex_data.num_ref_images)
                if args.no_mp:
                    eca.calc_and_set_coefficients()
                else:
                    eca.calc_and_set_coefficients_mp(ex_data.n_cpus)
                eca.save()
                print(f"{out_file} created!")
            else:
                print(f"{out_file} already exists!")


def apply_cc_on_ref_property(ex_data):
    """ color corrected property will be saved in the binary as {ref_property}_cc
    """
    import numpy as np
    from ledsa.analysis.data_preparation import apply_color_correction
    try:
        cc_matrix = np.genfromtxt('mean_all_cc_matrix_integral.csv', delimiter=',')
    except(FileNotFoundError):
        print('File: mean_all_cc_matrix_integral.csv containing the color correction matrix not found')
        exit(1)
    apply_color_correction(cc_matrix, on=ex_data.reference_property, channels= args.cc_channels)


if __name__ == "__main__":
    args = sys.argv
    main(sys.argv[1:])