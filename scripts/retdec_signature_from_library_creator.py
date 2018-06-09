#! /usr/bin/env python3

"""Create Yara rules file from static libraries."""
import argparse
import shutil
import sys
import os
import subprocess
import tempfile
from pathlib import Path

import retdec_utils as utils
import retdec_config as config

ignore_nop = ''
file_path = ''
tmp_dir_path = ''


def get_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-n', '--no-cleanup',
                        dest='no_cleanup',
                        action='store_true',
                        help='Temporary .pat files will be kept.')

    parser.add_argument('-o', '--output',
                        dest='output',
                        default='file-unpacked',
                        help='Where result(s) will be stored.')

    parser.add_argument('-m', '--min-pure',
                        dest='min_pure',
                        default=16,
                        help='Minimum pure information needed for patterns.')

    parser.add_argument('-i', '--ignore-nops',
                        dest='ignore_nops',
                        help='Ignore trailing NOPs when computing (pure) size.')

    parser.add_argument('-l', '--logfile',
                        dest='logfile',
                        action='store_true',
                        help='Add log-file with \'.log\' suffix from pat2yara.')

    parser.add_argument('-b', '--bin2pat-only',
                        dest='bin_to_pat_only',
                        action='store_true',
                        help='Stop after bin2pat.')

    parser.add_argument('input',
                        nargs='+',
                        help='Input file(s)')

    return parser


def die_with_error_and_cleanup(_args, message):
    """Exit with error message $1 and clean up temporary files.
    """

    # Cleanup.
    if not _args.no_cleanup:
        temporary_files_cleanup()

    utils.print_error_and_die(message + '.')


def temporary_files_cleanup():
    """Removes temporary files.
    """

    utils.remove_forced(tmp_dir_path)


def check_arguments(_args):
    global ignore_nop
    global file_path
    global tmp_dir_path

    if not _args.input:
        die_with_error_and_cleanup(_args, 'no input files')

    for f in _args.input:
        if not os.path.isfile(f):
            die_with_error_and_cleanup(_args, 'input %s is not a valid file nor argument' % f)

    # Output directory - compulsory argument.
    if not _args.output:
        die_with_error_and_cleanup(_args, 'option -o|--output is compulsory')
    else:
        file_path = _args.output
        dir_name = os.path.dirname(utils.get_realpath(file_path))
        tmp_dir_path = tempfile.mktemp(dir_name + '/XXXXXXXXX\'')

    if _args.ignore_nops:
        ignore_nop = '--ignore-nops'


def main(_args):
    check_arguments(_args)

    pattern_files = []
    object_dirs = []

    # Create .pat files for every library.
    for lib_path in _args.input:
        # Check for invalid archives.
        if not utils.is_valid_archive(lib_path):
            print('ignoring file '' + str(LIB_PATH) + '' - not valid archive')
            continue

        # Get library name for .pat file.
        lib_name = Path(lib_path).resolve().stem

        # Create sub-directory for object files.
        object_dir = tmp_dir_path + '/' + lib_name + '-objects'
        object_dirs = [object_dir]
        os.mkdir(object_dir)

        # Extract all files to temporary folder.
        subprocess.call([config.AR, lib_path, '--extract', '--output', object_dir], shell=True)

        # List all extracted objects.
        objects = []

        for root, dirs, files in os.walk(object_dir):
            for f in files:
                fname = os.path.join(root, f)
                if os.path.isfile(fname):
                    objects.append(fname)

        # Extract patterns from library.
        pattern_file = tmp_dir_path + '/' + lib_name + '.pat'
        pattern_files = [pattern_file]
        result = subprocess.call([config.BIN2PAT, '-o', pattern_file, ' '.join(objects)], shell=True)

        if result != 0:
            die_with_error_and_cleanup(_args, 'utility bin2pat failed when processing '' + str(LIB_PATH) + ''')

        # Remove extracted objects continuously.
        if not _args.no_cleanup:
            shutil.rmtree(object_dir)

    # Skip second step - only .pat files will be created.
    if _args.bin_to_pat_only:
        if not _args.no_cleanup:
            for d in object_dirs:
                shutil.rmtree(d)

        sys.exit(0)

    # Create final .yara file from .pat files.
    if _args.log_file:
        result = subprocess.call(
            [config.PAT2YARA, ' '.join(pattern_files), '--min-pure', _args.min_pure, '-o', file_path, '-l',
             file_path + '.log', ignore_nop, _args.ignore_nops], shell=True)

        if result != 0:
            die_with_error_and_cleanup(_args, 'utility pat2yara failed')
    else:
        result = subprocess.call(
            [config.PAT2YARA, ' '.join(pattern_files), '--min-pure', _args.min_pure, '-o', file_path, ignore_nop,
             _args.ignore_nops], shell=True)

        if result != 0:
            die_with_error_and_cleanup(_args, 'utility pat2yara failed')

    # Do cleanup.
    if not _args.no_cleanup:
        temporary_files_cleanup()


args = get_parser().parse_args()
main(args)
