#! /usr/bin/env python
from __future__ import print_function

import shutil
import sys

"""Unpacking of the given executable file."""

import argparse
import os, subprocess

import retdec_utils as utils
import retdec_config as config

#
# The script tries to unpack the given executable file by using any
# of the supported unpackers, which are at present:
#    * generic unpacker
#    * upx
#
# Required argument:
#    * (packed) binary file
#
# Optional arguments:
#    * desired name of unpacked file
#    * use extended exit codes
#
# Returns:
#  0 successfully unpacked
RET_UNPACK_OK = 0
#  1 generic unpacker - nothing to do; upx succeeded (--extended-exit-codes only)
RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK = 1
#  2 not packed or unknown packer
RET_NOTHING_TO_DO = 2
#  3 generic unpacker failed; upx succeeded (--extended-exit-codes only)
RET_UNPACKER_FAILED_OTHERS_OK = 3
#  4 generic unpacker failed; upx not succeeded
RET_UNPACKER_FAILED = 4

# 10 other errors
# RET_OTHER_ERRORS = 10

IN = ''
OUT = ''


def get_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-e', '--extended-exit-codes',
                        dest='extended_exit_codes',
                        help='Use more granular exit codes than just 0/1.')

    parser.add_argument('-o', '--output',
                        dest='output',
                        default='file-unpacked',
                        help='Output file (default: file-unpacked)')

    parser.add_argument('--max-memory',
                        dest='max_memory',
                        help='Limit the maximal memory of retdec-unpacker to N bytes.')

    parser.add_argument('--max-memory-half-ram',
                        dest='max_memory_half_ram',
                        help='Limit the maximal memory of retdec-unpacker to half of system RAM.')

    parser.add_argument('file',
                        dest='input',
                        help='The input file')

    return parser


#
# Check proper combination of input arguments.
#
def check_arguments(args):
    global IN
    global OUT

    # Check whether the input file was specified.
    if IN == '':
        utils.print_error_and_die('No input file was specified')

    # Conditional initialization.
    if OUT is None or OUT == '':
        OUT = '\'' + str(IN) + '\'-unpacked'

    # OUT = Expand.colonEq('OUT','\'' + str(IN) + '\'-unpacked')
    # Convert to absolute paths.
    IN = utils.get_realpath(IN)
    OUT = utils.get_realpath(OUT)


#
# Try to unpack the given file.
#
def try_to_unpack(input, output):
    global RET_NOTHING_TO_DO
    global UNPACKER_PARAMS
    global MAX_MEMORY
    global MAX_MEMORY_HALF_RAM
    global UNPACKER
    global UNPACKER_RETCODE
    global RET_UNPACK_OK
    global DEV_NULL
    global EXTENDED
    global RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK
    global RET_UNPACKER_FAILED_OTHERS_OK
    global RET_UNPACKER_FAILED
    global IN
    global OUT

    if not (os.path.exists(input) and os.stat(input).st_size > 0) or output == '':
        print('UNPACKER: wrong arguments')
        return RET_NOTHING_TO_DO

    IN = input
    OUT = output

    # Try to unpack via inhouse generic unpacker.
    # Create parameters.
    # Generic unpacker exit codes:
    # 0 Unpacker ended successfully.
    UNPACKER_EXIT_CODE_OK = 0
    # 1 There was not found matching plugin.
    UNPACKER_EXIT_CODE_NOTHING_TO_DO = 1
    # 2 At least one plugin failed at the unpacking of the file.
    UNPACKER_EXIT_CODE_UNPACKING_FAILED = 2
    # 3 Error with preprocessing of input file before unpacking.
    UNPACKER_EXIT_CODE_PREPROCESSING_ERROR = 3
    UNPACKER_PARAMS = [IN, ' -o ', OUT]

    if MAX_MEMORY:
        UNPACKER_PARAMS = '(--max-memory ' + MAX_MEMORY + ')'
    elif MAX_MEMORY_HALF_RAM:
        UNPACKER_PARAMS = '(--max-memory-half-ram)'

    print()
    print('##### Trying to unpack ' + IN + ' into ' + OUT + ' by using generic unpacker...')

    print('RUN: ' + config.UNPACKER + ' ' + ' '.join(UNPACKER_PARAMS))

    UNPACKER_RETCODE = subprocess.call([config.UNPACKER, IN, '-o', OUT], shell=True)

    if UNPACKER_RETCODE == UNPACKER_EXIT_CODE_OK:
        print('##### Unpacking by using generic unpacker: successfully unpacked')
        return RET_UNPACK_OK
    elif UNPACKER_RETCODE == UNPACKER_EXIT_CODE_NOTHING_TO_DO:
        print('##### Unpacking by using generic unpacker: nothing to do')
    else:
        # Do not return -> try the next unpacker
        # UNPACKER_EXIT_CODE_UNPACKING_FAILED
        # UNPACKER_EXIT_CODE_PREPROCESSING_ERROR
        print('##### Unpacking by using generic unpacker: failed')

    # Do not return -> try the next unpacker
    # Try to unpack via UPX
    print()
    print('##### Trying to unpack ' + IN + ' into ' + OUT + ' by using UPX...')
    print('RUN: upx -d ' + IN + ' -o ' + OUT)
    _rc0 = subprocess.call('upx' + ' ' + '-d' + ' ' + IN + ' ' + '-o' + ' ' + OUT, shell=True,
                           stdout=open(os.devnull, 'wb'))

    if _rc0 == 0:
        print('##### Unpacking by using UPX: successfully unpacked')
        if EXTENDED == 'yes':
            if UNPACKER_RETCODE == UNPACKER_EXIT_CODE_NOTHING_TO_DO:
                return RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK
            elif UNPACKER_RETCODE >= UNPACKER_EXIT_CODE_UNPACKING_FAILED:
                return RET_UNPACKER_FAILED_OTHERS_OK
        else:
            return RET_UNPACK_OK
    else:
        # We cannot distinguish whether upx failed or the input file was
        # not upx-packed
        print('##### Unpacking by using UPX: nothing to do')

    # Do not return -> try the next unpacker
    # Return.
    if UNPACKER_RETCODE >= UNPACKER_EXIT_CODE_UNPACKING_FAILED:
        return RET_UNPACKER_FAILED
    else:
        return RET_NOTHING_TO_DO


