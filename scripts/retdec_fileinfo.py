#! /usr/bin/env python3

import argparse
import subprocess
import sys

import retdec_config as config
import retdec_utils as utils

"""When analyzing an archive, use the archive decompilation script `--list` instead of
`fileinfo` because fileinfo is currently unable to analyze archives.

First, we have to find path to the input file. We take the first parameter
that does not start with a dash. This is a simplification and may not work in
all cases. A proper solution would need to parse fileinfo parameters, which
would be complex.
"""


def get_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("-j", "--json",
                        dest="json",
                        action='store_true',
                        help="Set to forward --json to the archive decompilation script.")

    parser.add_argument("--use-external-patterns",
                        dest="external_patterns",
                        action='store_true',
                        help="Should use external patterns")

    parser.add_argument('file',
                        help='The input file')

    return parser


def main(_args):
    if utils.has_archive_signature(_args.file):
        # The input file is not an archive.

        # The input file is an archive, so use the archive decompilation script
        # instead of fileinfo.
        archive_decompiler_args = _args.file + " --list"

        res = subprocess.call([config.ARCHIVE_DECOMPILER, archive_decompiler_args], shell=True)

        sys.exit(res)

    # We are not analyzing an archive, so proceed to fileinfo.
    fileinfo_params = []

    for par in config.FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES:
        fileinfo_params.append('--crypto ' + par)

    if _args.external_patterns:
        for par in config.FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES:
            fileinfo_params.append('--crypto ' + par)

    subprocess.call([config.FILEINFO, ' '.join(fileinfo_params)], shell=True)


args = get_parser().parse_args()
main(args)
