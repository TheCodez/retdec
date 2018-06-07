#! /usr/bin/env python3

import sys
import os
import subprocess
import argparse

import retdec_config as config
import retdec_utils as utils


"""When analyzing an archive, use the archive decompilation script `--list` instead of
`fileinfo` because fileinfo is currently unable to analyze archives.

First, we have to find path to the input file. We take the first parameter
that does not start with a dash. This is a simplification and may not work in
all cases. A proper solution would need to parse fileinfo parameters, which
would be complex.
"""


def main(args):
    for arg in Expand.at():
        if (str(arg:0:1) != "-" ):
            IN = arg
            if not utils.has_archive_signature(IN):
                # The input file is not an archive.
                break
            # The input file is an archive, so use the archive decompilation script
            # instead of fileinfo.
            ARCHIVE_DECOMPILER_SH_PARAMS = "(" + IN + " --list)"
            # When a JSON output was requested (any of the parameters is
            # -j/--json), forward it to the archive decompilation script.
            for arg in Expand.at():
                if (if not str(arg) == "-j":
                    str(arg) == "--json" ):
                ARCHIVE_DECOMPILER_SH_PARAMS = "(--json)"
        res = subprocess.call(
            [config.ARCHIVE_DECOMPILER_SH, config.ARCHIVE_DECOMPILER_SH_PARAMS[ @]]], shell = True)

        exit(res)

        # We are not analyzing an archive, so proceed to fileinfo.
        FILEINFO_PARAMS = "()"
        for par in Array(config.FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES[ @]]):
            FILEINFO_PARAMS = "(--crypto " + par + ")"

        for var in Expand.at():
            if var == "--use-external-patterns":
                for par in Array(config.FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES[ @]]):
                    FILEINFO_PARAMS = "(--crypto " + par + ")"
                else:
                    FILEINFO_PARAMS = "(" + ar + ")"

        _rc0 = subprocess.call([str(config.FILEINFO), str(config.FILEINFO_PARAMS[ @]])], shell = True)


def get_parser():

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("-j", "--json",
                        dest="json",
                        default=False,
                        help="print list of files in plain text")

    return parser

args = get_parser().parse_args()

if __name__ == "__main__":
    main(args)
