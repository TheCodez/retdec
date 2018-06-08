#! /usr/bin/env python3

"""Unpacking of the given executable file."""

import re
import shutil
import sys
import argparse
import os
import subprocess

import retdec_utils as utils
import retdec_config as config

""""
The script tries to unpack the given executable file by using any
of the supported unpackers, which are at present:
   * generic unpacker
   * upx

Required argument:
   * (packed) binary file

Optional arguments:
   * desired name of unpacked file
   * use extended exit codes

Returns:
 0 successfully unpacked
"""

RET_UNPACK_OK = 0
#  1 generic unpacker - nothing to do; upx succeeded (--extended-exit-codes only)
RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK = 1
#  2 not packed or unknown packer
RET_NOTHING_TO_DO = 2
#  3 generic unpacker failed; upx succeeded (--extended-exit-codes only)
RET_UNPACKER_FAILED_OTHERS_OK = 3
#  4 generic unpacker failed; upx not succeeded
RET_UNPACKER_FAILED = 4

"""Try to unpack via inhouse generic unpacker.
Create parameters.
Generic unpacker exit codes:
0 Unpacker ended successfully.
"""
UNPACKER_EXIT_CODE_OK = 0
# 1 There was not found matching plugin.
UNPACKER_EXIT_CODE_NOTHING_TO_DO = 1
# 2 At least one plugin failed at the unpacking of the file.
UNPACKER_EXIT_CODE_UNPACKING_FAILED = 2
# 3 Error with preprocessing of input file before unpacking.
UNPACKER_EXIT_CODE_PREPROCESSING_ERROR = 3


# 10 other errors
# RET_OTHER_ERRORS = 10


def get_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-e', '--extended-exit-codes',
                        dest='extended_exit_codes',
                        action='store_true',
                        help='Use more granular exit codes than just 0/1.')

    parser.add_argument('-o', '--output',
                        dest='output',
                        default='file-unpacked',
                        help='Output file')

    parser.add_argument('--max-memory',
                        dest='max_memory',
                        help='Limit the maximal memory of retdec-unpacker to N bytes.')

    parser.add_argument('--max-memory-half-ram',
                        dest='max_memory_half_ram',
                        action='store_true',
                        help='Limit the maximal memory of retdec-unpacker to half of system RAM.')

    parser.add_argument('input',
                        help='The input file')

    return parser


def check_arguments(_args):
    """Check proper combination of input arguments.
    """

    # Check whether the input file was specified.
    if not _args.input:
        utils.print_error_and_die('No input file was specified')

    if not os.access(_args.input, os.R_OK):
        utils.print_error_and_die('The input file %s does not exist or is not readable' % _args.input)

    # Conditional initialization.
    if not _args.output:
        _args.output = '\'' + _args.input + '\'-unpacked'

    # OUT = Expand.colonEq('OUT','\'' + str(IN) + '\'-unpacked')

    if not re.search('^[0-9] + ' + '$', _args.max_memory):
        utils.print_error_and_die('Invalid value for --max-memory: %d (expected a positive integer)' % _args.max_memory)

    # Convert to absolute paths.
    _args.input = utils.get_realpath(_args.input)
    _args.output = utils.get_realpath(_args.output)


def try_to_unpack(_args, _output):
    """Try to unpack the given file.
    """

    if not (os.path.exists(_args.input) and os.stat(_args.input).st_size > 0) or _output == '':
        print('UNPACKER: wrong arguments')
        return RET_NOTHING_TO_DO

    unpacker_params = [_args.input, ' -o ', _output]

    if _args.max_memory:
        unpacker_params.append('--max-memory ' + _args.max_memory)
    elif _args.max_memory_half_ram:
        unpacker_params.append('--max-memory-half-ram')

    print()
    print('##### Trying to unpack ' + _args.input + ' into ' + _output + ' by using generic unpacker...')

    print('RUN: ' + config.UNPACKER + ' ' + ' '.join(unpacker_params))

    unpacker_rc = subprocess.call([config.UNPACKER, ' '.join(unpacker_params)], shell=True)

    if unpacker_rc == UNPACKER_EXIT_CODE_OK:
        print('##### Unpacking by using generic unpacker: successfully unpacked')
        return RET_UNPACK_OK
    elif unpacker_rc == UNPACKER_EXIT_CODE_NOTHING_TO_DO:
        print('##### Unpacking by using generic unpacker: nothing to do')
    else:
        # Do not return -> try the next unpacker
        # UNPACKER_EXIT_CODE_UNPACKING_FAILED
        # UNPACKER_EXIT_CODE_PREPROCESSING_ERROR
        print('##### Unpacking by using generic unpacker: failed')

    # Do not return -> try the next unpacker
    # Try to unpack via UPX
    print()
    print('##### Trying to unpack ' + _args.input + ' into ' + _output + ' by using UPX...')
    print('RUN: upx -d ' + _args.input + ' -o ' + _output)

    _rc0 = subprocess.call('upx' + ' ' + '-d' + ' ' + _args.input + ' ' + '-o' + ' ' + _output, shell=True,
                           stdout=open(os.devnull, 'wb'))

    if _rc0 == 0:
        print('##### Unpacking by using UPX: successfully unpacked')
        if _args.extended_exit_codes:
            if unpacker_rc == UNPACKER_EXIT_CODE_NOTHING_TO_DO:
                return RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK
            elif unpacker_rc >= UNPACKER_EXIT_CODE_UNPACKING_FAILED:
                return RET_UNPACKER_FAILED_OTHERS_OK
        else:
            return RET_UNPACK_OK
    else:
        # We cannot distinguish whether upx failed or the input file was
        # not upx-packed
        print('##### Unpacking by using UPX: nothing to do')

    # Do not return -> try the next unpacker
    # Return.
    if unpacker_rc >= UNPACKER_EXIT_CODE_UNPACKING_FAILED:
        return RET_UNPACKER_FAILED
    else:
        return RET_NOTHING_TO_DO


if __name__ == '__main__':

    args = get_parser().parse_args()

    # Check arguments and set default values for unset options.
    check_arguments(args)

    should_continue = True
    res_rc = -1
    return_code = -1

    while should_continue:
        return_code = try_to_unpack(args, args.output + '.tmp')

        if return_code == RET_UNPACK_OK or return_code == RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK \
                or return_code == RET_UNPACKER_FAILED_OTHERS_OK:
            res_rc = return_code

            shutil.move(args.output + '.tmp', args.output)
            args.input = args.output
        else:
            # Remove the temporary file, just in case some of the unpackers crashed
            # during unpacking and left it on the disk (e.g. upx).
            utils.remove_forced(args.output + '.tmp')

            should_continue = False

    if res_rc == -1:
        sys.exit(return_code)
    else:
        sys.exit(res_rc)
