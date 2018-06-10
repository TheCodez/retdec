#! /usr/bin/env python3

"""Generates JSON files from includes in Windows SDK and Windows Drivers Kit."""

import argparse
import shutil
import sys
import os
import subprocess

#
# Paths.
#

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = __name__
EXTRACTOR = (SCRIPT_DIR + '/extract_types.py')
MERGER = (SCRIPT_DIR + '/merge_jsons.py')
OUT_DIR = '.'

#
# Windows SDK paths.
#
WIN_UCRT_OUT_DIR = (OUT_DIR + '/windows_ucrt')
WIN_SHARED_OUT_DIR = (OUT_DIR + '/windows_shared')
WIN_UM_OUT_DIR = (OUT_DIR + '/windows_um')
WIN_WINRT_OUT_DIR = (OUT_DIR + '/windows_winrt')
WIN_NETFX_OUT_DIR = (OUT_DIR + '/windows_netfx')
WIN_OUT_JSON = (OUT_DIR + '/windows.json')
WIN_OUT_JSON_WITH_UNUSED_TYPES = (OUT_DIR + '/windows_all_types.json')
#
# Windows Drivers Kit paths.
#
WDK_KM_OUT_DIR = (OUT_DIR + '/windrivers_km')
WDK_MMOS_OUT_DIR = (OUT_DIR + '/windrivers_mmos')
WDK_SHARED_OUT_DIR = (OUT_DIR + '/windrivers_shared')
WDK_UM_OUT_DIR = (OUT_DIR + '/windrivers_um')
WDK_KMDF_OUT_DIR = (OUT_DIR + '/windrivers_kmdf')
WDK_UMDF_OUT_DIR = (OUT_DIR + '/windrivers_umdf')
WDK_OUT_JSON = (OUT_DIR + '/windrivers.json')


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-i', '--json-indent',
                        dest='json_indent',
                        default=1,
                        help='Set indentation in JSON files.')

    parser.add_argument('-n', '--no-cleanup',
                        dest='no_cleanup',
                        default=True,
                        help='Do not remove dirs with JSONs for individual header files.')

    parser.add_argument('--sdk',
                        dest='sdk',
                        help='SDK dir')

    parser.add_argument('--wdk',
                        dest='wdk',
                        help='WDK dir')

    return parser.parse_args()


args = parse_args()

#
# Prints the given error message ($1) to stderr and exits.
#
def print_error_and_die(error):
    sys.stderr.write('Error: ' + error)
    # exit(1)


def remove_dir(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)


#
# Removes temporary dirs and files used to generate JSONS that are merged later.
#
def remove_tmp_dirs_and_files():

    remove_dir(WIN_UCRT_OUT_DIR)
    remove_dir(WIN_SHARED_OUT_DIR)
    remove_dir(WIN_UM_OUT_DIR)
    remove_dir(WIN_WINRT_OUT_DIR)
    remove_dir(WIN_NETFX_OUT_DIR)
    remove_dir(WIN_OUT_JSON_WITH_UNUSED_TYPES)
    remove_dir(WDK_KM_OUT_DIR)
    remove_dir(WDK_MMOS_OUT_DIR)
    remove_dir(WDK_SHARED_OUT_DIR)
    remove_dir(WDK_UM_OUT_DIR)
    remove_dir(WDK_KMDF_OUT_DIR)
    remove_dir(WDK_UMDF_OUT_DIR)


