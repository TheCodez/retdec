#! /usr/bin/env python3
import sys
import os
import subprocess
import argparse

import retdec_config as config

SCRIPT_DIR = os.popen("dirname \""+os.readlink(""+__file__+"\"").read().rstrip("\n")+"\"").read().rstrip("\n")

if str(config.DECOMPILER_UTILS) == '':
    config.DECOMPILER_UTILS = str(SCRIPT_DIR)+"/retdec-utils.sh"

_rc0 = subprocess.call([".",str(config.DECOMPILER_UTILS)],shell=True)


"""When analyzing an archive, use the archive decompilation script `--list` instead of
`fileinfo` because fileinfo is currently unable to analyze archives.

First, we have to find path to the input file. We take the first parameter
that does not start with a dash. This is a simplification and may not work in
all cases. A proper solution would need to parse fileinfo parameters, which
would be complex.
"""

for arg in Expand.at():
    if (str(arg:0:1) != "-" ):
        IN = arg
        if (not subprocess.call(["has_archive_signature",str(IN)],shell=True) ):
            # The input file is not an archive.
            break
        # The input file is an archive, so use the archive decompilation script
        # instead of fileinfo.
        ARCHIVE_DECOMPILER_SH_PARAMS = "("+str(IN)+" --list)"
        # When a JSON output was requested (any of the parameters is
        # -j/--json), forward it to the archive decompilation script.
        for arg in Expand.at():
            if (if not str(arg) == "-j":
                str(arg) == "--json" ):
                ARCHIVE_DECOMPILER_SH_PARAMS = "(--json)"
        subprocess.call([str(config.ARCHIVE_DECOMPILER_SH),str(config.ARCHIVE_DECOMPILER_SH_PARAMS[@] ])],shell=True)
        exit(_rc0)
# We are not analyzing an archive, so proceed to fileinfo.
FILEINFO_PARAMS="()"
for par in Array(config.FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES[@] ]):
    FILEINFO_PARAMS").setValue("(--crypto "+str(par)+")")
for var in Expand.at():
    if (str(var) == "--use-external-patterns" ):
        for par in Array(config.FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES[@] ]):
            FILEINFO_PARAMS = "(--crypto "+str(par)+")"
    else:
        FILEINFO_PARAMS = "("+str(var)+")"
_rc0 = subprocess.call([str(config.FILEINFO),str(config.FILEINFO_PARAMS[@] ])],shell=True)

def main(args):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-l', '--enable-logging', dest='enable_logging',
        action='store_true', default=False,
        help='enable emission of logging info'
    )
    parser.add_argument(
        '-o', '--output', dest='output',
        default='merge_output.json', help='choose output file'
    )

    return parser.parse_args()

args = parse_args()

if __name__ == "__main__":
    main(args)