""""
while (True):
    
    if ( str(sys.argv[1]) == '-e' or str(sys.argv[1]) == '--extended-exit-codes'):
        # Use extented exit codes.
        if str(EXTENDED) != '':
            subprocess.call(['print_error_and_die','Duplicate option: -e|--extended-exit-codes'],shell=True)
        Make('EXTENDED').setValue('yes')
        subprocess.call(['shift'],shell=True)
    elif ( str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help'):
        # Help.
        print_help()
        exit(int(RET_UNPACK_OK))
    elif ( str(sys.argv[1]) == '-o' or str(sys.argv[1]) == '--output'):
        # Output file.
        if str(OUT) != '':
            subprocess.call(['print_error_and_die','Duplicate option: -o|--output'],shell=True)
        Make('OUT').setValue(sys.argv[2])
        subprocess.call(['shift','2'],shell=True)
    elif ( str(sys.argv[1]) == '--max-memory-half-ram'):
        if str(MAX_MEMORY_HALF_RAM) != '':
            subprocess.call(['print_error_and_die','Duplicate option: --max-memory-half-ram'],shell=True)
        if str(MAX_MEMORY) != '':
            subprocess.call(['print_error_and_die','Clashing options: --max-memory-half-ram and --max-memory'],shell=True)
        Make('MAX_MEMORY_HALF_RAM').setValue(1)
        subprocess.call(['shift'],shell=True)
    elif ( str(sys.argv[1]) == '--max-memory'):
        if str(MAX_MEMORY) != '':
            subprocess.call(['print_error_and_die','Duplicate option: --max-memory'],shell=True)
        if str(MAX_MEMORY_HALF_RAM) != '':
            subprocess.call(['print_error_and_die','Clashing options: --max-memory and --max-memory-half-ram'],shell=True)
        Make('MAX_MEMORY').setValue(sys.argv[2])
        if (not re.search(Str(Glob('^[0-9] + ' + '$')),str(MAX_MEMORY)) ):
            subprocess.call(['print_error_and_die','Invalid value for --max-memory: ' + str(MAX_MEMORY) + ' (expected a positive integer)'],shell=True)
        subprocess.call(['shift','2'],shell=True)
    elif ( str(sys.argv[1]) == '--'):
        # Input file.
        if Expand.hash() == 2:
            Make('IN').setValue(sys.argv[2])
            if not os.access(str(IN),R_OK):
                subprocess.call(['print_error_and_die','The input file '' + str(IN) + '' does not exist or is not readable'],shell=True)
        elif Expand.hash() > 2:
            # Invalid options.
            subprocess.call(['print_error_and_die','Invalid options: '' + str(sys.argv[2]) + '', '' + str(sys.argv[3]) + '' ...'],shell=True)
        break
"""

# Check arguments and set default values for unset options.
check_arguments()
CONTINUE = True
FINAL_RC = -1

while CONTINUE:
    try_to_unpack(IN, OUT + '.tmp')

    RC = 0  # _rc0

    if RC == RET_UNPACK_OK or RC == RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK or RC == RET_UNPACKER_FAILED_OTHERS_OK:
        FINAL_RC = RC

        shutil.move(OUT + '.tmp', OUT)
        IN = OUT
    else:
        # Remove the temporary file, just in case some of the unpackers crashed
        # during unpacking and left it on the disk (e.g. upx).
        utils.remove_forced(OUT + '.tmp')

        CONTINUE = False

if FINAL_RC == -1:
    sys.exit(RC)
else:
    sys.exit(FINAL_RC)