#
# Parse and check script arguments.
#
"""
while (True):
    
    if ( (sys.argv[1])  =  =  '-i' or (sys.argv[1])  =  =  '--json-indent'):
        if (JSON_INDENT) ! =  '':
            print_error_and_die('Duplicate option: -i|--json-indent')
        JSON_INDENT = (sys.argv[2])
        subprocess.call(['shift','2'],shell = True)
    elif ( (sys.argv[1])  =  =  '-h' or (sys.argv[1])  =  =  '--help'):
        print_help()
        exit(0)
    elif ( (sys.argv[1])  =  =  '-N' or (sys.argv[1])  =  =  '--no-cleanup'):
        if (CLEANUP) ! =  '':
            print_error_and_die('Duplicate option: -N|--no-cleanup')
        CLEANUP = ('no')
        subprocess.call(['shift'],shell = True)
    elif ( (sys.argv[1])  =  =  '--sdk'):
        args.sdk = (sys.argv[2])
        if (not os.access((args.sdk),R_OK) ):
            print_error_and_die((args.sdk)+': No such file or directory')
        subprocess.call(['shift','2'],shell = True)
    elif ( (sys.argv[1])  =  =  '--wdk'):
        args.wdk = (sys.argv[2])
        if (not os.access((args.wdk),R_OK) ):
            print_error_and_die((args.wdk)+': No such file or directory')
        subprocess.call(['shift','2'],shell = True)
    elif ( (sys.argv[1])  =  =  '--'):
        if (Expand.hash() ! =  1 ):
            print_error_and_die('Invalid options: ''+(sys.argv[2])+''')
            exit(1)
        break
"""

# Path to the Windows SDK directory is required.
if not args.sdk or not args.wdk:
    print_error_and_die('Path to the Windows SDK directory is required')
    exit(1)

WIN_UCRT_IN_DIR = (args.sdk + '/10/Include/10.0.10150.0/ucrt')
WIN_SHARED_IN_DIR = (args.sdk + '/10/Include/10.0.10240.0/shared')
WIN_UM_IN_DIR = (args.sdk + '/10/Include/10.0.10240.0/um')
WIN_WINRT_IN_DIR = (args.sdk + '/10/Include/10.0.10240.0/winrt')
WIN_NETFX_IN_DIR = (args.sdk + '/NETFXSDK/4.6/Include/um')
WDK_KM_IN_DIR = (args.wdk + '/10.0.10586.0/km')
WDK_MMOS_IN_DIR = (args.wdk + '/10.0.10586.0/mmos')
WDK_SHARED_IN_DIR = (args.wdk + '/10.0.10586.0/shared')
WDK_UM_IN_DIR = (args.wdk + '/10.0.10586.0/um')
WDK_KMDF_IN_DIR = (args.wdk + '/wdf/kmdf')
WDK_UMDF_IN_DIR = (args.wdk + '/wdf/umdf')

#
# Initial cleanup.
#
remove_tmp_dirs_and_files()

os.makedirs(WIN_UCRT_OUT_DIR, exist_ok=True)
os.makedirs(WIN_SHARED_OUT_DIR, exist_ok=True)
os.makedirs(WIN_UM_OUT_DIR, exist_ok=True)
os.makedirs(WIN_WINRT_OUT_DIR, exist_ok=True)
os.makedirs(WIN_NETFX_OUT_DIR, exist_ok=True)
os.makedirs(WDK_KM_OUT_DIR, exist_ok=True)
os.makedirs(WDK_MMOS_OUT_DIR, exist_ok=True)
os.makedirs(WDK_SHARED_OUT_DIR, exist_ok=True)
os.makedirs(WDK_UM_OUT_DIR, exist_ok=True)
os.makedirs(WDK_KMDF_OUT_DIR, exist_ok=True)
os.makedirs(WDK_UMDF_OUT_DIR, exist_ok=True)

#
# Parse the includes in the given Windows SDK directory and merge the generated
# JSON files.
#
subprocess.call([EXTRACTOR, WIN_UCRT_IN_DIR, '-o', WIN_UCRT_OUT_DIR], shell=True)
subprocess.call([EXTRACTOR, WIN_SHARED_IN_DIR, '-o', WIN_SHARED_OUT_DIR], shell=True)
subprocess.call([EXTRACTOR, WIN_UM_IN_DIR, '-o', WIN_UM_OUT_DIR], shell=True)
subprocess.call([EXTRACTOR, WIN_WINRT_IN_DIR, '-o', WIN_WINRT_OUT_DIR], shell=True)
subprocess.call([EXTRACTOR, WIN_NETFX_IN_DIR, '-o', WIN_NETFX_OUT_DIR], shell=True)
subprocess.call([MERGER, WIN_SHARED_OUT_DIR, WIN_UM_OUT_DIR, WIN_UCRT_OUT_DIR, WIN_WINRT_OUT_DIR,
                 WIN_NETFX_OUT_DIR, '-o', WIN_OUT_JSON, '--json-indent', args.json_indent], shell=True)

