#! /usr/bin/env python3
"""Compilation and decompilation utility functions.
"""

from __future__ import print_function

import os
import pathlib
import re
import subprocess
import sys

SCRIPT_DIR = os.popen("dirname \"" + os.popen("gnureadlink -e \"" + __file__ + "\"").read().rstrip("\n") + "\"").read() \
    .rstrip("\n")
if config.DECOMPILER_CONFIG == '':
    DECOMPILER_CONFIG = SCRIPT_DIR + "/retdec-config.sh"

_rc0 = subprocess.call([".", config.DECOMPILER_CONFIG], shell=True)


def get_realpath(path):
    """Prints the real, physical location of a directory or file, relative or
    absolute.
    1 argument is needed
    """
    return pathlib.Path(path).resolve()


def print_error_and_die(error):
    """Print error message to stderr and die.
    1 argument is needed
    Returns - 1 if number of arguments is incorrect
    """
    if error is None:
        exit(1)

    print("Error: " + error, file=sys.stderr)
    exit(1)


def print_warning(warning):
    """Print warning message to stderr.
    """
    if warning is None:
        return

    print("Warning: " + warning, file=sys.stderr)


def has_archive_signature(path):
    """Check if file has any ar signature.
    1 argument is needed - file path
    Returns - 0 if file has ar signature
              1 if number of arguments is incorrect
              2 no signature
    """
    if subprocess.call([config.AR, path, "--arch-magic"], shell=True):
        return 0
    return 2


def has_thin_archive_signature(path):
    """Check if file has thin ar signature.
    1 argument is needed - file path
    Returns - 0 if file has thin ar signature
              1 if number of arguments is incorrect
              2 no signature
    """
    if subprocess.call([config.AR, path, "--thin-magic"], shell=True):
        return 0
    return 2


def is_valid_archive(path):
    """Check if file is an archive we can work with.
    1 argument is needed - file path
    Returns - 0 if file is valid archive
              1 if file is invalid archive
    """
    # We use our own messages so throw original output away.
    _rc0 = subprocess.call(config.AR + " " + path + " " + "--valid", shell=True, stderr=subprocess.STDOUT,
                           stdout=None)


def archive_object_count(path):
    """Counts object files in archive.
    1 argument is needed - file path
    Returns - 1 if error occurred
    """
    _rc0 = subprocess.call([config.AR, path, "--object-count"], shell=True)


def archive_list_content(path):
    """Print content of archive.
    1 argument is needed - file path
    Returns - 1 if number of arguments is incorrect
    """
    _rc0 = subprocess.call([config.AR, path, "--list", "--no-numbers"], shell=True)


def archive_list_numbered_content(path):
    """Print numbered content of archive.
    1 argument is needed - file path
    Returns - 1 if number of arguments is incorrect
    """
    print("Index\tName")
    _rc0 = subprocess.call([config.AR, path, "--list"], shell=True)


def archive_list_numbered_content_json(path):
    """Print numbered content of archive in JSON format.
    1 argument is needed - file path
    Returns - 1 if number of arguments is incorrect
    """
    _rc0 = subprocess.call([config.AR, path, "--list", "--json"], shell=True)


def archive_get_by_name(path, name, output):
    """Get a single file from archive by name.
    3 arguments are needed - path to the archive
                           - name of the file
                           - output path
    Returns - 1 if number of arguments is incorrect
            - 2 if error occurred
    """
    if (not subprocess.call(config.AR + " " + path + " " + "--name" + " " + name + " " + "--output" + " " + output,
                            shell=True, stderr=subprocess.STDOUT, stdout=None)):
        return 2

    return 1


def archive_get_by_index(archive, index, output):
    """Get a single file from archive by index.
    3 arguments are needed - path to the archive
                           - index of the file
                           - output path
    Returns - 1 if number of arguments is incorrect
            - 2 if error occurred
    """
    if (not subprocess.call(
            config.AR + " " + archive + " " + "--index" + " " + index + " " + "--output" + " " + output,
            shell=True, stderr=subprocess.STDOUT, stdout=None)):
        return (2)


def is_macho_archive(path):
    """Check if file is Mach-O universal binary with archives.
    1 argument is needed - file path
    Returns - 0 if file is archive
              1 if file is not archive
    """
    _rc0 = subprocess.call(str(config.EXTRACT) + " " + "--check-archive" + " " + path, shell=True,
                           stderr=subprocess.STDOUT, stdout=None)


def is_decimal_number(num):
    """Check string is a valid decimal number.
        1 argument is needed - string to check.
        Returns - 0 if string is a valid decimal number.
                  1 otherwise
    """
    regex = "^[0-9]+$"
    if re.search(regex, num):
        return True
    else:
        return False


def is_hexadecimal_number(num):
    """Check string is a valid hexadecimal number.
        1 argument is needed - string to check.
        Returns - 0 if string is a valid hexadecimal number.
                  1 otherwise
    """
    regex = "^0x[0-9a-fA-F]+$"
    if re.search(regex, num):
        return True
    else:
        return False


def is_number(num):
    """Check string is a valid number (decimal or hexadecimal).
        1 argument is needed - string to check.
        Returns - 0 if string is a valid number.
                  1 otherwise
    """
    if is_decimal_number(num):
        return True

    if is_hexadecimal_number(num):
        return True

    return False


def is_decimal_range(num):
    """Check string is a valid decimal range.
        1 argument is needed - string to check.
        Returns - 0 if string is a valid decimal range.
                  1 otherwise
    """
    regex = "^[0-9]+-[0-9]+$"
    if re.search(regex, num):
        return True
    else:
        return False


def is_hexadecimal_range(num):
    """Check string is a valid hexadecimal range
        1 argument is needed - string to check.
        Returns - 0 if string is a valid hexadecimal range
                  1 otherwise
    """
    regex = "^0x[0-9a-fA-F]+-0x[0-9a-fA-F]+$"
    if re.search(regex, num):
        return True
    else:
        return False


def is_range(num):
    """Check string is a valid range (decimal or hexadecimal).
        1 argument is needed - string to check.
        Returns - 0 if string is a valid range
                  1 otherwise
    """
    if is_decimal_range(num):
        return True

    if is_hexadecimal_range(num):
        return True

    return False
