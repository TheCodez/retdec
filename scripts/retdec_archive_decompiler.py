#! /usr/bin/env python3

import argparse
import multiprocessing
import shutil
import sys
import os
import subprocess

import retdec_config as config
import retdec_utils as utils

"""Configuration.
Timeout for the decompilation script.
"""
TIMEOUT = 300
JSON_FORMAT = False
PLAIN_FORMAT = False
LIBRARY_PATH = ''
TMP_ARCHIVE = ''
DECOMPILER_SH_ARGS = ''
LIST_MODE = ''


def print_help():
    parser = argparse.ArgumentParser(description='Runs the decompilation script with the given optional arguments over'
                                                 ' all files in the given static library or prints list of files in'
                                                 ' plain text with --plain argument or in JSON format with'
                                                 ' --json argument. You can pass arguments for decompilation after'
                                                 ' double-dash ' - -' argument.')

    """
    print('Runs the decompilation script with the given optional arguments over all files',file=file(str(_p1),'wb'))
    print('in the given static library or prints list of files in plain text',file=file(str(_p1),'wb'))
    print('with --plain argument or in JSON format with --json argument. You',file=file(str(_p1),'wb'))
    print('can pass arguments for decompilation after double-dash '--' argument.',file=file(str(_p1),'wb'))
    print('Usage:',file=file(str(_p1),'wb'))
    print('    ' + __file__ + ' ARCHIVE [-- ARGS]',file=file(str(_p1),'wb'))
    print('    ' + __file__ + ' ARCHIVE --plain|--json',file=file(str(_p1),'wb'))
    """


def print_error_plain_or_json(error):
    """Prints error in either plain text or JSON format.
    One argument required: error message.
    """
    if JSON_FORMAT != '':
        M = os.popen('echo \'' + error + '\' | sed \'s,\\\\,\\\\\\\\,g\'').read().rstrip('\n')
        M = os.popen('echo \'' + M + '\' | sed \'s,\\, \\\\,g\'').read().rstrip('\n')
        print('{')
        print('    \'error\' : \'' + M + '\'')
        print('}')
        exit(1)
    else:
        # Otherwise print in plain text.
        utils.print_error_and_die(error)


def cleanup(path):
    """Cleans up all temporary files.
    No arguments accepted.
    """
    if path is '':
        return

    for n in os.listdir(path):
        p = os.path.join(path, n)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.unlink(p)


"""Parse script arguments."""
while len(sys.argv) > 1:

    if str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help':
        print_help()
        exit(0)
    elif str(sys.argv[1]) == '--list':
        LIST_MODE = 1
        subprocess.call(['shift'], shell=True)
    elif str(sys.argv[1]) == '--plain':
        if JSON_FORMAT:
            utils.print_error_and_die('Arguments --plain and --json are mutually exclusive.')

        LIST_MODE = 1
        PLAIN_FORMAT = 1
        subprocess.call(['shift'], shell=True)
    elif sys.argv[1] == '--json':
        if PLAIN_FORMAT:
            utils.print_error_and_die('Arguments --plain and --json are mutually exclusive.')
        LIST_MODE = 1
        JSON_FORMAT = 1
        subprocess.call(['shift'], shell=True)
    elif sys.argv[1] == '--':
        # Skip -- and store arguments for decompilation.
        subprocess.call(['shift'], shell=True)
        DECOMPILER_SH_ARGS = " ".join(sys.argv[1:])  # Expand.star(0)
        break
    else:
        if not (os.path.isfile(str(sys.argv[1]))):
            utils.print_error_and_die('Input '' + str(sys.argv[1]) + '' is not a valid file.')

        LIBRARY_PATH = sys.argv[1]
        subprocess.call(['shift'], shell=True)

# Check arguments
if not LIBRARY_PATH != '':
    print_error_plain_or_json('No input file.')