#
# Parse the includes in the given WDK directory and merge the generated
# JSON files.
#
subprocess.call([EXTRACTOR, WDK_KM_IN_DIR, '-o', WDK_KM_OUT_DIR], shell=True)
subprocess.call([EXTRACTOR, WDK_MMOS_IN_DIR, '-o', WDK_MMOS_OUT_DIR], shell=True)
subprocess.call([EXTRACTOR, WDK_SHARED_IN_DIR, '-o', WDK_SHARED_OUT_DIR], shell=True)
subprocess.call([EXTRACTOR, WDK_UM_IN_DIR, '-o', WDK_UM_OUT_DIR], shell=True)

for d in os.listdir(WDK_KMDF_IN_DIR):
    subprocess.call([EXTRACTOR, WDK_KMDF_IN_DIR + '/' + d, '-o', WDK_KMDF_OUT_DIR], shell=True)

for d in os.listdir(WDK_UMDF_IN_DIR):
    subprocess.call([EXTRACTOR, WDK_UMDF_IN_DIR + '/' + d, '-o', WDK_UMDF_OUT_DIR], shell=True)

subprocess.call([MERGER, WDK_SHARED_OUT_DIR, WDK_UM_OUT_DIR, WDK_KM_OUT_DIR, WDK_MMOS_OUT_DIR,
                 WDK_KMDF_OUT_DIR, WDK_UMDF_OUT_DIR, '-o', WDK_OUT_JSON, '--json-indent', args.json_indent],
                shell=True)

#
# WDK uses many types defined in Windows SDK. We need SDK JSON with all types extracted
# and merge it with WDK. SDK functions must be removed!
#
subprocess.call([MERGER, WIN_SHARED_OUT_DIR, WIN_UM_OUT_DIR, WIN_UCRT_OUT_DIR, WIN_WINRT_OUT_DIR,
                 WIN_NETFX_OUT_DIR, '-o', WIN_OUT_JSON_WITH_UNUSED_TYPES, '--json-indent', args.json_indent,
                 '--keep-unused-types'], shell=True)

if args.json_indent == 0:
    subprocess.call(['sed', '-i', '-e', 's/^.*\}, \'types\': \{/\{\'functions\': \{\}, \'types\': \{/',
                     WIN_OUT_JSON_WITH_UNUSED_TYPES], shell=True)
else:
    TYPES_LINE_NUMBER = 0  # (os.popen('egrep -n \'^s*'types': {\' \''+(WIN_OUT_JSON_WITH_UNUSED_TYPES)+'\' | cut -f1 -d:').read().rip('\n'))
    TYPES_LINE_NUMBER = (TYPES_LINE_NUMBER - 1)
    subprocess.call(['sed', '-i', '-e', '1,' + TYPES_LINE_NUMBER + ' d', WIN_OUT_JSON_WITH_UNUSED_TYPES], shell=True)
    subprocess.call(['sed', '-i', '-e', '1s/^/\{\'functions\': \{\},\n/', WIN_OUT_JSON_WITH_UNUSED_TYPES], shell=True)

subprocess.call(
    [MERGER, WDK_OUT_JSON, WIN_OUT_JSON_WITH_UNUSED_TYPES, '-o', WDK_OUT_JSON, '--json-indent', args.json_indent],
    shell=True)

#
# Optional cleanup at the end.
#
if not args.no_cleanup:
    remove_tmp_dirs_and_files()
