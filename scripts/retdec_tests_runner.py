#! /usr/bin/env python3

"""Runs all the installed unit tests."""

import sys
import os
import subprocess

unit_tests_dir = ''

"""First argument can be verbose."""
if sys.argv[1] == '-v' or sys.argv[1] == '--verbose':
    verbose = True
else:
    verbose = False


def print_colored(message, color):
    """Emits a colored version of the given message to the standard output (without
    a new line).
       2 string argument are needed:
       $1 message to be colored
       $2 color (red, green, yellow)

    If the color is unknown, it emits just $1.
    """

    if color == 'red':
        print('\033[22;31m' + message + '\033[0m')

    elif color == 'green':
        print('\033[22;32m' + message + '\033[0m')

    elif color == 'yellow':
        print('\033[01;33m' + message + '\033[0m')

    else:
        print(message + '\n')


def unit_tests_in_dir(path):
    """Prints paths to all unit tests in the given directory.
    1 string argument is needed:
        $1 path to the directory with unit tests
    """

    """On macOS, find does not support the '-executable' parameter (#238).
    Therefore, on macOS, we have to use '-perm +111'. To explain, + means
    'any of these bits' and 111 is the octal representation for the
    executable bit on owner, group, and other. Unfortunately, we cannot use
    '-perm +111' on all systems because find on Linux/MSYS2 does not support
    +. It supports only /, but this is not supported by find on macOS...
    Hence, we need an if.
    """

    if sys.platform == 'darwin':
        executable_flag = '-perm +111'
    else:
        executable_flag = '-executable'

    _rc0 = _rcr2, _rcw2 = os.pipe()
    if os.fork():
        os.close(_rcw2)
        os.dup2(_rcr2, 0)
        _rcr3, _rcw3 = os.pipe()
        if os.fork():
            os.close(_rcw3)
            os.dup2(_rcr3, 0)
            subprocess.call(['sort'], shell=True)
        else:
            os.close(_rcr3)
            os.dup2(_rcw3, 1)
            subprocess.call(['grep', '-v', '\\.sh$'], shell=True)
            #sys.exit(0)

    else:
        os.close(_rcr2)
        os.dup2(_rcw2, 1)
        return subprocess.check_output(['find', path, '-name', 'retdec-tests-*', '-type', 'f', executable_flag], shell=True)
        #sys.exit(0)


def run_unit_tests_in_dir(path):
    """Runs all unit tests in the given directory.
    1 string argument is needed:

        $1 path to the directory with unit tests

    Returns 0 if all tests passed, 1 otherwise.
    """

    global unit_tests_dir

    unit_tests_dir = path
    tests_failed = False
    tests_run = False

    for unit_test in unit_tests_in_dir(unit_tests_dir):
        print()
        unit_test_name = os.popen('sed \'s/^.*/bin///' << '\'' + unit_test + '\'').read().rstrip('\n')
        print_colored(unit_test_name, 'yellow')
        print()

        if not verbose:
            subprocess.call([unit_test, '--gtest_color=yes'], shell=True)
        else:
            _rcr7, _rcw7 = os.pipe()
            if os.fork():
                os.close(_rcw7)
                os.dup2(_rcr7, 0)
                _rcr8, _rcw8 = os.pipe()
                if os.fork():
                    os.close(_rcw8)
                    os.dup2(_rcr8, 0)
                    _rcr9, _rcw9 = os.pipe()
                    if os.fork():
                        os.close(_rcw9)
                        os.dup2(_rcr9, 0)
                        subprocess.call(['grep', '-v', 'Running main() from gmock_main.cc'], shell=True)
                    else:
                        os.close(_rcr9)
                        os.dup2(_rcw9, 1)
                        subprocess.call(['grep', '-v', '^' + '$'], shell=True)
                        sys.exit(0)

                else:
                    os.close(_rcr8)
                    os.dup2(_rcw8, 1)
                    subprocess.call(['grep', '-v', 'RUN\|OK\|----------\|=========='], shell=True)
                    sys.exit(0)

            else:
                os.close(_rcr7)
                os.dup2(_rcw7, 1)
                subprocess.call([unit_test, '--gtest_color=yes'], shell=True)
                sys.exit(0)

        return_code = 0  # PIPESTATUS[0]
        if return_code != 0:
            tests_failed = True
            if return_code >= 127:
                # Segfault, floating-point exception, etc.
                print_colored('FAILED (return code %d)\n' % return_code, 'red')
        tests_run = True

    if tests_failed or not tests_run:
        return 1
    else:
        return 0


if not os.path.isdir(unit_tests_dir):
    '''Run all binaries in unit test dir.'''

    sys.stderr.write('error: no unit tests found in %s' % unit_tests_dir)
    sys.exit(1)

print('Running all unit tests in %s...' % unit_tests_dir)
run_unit_tests_in_dir(unit_tests_dir)