# Check for archives packed in Mach-O Universal Binaries.
if utils.is_macho_archive(LIBRARY_PATH):
    if LIST_MODE != '':
        if str(JSON_FORMAT) != '':
            subprocess.call([str(config.EXTRACT), '--objects', '--json', str(LIBRARY_PATH)], shell=True)
        else:
            # Otherwise print in plain text.
            subprocess.call([str(config.EXTRACT), '--objects', str(LIBRARY_PATH)], shell=True)
        # Not sure why failure is used there.
        exit(1)
    TMP_ARCHIVE = str(LIBRARY_PATH) + '.a'
    subprocess.call([str(config.EXTRACT), '--best', '--out', str(TMP_ARCHIVE), str(LIBRARY_PATH)], shell=True)
    LIBRARY_PATH = TMP_ARCHIVE

# Check for thin archives.
if utils.has_thin_archive_signature(LIBRARY_PATH) == 0:
    print_error_plain_or_json('File is a thin archive and cannot be decompiled.')

# Check if file is archive
if not utils.is_valid_archive(LIBRARY_PATH):
    print_error_plain_or_json('File is not supported archive or is not readable.')

# Check number of files.
FILE_COUNT = utils.archive_object_count(LIBRARY_PATH)
if FILE_COUNT <= 0:
    print_error_plain_or_json('No files found in archive.')

"""List only mode."""
if LIST_MODE != '':
    if JSON_FORMAT:
        utils.archive_list_numbered_content_json(LIBRARY_PATH)
    else:
        # Otherwise print in plain text.
        utils.archive_list_numbered_content(LIBRARY_PATH)
    cleanup(TMP_ARCHIVE)
    exit(0)

"""Run the decompilation script over all the found files."""
print('Running \`' + config.DECOMPILER_SH, end='')

if DECOMPILER_SH_ARGS != '':
    print(DECOMPILER_SH_ARGS, end='')

print('\` over ' + str(FILE_COUNT) + ' files with timeout ' + str(TIMEOUT) + 's', '(run \`kill ' + str(os.getpid())
      + '\` to terminate this script)...', file=sys.stderr)


def decompile():
    for i in range(FILE_COUNT):
        file_index = (i + 1)
        print('-ne', str(file_index) + '/' + str(FILE_COUNT) + '\t\t')

        # We have to use indexes instead of names because archives can contain multiple files with same name.
        log_file = LIBRARY_PATH + '.file_' + str(file_index) + '.log.verbose'
        # Do not escape!
        subprocess.call(
            config.DECOMPILER_SH + ' ' + '--ar-index=' + str(i) + ' ' + '-o' + ' ' + LIBRARY_PATH + '.file_' + str(
                file_index) + '.c' + ' ' + LIBRARY_PATH + ' ' + DECOMPILER_SH_ARGS, shell=True,
            stdout=open(log_file, 'wb'), stderr=subprocess.STDOUT)


p = multiprocessing.Process(target=decompile())
p.start()

# Wait for 10 seconds or until process finishes
p.join(TIMEOUT)

# If thread is still active
if p.is_alive():
    print('[TIMEOUT]')

    # Terminate
    p.terminate()
    p.join()
else:
    print('[OK]')

'''
while INDEX < FILE_COUNT:
    FILE_INDEX = (INDEX  +  1)
    print('-ne', str(FILE_INDEX) + '/' + str(FILE_COUNT) + '\t\t')

    # We have to use indexes instead of names because archives can contain multiple files with same name.
    LOG_FILE = str(LIBRARY_PATH) + '.file_' + str(FILE_INDEX) + '.log.verbose'
    # Do not escape!
    subprocess.call('gnutimeout'  +  ' '  +  str(TIMEOUT)  +  ' '  +  str(DECOMPILER_SH)  +  ' '  +  '--ar-index=' + 
    str(INDEX) +  ' '  +  '-o'  +  ' '  +  str(LIBRARY_PATH) + '.file_' + str(FILE_INDEX) + '.c'  +  ' '
      +  str(LIBRARY_PATH) +  ' '  +  str(DECOMPILER_SH_ARGS),shell=True,stdout=file(str(LOG_FILE),'wb'),
      stderr=subprocess.STDOUT)
    
    RC = _rc0
    # Print status.
    
    if str(RC) == '0':
        print('[OK]')
    elif str(RC) == '124':
        print('[TIMEOUT]')
    else:
        print('[FAIL]')
    INDEX + = 1
'''

# Cleanup
cleanup(TMP_ARCHIVE)
# Success!
exit(0)
