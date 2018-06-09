#! /usr/bin/env python3

import argparse
import multiprocessing
import os
import subprocess
import sys

import retdec_config as config
import retdec_utils as utils

time_out = 300
use_json_format = False
use_plain_format = False
library_path = ''
tmp_archive = ''
decompiler_sh_args = ''
enable_list_mode = False
file_count = 0


def get_parser():
    parser = argparse.ArgumentParser(description='Runs the decompilation script with the given optional arguments over'
                                                 ' all files in the given static library or prints list of files in'
                                                 ' plain text with --plain argument or in JSON format with'
                                                 ' --json argument. You can pass arguments for decompilation after'
                                                 ' double-dash -- argument.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--plain",
                        dest="plain_format",
                        help="print list of files in plain text")

    parser.add_argument("--json",
                        dest="json_format",
                        help="print list of files in json format")

    parser.add_argument("--args",
                        nargs='+',
                        dest="arg_list",
                        help="args passed to the decompiler")

    parser.add_argument("--list",
                        dest="list_mode",
                        help="list")

    parser.add_argument("file",
                        help="path")

    return parser


def print_error_plain_or_json(error):
    """Prints error in either plain text or JSON format.
    One argument required: error message.
    """
    if use_json_format != '':
        message = os.popen('echo \'' + error + '\' | sed \'s,\\\\,\\\\\\\\,g\'').read().rstrip('\n')
        message = os.popen('echo \'' + message + '\' | sed \'s,\\, \\\\,g\'').read().rstrip('\n')
        print('{')
        print('    \'error\' : \'' + message + '\'')
        print('}')
        exit(1)
    else:
        # Otherwise print in plain text.
        utils.print_error_and_die(error)


def cleanup():
    """Cleans up all temporary files.
    No arguments accepted.
    """

    utils.remove_forced(tmp_archive)


def decompile():
    global file_count

    for i in range(file_count):
        file_index = (i + 1)
        print('-ne', str(file_index) + '/' + str(file_count) + '\t\t')

        # We have to use indexes instead of names because archives can contain multiple files with same name.
        log_file = library_path + '.file_' + str(file_index) + '.log.verbose'
        # Do not escape!

        subprocess.call('%s --ar-index=%d -o %s.file_%d.c %s %s' % (
            config.DECOMPILER_SH, i, library_path, file_index, library_path, decompiler_sh_args), shell=True,
                        stdout=open(log_file, 'wb'), stderr=subprocess.STDOUT)


def parse_args(_args):
    global use_json_format
    global use_plain_format
    global enable_list_mode
    global decompiler_sh_args
    global library_path

    if _args.list_mode:
        enable_list_mode = True

    if _args.plain_format:
        if use_json_format:
            utils.print_error_and_die('Arguments --plain and --json are mutually exclusive.')

        enable_list_mode = True
        use_plain_format = True

    if _args.json_format:
        if use_plain_format:
            utils.print_error_and_die('Arguments --plain and --json are mutually exclusive.')
        enable_list_mode = True
        use_json_format = True

    if _args.arg_list:
        decompiler_sh_args = ' '.join(_args.arg_list)  # Expand.star(0)

    if _args.file:
        if not (os.path.isfile(_args.file)):
            utils.print_error_and_die('Input %s is not a valid file.' % _args.file)

        library_path = _args.file


def main(_args):
    global library_path
    global tmp_archive
    global file_count

    parse_args(_args)

    # Check arguments
    if library_path == '':
        print_error_plain_or_json('No input file.')

    # Check for archives packed in Mach-O Universal Binaries.
    if utils.is_macho_archive(library_path):
        if enable_list_mode:
            if use_json_format:
                subprocess.call([config.EXTRACT, '--objects', '--json', library_path], shell=True)
            else:
                subprocess.call([config.EXTRACT, '--objects', library_path], shell=True)
            sys.exit(1)

        tmp_archive = library_path + '.a'
        subprocess.call([config.EXTRACT, '--best', '--out', tmp_archive, library_path], shell=True)
        library_path = tmp_archive

    # Check for thin archives.
    if utils.has_thin_archive_signature(library_path) == 0:
        print_error_plain_or_json('File is a thin archive and cannot be decompiled.')

    # Check if file is archive
    if not utils.is_valid_archive(library_path):
        print_error_plain_or_json('File is not supported archive or is not readable.')

    # Check number of files.
    file_count = utils.archive_object_count(library_path)
    if file_count <= 0:
        print_error_plain_or_json('No files found in archive.')

    # List only mode.
    if enable_list_mode:
        if use_json_format:
            utils.archive_list_numbered_content_json(library_path)
        else:
            utils.archive_list_numbered_content(library_path)
        cleanup()
        sys.exit(0)

    # Run the decompilation script over all the found files.
    print('Running \`%s' % config.DECOMPILER_SH, end='')

    if decompiler_sh_args != '':
        print(decompiler_sh_args, end='')

    print('\` over %d files with timeout %d s. (run \`kill %d \` to terminate this script)...' % (
        file_count, time_out, os.getpid()), file=sys.stderr)

    p = multiprocessing.Process(target=decompile())
    p.start()
    p.join(time_out)

    if p.is_alive():
        print('[TIMEOUT]')
        p.terminate()
        p.join()
    else:
        print('[OK]')

    cleanup()
    sys.exit(0)


args = get_parser().parse_args()
main(args)
