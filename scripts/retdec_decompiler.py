#! /usr/bin/env python3

"""Decompiles the given file into the selected target high-level language."""

import argparse
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import retdec_config as config
from retdec_utils import Utils


def get_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-a', '--arch',
                        dest='arch',
                        choices=['mips', 'pic32', 'arm', 'thumb', 'powerpc', 'x86'],
                        help='Specify target architecture [mips|pic32|arm|thumb|powerpc|x86]. Required if it cannot be autodetected from the input (e.g. raw mode, Intel HEX).')

    parser.add_argument('-e', '--endian',
                        dest='endian',
                        choices=['little', 'big'],
                        help='Specify target endianness [little|big]. Required if it cannot be autodetected from the input (e.g. raw mode, Intel HEX).')

    parser.add_argument('-k', '--keep-unreachable-funcs',
                        dest='keep_unreachable_funcs',
                        action='store_true',
                        help='Keep functions that are unreachable from the main function.')

    parser.add_argument('-l', '--target-language',
                        dest='target_language',
                        default='c',
                        choices=['c', 'py'],
                        help='Target high-level language [c|py].')

    parser.add_argument('-m', '--mode',
                        dest='mode',
                        choices=['bin', 'll', 'raw'],
                        help='Force the type of decompilation mode [bin|ll|raw] (default: ll if input\'s suffix is \'.ll\', bin otherwise).')

    parser.add_argument('-o', '--output',
                        dest='output',
                        default='file.ext',
                        help='Output file.')

    parser.add_argument('-p', '--pdb',
                        dest='pdb',
                        help='File with PDB debug information.')

    parser.add_argument('--generate-log',
                        dest='generate_log',
                        help='Generate log')


    parser.add_argument('--ar-index',
                        dest='ar_index',
                        help='Pick file from archive for decompilation by its zero-based index.')

    parser.add_argument('--ar-name',
                        dest='ar_name',
                        help='Pick file from archive for decompilation by its name.')

    parser.add_argument('--backend-aggressive-opts',
                        dest='backend_aggressive_opts',
                        help='Enables aggressive optimizations.')

    parser.add_argument('--backend-arithm-expr-evaluator',
                        dest='backend_arithm_expr_evaluator',
                        default='c',
                        help='Name of the used evaluator of arithmetical expressions .')

    parser.add_argument('--backend-call-info-obtainer',
                        dest='backend_call_info_obtainer',
                        default='optim',
                        help='Name of the obtainer of information about function calls.')

    parser.add_argument('--backend-cfg-test',
                        dest='backend_cfg_test',
                        help='Unifies the labels of all nodes in the emitted CFG (this has to be used in tests).')

    parser.add_argument('--backend-disabled-opts',
                        dest='backend_disabled_opts',
                        help='Prevents the optimizations from the given comma-separated list of optimizations to be run.')

    parser.add_argument('--backend-emit-cfg',
                        dest='backend_emit_cfg',
                        help='Emits a CFG for each function in the backend IR (in the .dot format).')

    parser.add_argument('--backend-emit-cg',
                        dest='backend_emit_cg',
                        help='Emits a CG for the decompiled module in the backend IR (in the .dot format).')

    parser.add_argument('--backend-cg-conversion',
                        dest='backend_cg_conversion',
                        default='auto',
                        choices=['auto', 'manual'],
                        help='Should the CG from the backend be converted automatically into the desired format? [auto|manual].')

    parser.add_argument('--backend-cfg-conversion',
                        dest='backend_cfg_conversion',
                        default='auto',
                        help='Should CFGs from the backend be converted automatically into the desired format?')

    parser.add_argument('--backend-enabled-opts',
                        dest='backend_enabled_opts',
                        help='Runs only the optimizations from the given comma-separated list of optimizations.')

    parser.add_argument('--backend-find-patterns',
                        dest='backend_find_patterns',
                        help='Runs the finders of patterns specified in the given comma-separated list (use \'all\' to run them all).')

    parser.add_argument('--backend-force-module-name',
                        dest='backend_force_module_name',
                        help='Overwrites the module name that was detected/generated by the front-end.')

    parser.add_argument('--backend-keep-all-brackets',
                        dest='backend_keep_all_brackets',
                        help='Keeps all brackets in the generated code.')

    parser.add_argument('--backend-keep-library-funcs',
                        dest='backend_keep_library_funcs',
                        help='Keep functions from standard libraries.')

    parser.add_argument('--backend-llvmir2bir-converter',
                        dest='backend_llvmir2bir_converter',
                        default='orig',
                        help='Name of the converter from LLVM IR to BIR.')

    parser.add_argument('--backend-no-compound-operators',
                        dest='backend_no_compound_operators',
                        help='Do not emit compound operators (like +=) instead of assignments.')

    parser.add_argument('--backend-no-debug',
                        dest='backend_no_debug',
                        help='Disables the emission of debug messages, such as phases.')

    parser.add_argument('--backend-no-debug-comments',
                        dest='backend_no_debug_comments',
                        help='Disables the emission of debug comments in the generated code.')

    parser.add_argument('--backend-no-opts',
                        dest='backend_no_opts',
                        help='Disables backend optimizations.')

    parser.add_argument('--backend-no-symbolic-names',
                        dest='backend_no_symbolic_names',
                        help='Disables the conversion of constant arguments to their symbolic names.')

    parser.add_argument('--backend-no-time-varying-info',
                        dest='backend_no_time_varying_info',
                        help='Do not emit time-varying information, like dates.')

    parser.add_argument('--backend-no-var-renaming',
                        dest='backend_no_var_renaming',
                        help='Disables renaming of variables in the backend.')

    parser.add_argument('--backend-semantics',
                        dest='backend_semantics',
                        help='A comma-separated list of the used semantics.')

    parser.add_argument('--backend-strict-fpu-semantics',
                        dest='backend_strict_fpu_semantics',
                        help='Disables backend optimizations.')

    parser.add_argument('--backend-var-renamer',
                        dest='backend_var_renamer',
                        default='readable',
                        choices=['address', 'hungarian', 'readable', 'simple', 'unified'],
                        help='Used renamer of variables [address|hungarian|readable|simple|unified]')

    parser.add_argument('--cleanup',
                        dest='cleanup',
                        help='Removes temporary files created during the decompilation.')

    parser.add_argument('--color-for-ida',
                        dest='color_for_ida ',
                        help='Put IDA Pro color tags to output C file.')

    parser.add_argument('--config',
                        dest='config',
                        help='Specify JSON decompilation configuration file.')

    parser.add_argument('--no-config',
                        dest='no_config',
                        help='State explicitly that config file is not to be used.')

    parser.add_argument('--fileinfo-verbose',
                        dest='fileinfo_verbose',
                        help='Print all detected information about input file.')

    parser.add_argument('--fileinfo-use-all-external-patterns',
                        dest='fileinfo_use_all_external_patterns',
                        help='Use all detection rules from external YARA databases.')

    parser.add_argument('--graph-format',
                        dest='graph_format',
                        default='png',
                        choices=['pdf', 'png', 'svg'],
                        help='Specify format of a all generated graphs (e.g. CG, CFG) [pdf|png|svg].')

    parser.add_argument('--raw-entry-point',
                        dest='raw_entry_point',
                        help='Entry point address used for raw binary (default: architecture dependent)')

    parser.add_argument('--raw-section-vma',
                        dest='raw_section_vma',
                        help='Virtual address where section created from the raw binary will be placed')

    parser.add_argument('--select-decode-only',
                        dest='select_decode_only',
                        help='Decode only selected parts (functions/ranges). Faster decompilation, but worse results.')

    parser.add_argument('--select-functions',
                        dest='select_functions',
                        help='Specify a comma separated list of functions to decompile (example: fnc1,fnc2,fnc3).')

    parser.add_argument('--select-ranges',
                        dest='select_ranges',
                        help='Specify a comma separated list of ranges to decompile (example: 0x100-0x200,0x300-0x400,0x500-0x600).')

    parser.add_argument('--stop-after',
                        dest='stop_after',
                        help='Stop the decompilation after the given tool (supported tools: fileinfo, unpacker, bin2llvmir, llvmir2hll).')

    parser.add_argument('--static-code-sigfile',
                        dest='static_code_sigfile',
                        help='Adds additional signature file for static code detection.')

    parser.add_argument('--static-code-archive',
                        dest='static_code_archive',
                        help='Adds additional signature file for static code detection from given archive.')

    parser.add_argument('--no-default-static-signatures',
                        dest='no_default_static_signatures',
                        help='No default signatures for statically linked code analysis are loaded (options static-code-sigfile/archive are still available).')

    parser.add_argument('--max-memory',
                        dest='max_memory',
                        help='Limits the maximal memory of fileinfo, unpacker, bin2llvmir, and llvmir2hll into the given number of bytes.')

    parser.add_argument('--no-memory-limit',
                        dest='no_memory_limit',
                        help='Disables the default memory limit (half of system RAM) of fileinfo, unpacker, bin2llvmir, and llvmir2hll.')

    parser.add_argument('input',
                        help='Input file')


# todo move
_args = get_parser().parse_args()

def check_arguments(_args):
    """Check proper combination of input arguments.
    """

    global IN
    global CONFIG_DB
    global RAW_ENTRY_POINT
    global RAW_SECTION_VMA
    global HLL
    global OUT
    global PICKED_FILE

    # Check whether the input file was specified.
    if not _args.input:
        Utils.print_error_and_die('No input file was specified')

    # Try to detect desired decompilation mode if not set by user.
    # We cannot detect 'raw' mode because it overlaps with 'bin' (at least not based on extension).
    if not _args.mode:
        if Path(_args.input).suffix == 'll':
            # Suffix .ll
            _args.mode = 'll'
        else:
            _args.mode = 'bin'

    # Print warning message about unsupported combinations of options.
    if _args.mode == 'll':
        if _args.arch:
            Utils.print_warning('Option -a|--arch is not used in mode ' + _args.mode)
        if _args.pdb:
            Utils.print_warning('Option -p|--pdb is not used in mode ' + _args.mode)
        if CONFIG_DB == '' or _args.config:
            Utils.print_error_and_die('Option --config or --no-config must be specified in mode ' + _args.mode)
    elif _args.mode == 'raw':
        # Errors -- missing critical arguments.
        if not _args.arch:
            Utils.print_error_and_die('Option -a|--arch must be used with mode ' + _args.mode)

        if not _args.endian:
                Utils.print_error_and_die('Option -e|--endian must be used with mode ' + _args.mode)

        if not RAW_ENTRY_POINT != '':
                Utils.print_error_and_die('Option --raw-entry-point must be used with mode ' + _args.mode)

        if not RAW_SECTION_VMA != '':
                Utils.print_error_and_die('Option --raw-section-vma must be used with mode ' + _args.mode)

        if not Utils.is_number(RAW_ENTRY_POINT):
            Utils.print_error_and_die('Value in option --raw-entry-point must be decimal (e.g. 123) or hexadecimal value (e.g. 0x123)')
        if not Utils.is_number(RAW_SECTION_VMA):
            Utils.print_error_and_die('Value in option --raw-section-vma must be decimal (e.g. 123) or hexadecimal value (e.g. 0x123)')

    # Archive decompilation errors.
    if _args.ar_name and _args.ar_index:
        Utils.print_error_and_die('Options --ar-name and --ar-index are mutually exclusive. Pick one.')
    if _args.mode != 'bin':
        if _args.ar_name:
            Utils.print_warning('Option --ar-name is not used in mode ' + _args.mode)
        if _args.ar_index:
            Utils.print_warning('Option --ar-index is not used in mode ' + _args.mode)


    if not _args.output:
        # No output file was given, so use the default one.
        (iname, ext) = os.path.splitext(IN)

        if ext == 'll':
            # Suffix .ll
            OUT = name + '.' + HLL
        elif ext == 'exe':
            # Suffix .exe
            OUT = name + '.' + HLL
        elif ext == 'elf':
            # Suffix .elf
            OUT = name + '.' + HLL
        elif ext == 'ihex':
            # Suffix .ihex
            OUT = name + '.' + HLL
        elif ext == 'macho':
            # Suffix .macho
            OUT = name + '.' + HLL
        else:
            OUT = IN + PICKED_FILE + '.' + HLL

        # If the output file name matches the input file name, we have to change the
        # output file name. Otherwise, the input file gets overwritten.
        if IN == OUT:
            OUT = name + '.out.' + HLL

        # Convert to absolute paths.
        IN = Utils.get_realpath(IN)
        OUT = Utils.get_realpath(OUT)

        if os.path.exists(_args.pdb):
            _args.pdb = Utils.get_realpath(_args.pdb)

        # Check that selected ranges are valid.
        if _args.selected_ranges:
            for range in _args.selected_ranges:
                # Check if valid range.
                if not Utils.is_range(range):
                    Utils.print_error_and_die('Range %s in option --select-ranges is not a valid decimal (e.g. 123-456) or hexadecimal (e.g. 0x123-0xabc) range.' % range)

        # Check if first <= last.
        ranges = _args.selected_ranges.split('-')
        # parser line into array
        if int(ranges[0]) > int(ranges[1]):
            Utils.print_error_and_die('Range '' + (r) + '' in option --select-ranges is not a valid range: second address must be greater or equal than the first one.')


def print_warning_if_decompiling_bytecode():
    """Prints a warning if we are decompiling bytecode."""

    bytecode = os.popen('\'' + config.CONFIGTOOL + '\' \'' + CONFIG + '\' --read --bytecode').read(). \
        rstrip('\n')

    if bytecode != '':
        Utils.print_warning('Detected ' + bytecode + ' bytecode, which cannot be decompiled by our machine-code '
                                                          'decompiler. The decompilation result may be inaccurate.')


def check_whether_decompilation_should_be_forcefully_stopped(tool_name):
    """Checks whether the decompilation should be forcefully stopped because of the
    --stop-after parameter. If so, cleanup is run and the script exits with 0.

    Arguments:

      $1 Name of the tool.

    The function expects the $STOP_AFTER variable to be set.
    """

    if _args.stop_after == tool_name:
        if _args.generate_log:
            generate_log()

        cleanup()
        print()
        print('#### Forced stop due to  - -stop - after %s...' % _args.stop_after)
        sys.exit(0)


#
# Clean working directory.
#
def cleanup():
    global CLEANUP
    global OUT_UNPACKED
    global OUT_FRONTEND_LL
    global OUT_FRONTEND_BC
    global CONFIG
    global CONFIG_DB
    global OUT_BACKEND_BC
    global OUT_BACKEND_LL
    global OUT_RESTORED
    global OUT_ARCHIVE
    global SIGNATURES_TO_REMOVE
    global TOOL_LOG_FILE

    if _args.cleanup:
        Utils.remove_forced(OUT_UNPACKED)
        Utils.remove_forced(OUT_FRONTEND_LL)
        Utils.remove_forced(OUT_FRONTEND_BC)

        if CONFIG != CONFIG_DB:
            Utils.remove_forced(CONFIG)

        Utils.remove_forced(OUT_BACKEND_BC)
        Utils.remove_forced(OUT_BACKEND_LL)
        Utils.remove_forced(OUT_RESTORED)

        # Archive support
        Utils.remove_forced(OUT_ARCHIVE)

        # Archive support (Macho-O Universal)
        for sig in SIGNATURES_TO_REMOVE:
            Utils.remove_forced(sig)

        # Signatures generated from archives
        if TOOL_LOG_FILE != '':
            Utils.remove_forced(TOOL_LOG_FILE)


#
# An alternative to the `time` shell builtin that provides more information. It
# is used in decompilation log to get the running time and used memory of a command.
#
TIME = '/usr/bin/time -v'
TIMEOUT = 300
#
# Parses the given return code and output from a tool that was run through
# `/usr/bin/time -v` and prints the return code to be stored into the log.
#
# Parameters:
#
#    - $1: return code from `/usr/bin/time`
#    - $2: combined output from the tool and `/usr/bin/time -v`
#
# This function has to be called for every tool that is run through
# `/usr/bin/time`. The reason is that when a tool is run without
# `/usr/bin/time` and it e.g. segfaults, shell returns 139, but when it is run
# through `/usr/bin/time`, it returns 11 (139 - 128). If this is the case, this
# function prints 139 instead of 11 to make the return codes of all tools
# consistent.
#
def get_tool_rc(return_code, output):
    global BASH_REMATCH
    global RC

    orig_rc = return_code
    signal_regex = 'Command terminated by signal ([0-9]*)'

    if re.search(signal_regex, output):
        signal_num = BASH_REMATCH[1]
        RC = signal_num + 128
    else:
        RC = orig_rc
        # We want to be able to distinguish assertions and memory-insufficiency
        # errors. The problem is that both assertions and memory-insufficiency
        # errors make the program exit with return code 134. We solve this by
        # replacing 134 with 135 (SIBGUS, 7) when there is 'std::bad_alloc' in the
        # output. So, 134 will mean abort (assertion error) and 135 will mean
        # memory-insufficiency error.
        if RC == 134 or re.search('std::bad_alloc', output):
            RC = 135
        print(RC)

    return RC

#
# Parses the given output ($1) from a tool that was run through
# `/usr/bin/time -v` and prints the running time in seconds.
#
def get_tool_runtime(_p1):
    global USER_TIME_F
    global SYSTEM_TIME_F
    global RUNTIME_F

    # The output from `/usr/bin/time -v` looks like this:
    #
    #    [..] (output from the tool)
    #        Command being timed: 'tool'
    #        User time (seconds): 0.04
    #        System time (seconds): 0.00
    #        [..] (other data)
    #
    # We combine the user and system times into a single time in seconds.
    USER_TIME_F = os.popen('egrep \'User time \\(seconds\\').read().rstrip('\n') + ': <<< ' + (_p1) + ' | cut -d: -f2)'

    SYSTEM_TIME_F = os.popen('egrep \'System time \\(seconds\\').read().rstrip('\n') + ': <<< ' + (_p1) + ' | cut -d: -f2)'
    RUNTIME_F = os.popen('echo ' + USER_TIME_F + '  +  ' + SYSTEM_TIME_F + ' | bc').read().rstrip('\n')
    # Convert the runtime from float to int (http://unix.stackexchange.com/a/89843).
    # By adding 1, we make sure that the runtime is at least one second. This
    # also takes care of proper rounding (we want to round runtime 1.1 to 2).
    _rc0 = _rcr2, _rcw2 = os.pipe()
    if os.fork():
        os.close(_rcw2)
        os.dup2(_rcr2, 0)
        subprocess.call(['bc'], shell=True)
    else:
        os.close(_rcr2)
        os.dup2(_rcw2, 1)
        print('(' + RUNTIME_F + '  +  1)/1')
        #sys.exit(0)

    return  RUNTIME_F

#
# Parses the given output ($1) from a tool that was run through
# `/usr/bin/time -v` and prints the memory usage in MB.
#
def get_tool_memory_usage(tool):
    global RSS_KB
    global RSS_MB

    """The output from `/usr/bin/time -v` looks like this:
    
        [..] (output from the tool)
            Command being timed: 'tool'
            [..] (other data)
            Maximum resident set size (kbytes): 1808
            [..] (other data)
    
    We want the value of 'resident set size' (RSS), which we convert from KB
    to MB. If the resulting value is less than 1 MB, round it to 1 MB.
    """
    RSS_KB = os.popen('egrep \'Maximum resident set size \\(kbytes\\').read().rstrip('\n') + ': <<< ' + (
        tool) + ' | cut -d: -f2)'

    RSS_MB = (RSS_KB // 1024)
    print((RSS_MB if (RSS_MB > 0) else 1))

    return RSS_MB


#
# Prints the actual output of a tool that was run through `/usr/bin/time -v`.
# The parameter ($1) is the combined output from the tool and `/usr/bin/time -v`.
#
def get_tool_output(_p1):
    # The output from `/usr/bin/time -v` looks either like this (success):
    #
    #    [..] (output from the tool)
    #        Command being timed: 'tool'
    #        [..] (other data)
    #
    # or like this (when there was an error):
    #
    #    [..] (output from the tool)
    #        Command exited with non-zero status X
    #        [..] (other data)
    #
    # Remove everything after and including 'Command...'
    # (http://stackoverflow.com/a/5227429/2580955).
    _rcr1, _rcw1 = os.pipe()
    if os.fork():
        os.close(_rcw1)
        os.dup2(_rcr1, 0)
        subprocess.call(['sed', '-n', '/Command exited with non-zero status/q;p'], shell=True)
    else:
        os.close(_rcr1)
        os.dup2(_rcw1, 1)
        _rc0 = subprocess.Popen('sed' + ' ' + '-n' + ' ' + '/Command being timed:/q;p', shell=True, stdin=subprocess.PIPE)
        _rc0.communicate(_p1 + '\n')

        return _rc0.wait()
        #sys.exit(0)


#
# Prints an escaped version of the given text so it can be inserted into JSON.
#
# Parameters:
#   - $1 Text to be escaped.
#
def json_escape(_p1):
    # We need to escape backslashes (\), double quotes ('), and replace new lines with '\n'.
    _rcr1, _rcw1 = os.pipe()
    if os.fork():
        os.close(_rcw1)
        os.dup2(_rcr1, 0)
        _rcr2, _rcw2 = os.pipe()
        if os.fork():
            os.close(_rcw2)
            os.dup2(_rcr2, 0)
            _rcr3, _rcw3 = os.pipe()
            if os.fork():
                os.close(_rcw3)
                os.dup2(_rcr3, 0)
                subprocess.call(['sed', '{:q;N;s/\\n/\\\\n/g;t q}'], shell=True)
            else:
                os.close(_rcr3)
                os.dup2(_rcw3, 1)
                subprocess.call(['sed', 's/\'/\\\\\'/g'], shell=True)
                #sys.exit(0)

        else:
            os.close(_rcr2)
            os.dup2(_rcw2, 1)
            subprocess.call(['sed', 's/\\\\/\\\\\\\\/g'], shell=True)
            #sys.exit(0)

    else:
        os.close(_rcr1)
        os.dup2(_rcw1, 1)
        print(_p1)
        #sys.exit(0)

    # for now just return the param
    return _p1



def remove_colors(_p1):
    """Removes color codes from the given text ($1).
    """
    _rc0 = subprocess.Popen('sed' + ' ' + '-r' + ' ' + 's/\x1b[^m]*m//g', shell=True, stdin=subprocess.PIPE)
    _rc0.communicate(_p1 + '\n')

    return _rc0.wait()


def timed_kill(pid):
    """Platform-independent alternative to `ulimit -t` or `timeout`.
    Based on http://www.bashcookbook.com/bashinfo/source/bash-4.0/examples/scripts/timeout3
    1 argument is needed - PID
    Returns - 1 if number of arguments is incorrect
              0 otherwise
    """

    global TIMEOUT
    global timeout

    PID = pid
    # PID of the target process
    PROCESS_NAME = os.popen('ps -p ' + PID + ' -o comm --no-heading').read().rstrip('\n')

    if PROCESS_NAME == 'time':
        # The program is run through `/usr/bin/time`, so get the PID of the
        # child process (the actual program). Otherwise, if we killed
        # `/usr/bin/time`, we would obtain no output from it (user time, memory
        # usage etc.).
        PID = os.popen('ps --ppid ' + PID + ' -o pid --no-heading | head -n1').read().rstrip('\n')

    if not TIMEOUT:
        TIMEOUT = 300

    timeout = TIMEOUT
    t = timeout

    while t > 0:
        subprocess.call(['sleep', '1'], shell=True)

        if not subprocess.call('kill' + ' ' + '-0' + ' ' + PID, shell=True, stdout=open(os.devnull, 'wb'),
                               stderr=open(os.devnull, 'wb')):
            exit(0)

    t = t - 1

    _rc0 = subprocess.call('kill_tree' + ' ' + PID + ' ' + 'SIGKILL', shell=True, stdout=open(os.devnull, 'wb'),
                           stderr=open(os.devnull, 'wb'))

    return 0


#
# Kill process and all its children.
# Based on http://stackoverflow.com/questions/392022/best-way-to-kill-all-child-processes/3211182#3211182
# 2 arguments are needed - PID of process to kill  +  signal type
# Returns - 1 if number of arguments is incorrect
#           0 otherwise
#
def kill_tree(pid, signal_type):
    """ TODO implement
    _pid = pid
    _sig = Expand.colonMinus('2', 'TERM')
    _rc0 = subprocess.call(['kill', '-stop', Expand.underbar() + 'pid'], shell=True)

    # needed to stop quickly forking parent from producing child between child killing and parent killing
    for _child in os.popen('ps -o pid --no-headers --ppid \'' + Expand.underbar() + 'pid\'').read().rstrip('\n'):
        kill_tree(Expand.underbar() + 'child', Expand.underbar() + 'sig')
    _rc0 = subprocess.call(['kill', '-' + Expand.underbar() + 'sig', Expand.underbar() + 'pid'], shell=True)
    """

    return 0


def string_to_md5(string):
    """Generate a MD5 checksum from a given string.
    """

    m = hashlib.md5()
    m.update(string)

    return m.hexdigest()


def generate_log():
    global OUT
    global LOG_DECOMPILATION_END_DATE
    global LOG_FILEINFO_OUTPUT
    global LOG_UNPACKER_OUTPUT
    global LOG_BIN2LLVMIR_OUTPUT
    global LOG_LLVMIR2HLL_OUTPUT
    global IN
    global LOG_DECOMPILATION_START_DATE
    global FORMAT
    global LOG_FILEINFO_RC
    global LOG_UNPACKER_RC
    global LOG_BIN2LLVMIR_RC
    global LOG_LLVMIR2HLL_RC
    global LOG_FILEINFO_RUNTIME
    global LOG_BIN2LLVMIR_RUNTIME
    global LOG_LLVMIR2HLL_RUNTIME
    global LOG_FILEINFO_MEMORY
    global LOG_BIN2LLVMIR_MEMORY
    global LOG_LLVMIR2HLL_MEMORY

    LOG_FILE = OUT + '.decompilation.log'
    LOG_DECOMPILATION_END_DATE = os.popen('date  + %s').read().rstrip('\n')

    LOG_FILEINFO_OUTPUT =  json_escape(LOG_FILEINFO_OUTPUT)
    LOG_UNPACKER_OUTPUT = json_escape(LOG_UNPACKER_OUTPUT)
    LOG_BIN2LLVMIR_OUTPUT = remove_colors(LOG_BIN2LLVMIR_OUTPUT)
    LOG_BIN2LLVMIR_OUTPUT = json_escape(LOG_BIN2LLVMIR_OUTPUT)
    LOG_LLVMIR2HLL_OUTPUT = remove_colors(LOG_LLVMIR2HLL_OUTPUT)
    LOG_LLVMIR2HLL_OUTPUT = json_escape(LOG_LLVMIR2HLL_OUTPUT)

    log_structure = '{\n\t\'input_file\' : \'%s\',\n\t\'pdb_file\' : \'%s\',\n\t\'start_date\' :' \
                    ' \'%s\',\n\t\'end_date\' : \'%s\',\n\t\'mode\' : \'%s\',\n\t\'arch\' : \'%s\',\n\t\'format\'' \
                    ' : \'%s\',\n\t\'fileinfo_rc\' : \'%s\',\n\t\'unpacker_rc\' : \'%s\',\n\t\'bin2llvmir_rc\'' \
                    ' : \'%s\',\n\t\'llvmir2hll_rc\' : \'%s\',\n\t\'fileinfo_output\' :' \
                    ' \'%s\',\n\t\'unpacker_output\' : \'%s\',\n\t\'bin2llvmir_output\' :' \
                    ' \'%s\',\n\t\'llvmir2hll_output\' : \'%s\',\n\t\'fileinfo_runtime\' :' \
                    ' \'%s\',\n\t\'bin2llvmir_runtime\' : \'%s\',\n\t\'llvmir2hll_runtime\' :' \
                    ' \'%s\',\n\t\'fileinfo_memory\' : \'%s\',\n\t\'bin2llvmir_memory\' :' \
                    ' \'%s\',\n\t\'llvmir2hll_memory\' : \'%s\'\n}\n'

    print(log_structure % (
        IN, _args.pdb, LOG_DECOMPILATION_START_DATE, LOG_DECOMPILATION_END_DATE, _args.mode,
        _args.arch,
        FORMAT, LOG_FILEINFO_RC, LOG_UNPACKER_RC, LOG_BIN2LLVMIR_RC, LOG_LLVMIR2HLL_RC,
        LOG_FILEINFO_OUTPUT, LOG_UNPACKER_OUTPUT, LOG_BIN2LLVMIR_OUTPUT, LOG_LLVMIR2HLL_OUTPUT,
        LOG_FILEINFO_RUNTIME, LOG_BIN2LLVMIR_RUNTIME, LOG_LLVMIR2HLL_RUNTIME, LOG_FILEINFO_MEMORY,
        LOG_BIN2LLVMIR_MEMORY, LOG_LLVMIR2HLL_MEMORY))

"""
while True:

    if (sys.argv[1]) == '-a' or (sys.argv[1]) == '--arch':
        # Target architecture.
        if (_args.arch) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: -a|--arch'], shell=True)
        if (sys.argv[
                   2]) != 'mips' os.path.exists((sys.argv[2])) '!='  '-a' (sys.argv[2]) != 'arm' os.path.exists((sys.argv[2])) '!='  '-a' (sys.argv[2]) != 'powerpc' os.path.exists((sys.argv[2]))'!=' != '':
            subprocess.call(['print_error_and_die',
                             'Unsupported target architecture '' + (sys.argv[2]) + ''. Supported architectures: Intel x86, ARM, ARM + Thumb, MIPS, PIC32, PowerPC.'],
                            shell=True)
        _args.arch = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '-e' or (sys.argv[1]) == '--endian':
        # Endian.
        if ENDIAN != '':
            utils.print_error_and_die('Duplicate option: -e|--endian')
        ENDIAN = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '-h' or (sys.argv[1]) == '--help':
        # Help.
        print_help()
        exit(0)
    elif (sys.argv[1]) == '-k' or (sys.argv[1]) == '--keep-unreachable-funcs':
        # Keep unreachable functions.
        # Do not check if this parameter is a duplicate because when both
        # --select-ranges or --select--functions and -k is specified, the
        # decompilation fails.
        _args.keep_unreachable_funcs = 1
        subprocess.call(['shift'], shell=True)
    elif (sys.argv[1]) == '-l' or (sys.argv[1]) == '--target-language':
        # Target language.
        if (HLL) != '':
            utils.print_error_and_die('Duplicate option: -l|--target-language')
        if (sys.argv[2]) != 'c' and os.path.exists((sys.argv[2])) != '':
            utils.print_error_and_die('Unsupported target language '' + (sys.argv[2]) + ''. Supported languages: C, Python.')
        HLL = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '-m' or (sys.argv[1]) == '--mode':
        # Decompilation mode.
        if (MODE) != '':
            utils.print_error_and_die('Duplicate option: -m|--mode')
        if (sys.argv[2]) != 'bin' os.path.exists((sys.argv[2])) '!='  '-a' (sys.argv[2]) != 'raw':
            utils.print_error_and_die('Unsupported decompilation mode '' + (sys.argv[2]) + ''. Supported modes: bin, ll, raw.')
        MODE = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '-o' or (sys.argv[1]) == '--output':
        # Output file.
        if (OUT) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: -o|--output'], shell=True)
        OUT = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '-p' or (sys.argv[1]) == '--pdb':
        # File containing PDB debug information.
        if (_args.pdb) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: -p|--pdb'], shell=True)
        _args.pdb = sys.argv[2]
        if not os.access, R_OK) ):
            subprocess.call(
                ['print_error_and_die', 'The input PDB file '' + (_args.pdb) + '' does not exist or is not readable'],
                shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '--backend-aggressive-opts':
        # Enable aggressive optimizations.
        if (_args.backend_aggressive_opts) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-aggressive-opts'], shell=True)
        _args.backend_aggressive_opts = 1
        subprocess.call(['shift'], shell=True)
    elif (sys.argv[1]) == '--backend-arithm-expr-evaluator':
        # Name of the evaluator of arithmetical expressions.
        if (_args.backend_arithm_expr_evaluator) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-arithm-expr-evaluator'], shell=True)
        _args.backend_arithm_expr_evaluator = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '--backend-call-info-obtainer':
        # Name of the obtainer of information about function calls.
        if (_args.backend_call_info_obtainer) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-call-info-obtainer'], shell=True)
        _args.backend_call_info_obtainer = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '--backend-cfg-test':
        # Unify the labels in the emitted CFG.
        if (_args.backend_cfg_test) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-cfg-test'], shell=True)
        _args.backend_cfg_test = 1
        subprocess.call(['shift'], shell=True)
    elif (sys.argv[1]) == '--backend-disabled-opts':
        # List of disabled optimizations in the backend.
        if (_args.backend_disabled_opts) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-disabled-opts'], shell=True)
        _args.backend_disabled_opts = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '--backend-emit-cfg':
        # Emit a CFG of each function in the backend IR.
        if (_args.backend_emit_cfg) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-emit-cfg'], shell=True)
        _args.backend_emit_cfg = 1
        subprocess.call(['shift'], shell=True)
    elif (sys.argv[1]) == '--backend-emit-cg':
        # Emit a CG of the decompiled module in the backend IR.
        if (_args.backend_emit_cg) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-emit-cg'], shell=True)
        _args.backend_emit_cg = 1
        subprocess.call(['shift'], shell=True)
    elif (sys.argv[1]) == '--backend-cg-conversion':
        # Should the CG from the backend be converted automatically into the desired format?.
        if (_args.backend_cg_conversion) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-cg-conversion'], shell=True)
        if (sys.argv[2]) != 'auto' os.path.exists((sys.argv[2]))'!=' != '':
            subprocess.call(['print_error_and_die',
                             'Unsupported CG conversion mode '' + (sys.argv[2]) + ''. Supported modes: auto, manual.'],
                            shell=True)
        _args.backend_cg_conversion = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '--backend-cfg-conversion':
        # Should CFGs from the backend be converted automatically into the desired format?.
        if (_args.backend_cfg_conversion) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-cfg-conversion'], shell=True)
        if (sys.argv[2]) != 'auto' os.path.exists((sys.argv[2]))'!=' != '':
            subprocess.call(['print_error_and_die',
                             'Unsupported CFG conversion mode '' + (sys.argv[2]) + ''. Supported modes: auto, manual.'],
                            shell=True)
        _args.backend_cfg_conversion = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (sys.argv[1]) == '--backend-enabled-opts':
        # List of enabled optimizations in the backend.
        if (_args.backend_enabled_opts) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-enabled-opts'], shell=True)
        _args.backend_enabled_opts = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--backend-find-patterns'):
        # Try to find patterns.
        if (_args.backend_find_patterns) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-find-patterns'], shell=True)
        _args.backend_find_patterns = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--backend-force-module-name'):
        # Force the module's name in the backend.
        if (_args.backend_force_module_name) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-force-module-name'], shell=True)
        _args.backend_force_module_name = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--backend-keep-all-brackets'):
        # Keep all brackets.
        if (_args.backend_keep_all_brackets) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-keep-all-brackets'], shell=True)
        _args.backend_keep_all_brackets = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-keep-library-funcs'):
        # Keep library functions.
        if (_args.backend_keep_library_funcs) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-keep-library-funcs'], shell=True)
        _args.backend_keep_library_funcs = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-llvmir2bir-converter'):
        # Name of the converter of LLVM IR to BIR.
        if (_args.backend_llvmir2bir_converter) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-llvmir2bir-converter'], shell=True)
        _args.backend_llvmir2bir_converter = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--backend-no-compound-operators'):
        # Do not use compound operators.
        if (_args.backend_no_compound_operators) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-compound-operators'], shell=True)
        _args.backend_no_compound_operators = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-no-debug'):
        # Emission of debug messages.
        if (_args.backend_no_debug) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-debug'], shell=True)
        _args.backend_no_debug = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-no-debug-comments'):
        # Emission of debug comments.
        if (_args.backend_no_debug_comments) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-debug-comments'], shell=True)
        _args.backend_no_debug_comments = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-no-opts'):
        # Disable backend optimizations.
        if (_args.backend_no_opts) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-opts'], shell=True)
        _args.backend_no_opts = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-no-symbolic-names'):
        # Disable the conversion of constant arguments.
        if (_args.backend_no_symbolic_names) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-symbolic-names'], shell=True)
        _args.backend_no_symbolic_names = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-no-time-varying-info'):
        # Do not emit any time-varying information.
        if (_args.backend_no_time_varying_info) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-time-varying-info'], shell=True)
        _args.backend_no_time_varying_info = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-no-var-renaming'):
        # Disable renaming of variables in the backend.
        if (_args.backend_no_var_renaming) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-var-renaming'], shell=True)
        _args.backend_no_var_renaming = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-semantics'):
        # The used semantics in the backend.
        if (_args.backend_semantics) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-semantics'], shell=True)
        _args.backend_semantics = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--backend-strict-fpu-semantics'):
        # Use strict FPU semantics in the backend.
        if (_args.backend_strict_fpu_semantics) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-strict-fpu-semantics'], shell=True)
        _args.backend_strict_fpu_semantics = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--backend-var-renamer'):
        # Used renamer of variable names.
        if (_args.backend_var_renamer) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-var-renamer'], shell=True)
        if (sys.argv[
                   2]) != 'address' os.path.exists((sys.argv[2])) '!='  '-a' (sys.argv[2]) != 'readable' os.path.exists((sys.argv[2])) '!='  '-a' (sys.argv[2]) != 'unified':
            subprocess.call(['print_error_and_die',
                             'Unsupported variable renamer '' + (sys.argv[2]) + ''. Supported renamers: address, hungarian, readable, simple, unified.'],
                            shell=True)
        _args.backend_var_renamer = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--raw-entry-point'):
        # Entry point address for binary created from raw data.
        if (RAW_ENTRY_POINT) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --raw-entry-point'], shell=True)
        RAW_ENTRY_POINT = sys.argv[2]
        # RAW_ENTRY_POINT='$(($2))'  # evaluate hex address - probably not needed
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--raw-section-vma'):
        # Virtual memory address for section created from raw data.
        if (RAW_SECTION_VMA) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --raw-section-vma'], shell=True)
        RAW_SECTION_VMA = sys.argv[2]
        # RAW_SECTION_VMA='$(($2))'  # evaluate hex address - probably not needed
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--cleanup'):
        # Cleanup.
        if (CLEANUP) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --cleanup'], shell=True)
        CLEANUP = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--color-for-ida'):
        if (_args.color_for_ida) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --color-for-ida'], shell=True)
        _args.color_for_ida = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--config'):
        if (CONFIG_DB) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --config'], shell=True)
        if (NO_CONFIG) != '':
            subprocess.call(['print_error_and_die', 'Option --config can not be used with option --no-config'],
                            shell=True)
        CONFIG_DB = sys.argv[2]
        if (not os.access((CONFIG_DB), R_OK) ):
            subprocess.call(['print_error_and_die',
                             'The input JSON configuration file '' + (CONFIG_DB) + '' does not exist or is not readable'],
                            shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--no-config'):
        if (NO_CONFIG) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --no-config'], shell=True)
        if (CONFIG_DB) != '':
            subprocess.call(['print_error_and_die', 'Option --no-config can not be used with option --config'],
                            shell=True)
        NO_CONFIG = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--graph-format'):
        # Format of graph files.
        if (_args.graph_format) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --graph-format'], shell=True)
        if (sys.argv[2]) != 'pdf' os.path.exists((sys.argv[2])) '!='  '-a' (sys.argv[2]) != 'svg':
            subprocess.call(['print_error_and_die',
                             'Unsupported graph format '' + (sys.argv[2]) + ''. Supported formats: pdf, png, svg.'],
                            shell=True)
        _args.graph_format = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--select-decode-only'):
        if (_args.selected_decode_only) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --select-decode-only'], shell=True)
        _args.selected_decode_only = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--select-functions'):
        # List of selected functions.
        if (_args.selected_functions) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --select-functions'], shell=True)
        IFS').setValue(',')
        # parser line into array
        _args.keep_unreachable_funcs = 1
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--select-ranges'):
        # List of selected ranges.
        if (_args.selected_ranges) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --select-ranges'], shell=True)
        _args.selected_ranges = sys.argv[2]
        IFS').setValue(',')
        # parser line into array
        _args.keep_unreachable_funcs = 1
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--stop-after'):
        # Stop decompilation after the given tool.
        if (STOP_AFTER) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --stop-after'], shell=True)
        STOP_AFTER = sys.argv[2]
        if (not re.search('^(fileinfo|unpacker|bin2llvmir|llvmir2hll)' + '$', (STOP_AFTER))):
            subprocess.call(['print_error_and_die', 'Unsupported tool '' + (STOP_AFTER) + '' for --stop-after'],
                            shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--static-code-sigfile'):
        # User provided signature file.
        if not os.path.isfile((sys.argv[2])):
            subprocess.call(['print_error_and_die', 'Invalid .yara file '' + (sys.argv[2]) + '''], shell=True)
        _args.static_code_sigfile').setValue('(' + (sys.argv[2]) + ')')
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--static-code-archive'):
        # User provided archive to create signature file from.
        if not os.path.isfile((sys.argv[2])):
            subprocess.call(['print_error_and_die', 'Invalid archive file '' + (sys.argv[2]) + '''], shell=True)
        _args.static_code_archive').setValue('(' + (sys.argv[2]) + ')')
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--no-default-static-signatures'):
        _args.no_default_static_signatures = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--fileinfo-verbose'):
        # Enable --verbose mode in fileinfo.
        if (_args.fileinfo_verbose) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --fileinfo-verbose'], shell=True)
        _args.fileinfo_verbose = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--fileinfo-use-all-external-patterns'):
        if (FILEINFO_USE_ALL_EXTERNAL_PATTERNS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --fileinfo-use-all-external-patterns'],
                            shell=True)
        FILEINFO_USE_ALL_EXTERNAL_PATTERNS = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--ar-name'):
        # Archive decompilation by name.
        if (_args.ar_name) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --ar-name'], shell=True)
        _args.ar_name = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--ar-index'):
        # Archive decompilation by index.
        if (_args.ar_index) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --ar-index'], shell=True)
        _args.ar_index = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--max-memory'):
        if (_args.max_memory) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --max-memory'], shell=True)
        if (_args.no_memory_limit) != '':
            subprocess.call(['print_error_and_die', 'Clashing options: --max-memory and --no-memory-limit'], shell=True)
        _args.max_memory = sys.argv[2]
        if (not re.search(Str(Glob('^[0-9] + ' + '$')), (_args.max_memory))):
            subprocess.call(['print_error_and_die',
                             'Invalid value for --max-memory: ' + (_args.max_memory) + ' (expected a positive integer)'],
                            shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif ((sys.argv[1]) == '--no-memory-limit'):
        if (_args.no_memory_limit) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --no-memory-limit'], shell=True)
        if (_args.max_memory) != '':
            subprocess.call(['print_error_and_die', 'Clashing options: --max-memory and --no-memory-limit'], shell=True)
        _args.no_memory_limit = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--generate-log'):
        # Intentionally undocumented option.
        # Used only for internal testing.
        # NOT guaranteed it works everywhere (systems other than our internal test machines).
        if (_args.generate_log) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --generate-log'], shell=True)
        _args.generate_log = 1
        _args.no_memory_limit = 1
        subprocess.call(['shift'], shell=True)
    elif ((sys.argv[1]) == '--'):
        # Input file.
        if (Expand.hash() == 2):
            IN = sys.argv[2]
            if (not os.access((IN), R_OK) ):
                subprocess.call(
                    ['print_error_and_die', 'The input file '' + (IN) + '' does not exist or is not readable'],
                    shell=True)
        elif (Expand.hash() > 2):
            # Invalid options.
            subprocess.call(
                ['print_error_and_die', 'Invalid options: '' + (sys.argv[2]) + '', '' + (sys.argv[3]) + '' ...'],
                shell=True)
        break
"""


# Check arguments and set default values for unset options.
check_arguments(_args)

# Initialize variables used by logging.
if _args.generate_log:
    LOG_DECOMPILATION_START_DATE = os.popen('date  + %s').read().rstrip('\n')
    # Put the tool log file and tmp file into /tmp because it uses tmpfs. This means that
    # the data are stored in RAM instead on the disk, which should provide faster access.
    TMP_DIR = '/tmp/decompiler_log'

    os.makedirs(TMP_DIR, exist_ok=True)

    FILE_MD5 = string_to_md5(OUT)
    TOOL_LOG_FILE = TMP_DIR + '/' + FILE_MD5 + '.tool'

# Raw.
if _args.mode == 'raw':
    # Entry point for THUMB must be odd.
    if _args.arch == 'thumb' or (RAW_ENTRY_POINT % 2) == 0:
        _args.keep_unreachable_funcs = 1
        RAW_ENTRY_POINT = (RAW_ENTRY_POINT + 1)

# Check for archives.
if _args.mode == 'bin':
    # Check for archives packed in Mach-O Universal Binaries.
    print('##### Checking if file is a Mach-O Universal static library...')
    print('RUN: ' + config.EXTRACT + ' --list ' + IN)

    if Utils.is_macho_archive(IN):
        OUT_ARCHIVE = OUT + '.a'
        if _args.arch:
            print()
            print('##### Restoring static library with architecture family ' + _args.arch + '...')
            print('RUN: ' + config.EXTRACT + ' --family ' + _args.arch + ' --out ' + OUT_ARCHIVE + ' ' + IN)
            if (
                    not subprocess.call([config.EXTRACT, '--family', _args.arch, '--out', OUT_ARCHIVE, IN],
                                        shell=True)):
                # Architecture not supported
                print('Invalid --arch option \'' + _args.arch + '\'. File contains these architecture families:')
                subprocess.call([config.EXTRACT, '--list', IN], shell=True)
                cleanup()
                sys.exit(1)
        else:
            # Pick best architecture
            print()
            print('##### Restoring best static library for decompilation...')
            print('RUN: ' + config.EXTRACT + ' --best --out ' + OUT_ARCHIVE + ' ' + IN)
            subprocess.call([config.EXTRACT, '--best', '--out', OUT_ARCHIVE, IN], shell=True)
        IN = OUT_ARCHIVE

    print()
    print('##### Checking if file is an archive...')
    print('RUN: ' + config.AR + ' --arch-magic ' + IN)

    if Utils.has_archive_signature(IN):
        print('This file is an archive!')

        # Check for thin signature.
        if Utils.has_thin_archive_signature(IN):
            cleanup()
            Utils.print_error_and_die('File is a thin archive and cannot be decompiled.')

        # Check if our tools can handle it.
        if not Utils.is_valid_archive(IN):
            cleanup()
            Utils.print_error_and_die('The input archive has invalid format.')

        # Get and check number of objects.
        ARCH_OBJECT_COUNT = Utils.archive_object_count(IN)
        if ARCH_OBJECT_COUNT <= 0:
            cleanup()
            Utils.print_error_and_die('The input archive is empty.')

        # Prepare object output path.
        OUT_RESTORED = OUT + '.restored'

        # Pick object by index.
        if _args.ar_index != '':
            print()
            print('##### Restoring object file on index '' + (_args.ar_index) + '' from archive...')
            print('RUN: ' + config.AR + ' ' + IN + ' --index ' + _args.ar_index + ' --output ' + OUT_RESTORED)

            if not Utils.archive_get_by_index(IN, _args.ar_index, OUT_RESTORED):
                cleanup()
                VALID_INDEX = (ARCH_OBJECT_COUNT - 1)

                if VALID_INDEX != 0:
                    Utils.print_error_and_die('File on index \'' + (
                        _args.ar_index) + '\' was not found in the input archive. Valid indexes are 0-' + (
                        VALID_INDEX) + '.')
                else:
                    Utils.print_error_and_die('File on index \'' + (
                        _args.ar_index) + '\' was not found in the input archive. The only valid index is 0.')
            IN = OUT_RESTORED
        elif _args.ar_name:
            print()
            print('##### Restoring object file with name '' + (_args.ar_name) + '' from archive...')
            print('RUN: ' + config.AR + ' ' + IN + ' --name ' + _args.ar_name + ' --output ' + OUT_RESTORED)

            if not Utils.archive_get_by_name(IN, _args.ar_name, OUT_RESTORED):
                cleanup()
                Utils.print_error_and_die('File named %s was not found in the input archive.' % _args.ar_name)
            IN = OUT_RESTORED
        else:
            # Print list of files.
            print('Please select file to decompile with either \' --ar-index = n\'')
            print('or \' --ar-name = string\' option. Archive contains these files:')

            Utils.archive_list_numbered_content(IN)
            cleanup()
            sys.exit(1)
    else:
        if _args.ar_name != '':
            Utils.print_warning('Option --ar-name can be used only with archives.')

        if _args.ar_index != '':
            Utils.print_warning('Option --ar-index can be used only with archives.')

        print('Not an archive, going to the next step.')


if _args.mode == 'bin' or _args.mode == 'raw':
    # Assignment of other used variables.
    name = os.path.splitext(OUT)[0]
    OUT_UNPACKED = name + '-unpacked'
    OUT_FRONTEND = OUT + '.frontend'
    OUT_FRONTEND_LL = OUT_FRONTEND + '.ll'
    OUT_FRONTEND_BC = OUT_FRONTEND + '.bc'
    CONFIG = OUT + '.json'

    if CONFIG != CONFIG_DB:
        Utils.remove_forced(CONFIG)

    if CONFIG_DB != '':
        shutil.copyfile(CONFIG_DB, CONFIG)

    # Preprocess existing file or create a new, empty JSON file.
    if os.path.isfile(CONFIG):
        subprocess.call([config.CONFIGTOOL, CONFIG, '--preprocess'], shell=True)
    else:
        print('{}', file=open(CONFIG, 'wb'))


    # Raw data needs architecture, endianess and optionaly sections's vma and entry point to be specified.
    if _args.mode == 'raw':
        if not _args.arch or _args.arch == 'unknown' or _args.arch == '':
            Utils.print_error_and_die('Option -a|--arch must be used with mode ' + _args.mode)

        if not _args.endian:
            Utils.print_error_and_die('Option -e|--endian must be used with mode ' + _args.mode)

        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--format', 'raw'], shell=True)
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--arch', _args.arch], shell=True)
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--bit-size', '32'], shell=True)
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--file-class', '32'], shell=True)
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--endian', _args.endian], shell=True)

        if RAW_ENTRY_POINT != '':
            subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--entry-point', RAW_ENTRY_POINT], shell=True)

        if RAW_SECTION_VMA != '':
            subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--section-vma', RAW_SECTION_VMA], shell=True)

    ##
    ## Call fileinfo to create an initial config file.
    ##
    FILEINFO_PARAMS = ['-c', CONFIG, '--similarity', IN, '--no-hashes=all']

    if _args.fileinfo_verbose:
        FILEINFO_PARAMS.append('-c ' + CONFIG + ' --similarity --verbose ' + IN)

    for par in config.FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES:
        FILEINFO_PARAMS.append('--crypto ' + ' '.join(config.FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES))

    if _args.fileinfo_use_all_external_patterns:
        for par in config.FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES:
            FILEINFO_PARAMS = '(--crypto ' + par + ')'

    if _args.max_memory:
        FILEINFO_PARAMS.append('--max-memory ' + _args.max_memory)
    elif not _args.no_memory_limit:
        # By default, we want to limit the memory of fileinfo into half of
        # system RAM to prevent potential black screens on Windows (#270).
        FILEINFO_PARAMS = '(--max-memory-half-ram)'

    print()
    print('##### Gathering file information...')
    print('RUN: ' + config.FILEINFO + ' ' +  ' '.join(FILEINFO_PARAMS))

    if _args.generate_log != '':
        FILEINFO_AND_TIME_OUTPUT = os.popen(TIME + ' \'' + config.FILEINFO + '\' \''
                                            + ' '.join(FILEINFO_PARAMS) + '\' 2>&1').read().rstrip('\n')

        FILEINFO_RC = 0 #_rc0 #TODO use fileinfo rc
        LOG_FILEINFO_RC = get_tool_rc(FILEINFO_RC, FILEINFO_AND_TIME_OUTPUT)

        LOG_FILEINFO_RUNTIME = get_tool_runtime(FILEINFO_AND_TIME_OUTPUT)
        LOG_FILEINFO_MEMORY = get_tool_memory_usage(FILEINFO_AND_TIME_OUTPUT)
        LOG_FILEINFO_OUTPUT = get_tool_output(FILEINFO_AND_TIME_OUTPUT)
        print(LOG_FILEINFO_OUTPUT)
    else:
        _rc0 = subprocess.call([config.FILEINFO, ' '.join(FILEINFO_PARAMS)], shell = True)
        FILEINFO_RC = _rc0

    if int(FILEINFO_RC) != 0:
        if _args.generate_log:
            generate_log()

        cleanup()
        # The error message has been already reported by fileinfo in stderr.
        Utils.print_error_and_die('')

    check_whether_decompilation_should_be_forcefully_stopped('fileinfo')

    ##
    ## Unpacking.
    ##
    UNPACK_PARAMS = ['--extended-exit-codes', '--output ', OUT_UNPACKED, IN]

    if _args.max_memory:
        UNPACK_PARAMS.append('--max-memory ' + _args.max_memory)
    elif not _args.no_memory_limit:
        # By default, we want to limit the memory of retdec-unpacker into half
        # of system RAM to prevent potential black screens on Windows (#270).
        UNPACK_PARAMS.append('--max-memory-half-ram')

    if _args.generate_log != '':
        LOG_UNPACKER_OUTPUT = os.popen(config.UNPACK + ' \'' + ' '.join(UNPACK_PARAMS) + '\' 2>&1').read().rstrip('\n')

        UNPACKER_RC = _rc0
        LOG_UNPACKER_RC = UNPACKER_RC
    else:
        UNPACKER_RC = subprocess.call([config.UNPACK, ' '.join(UNPACK_PARAMS)], shell = True)

    check_whether_decompilation_should_be_forcefully_stopped('unpacker')

    # RET_UNPACK_OK=0
    # RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK=1
    # RET_NOTHING_TO_DO=2
    # RET_UNPACKER_FAILED_OTHERS_OK=3
    # RET_UNPACKER_FAILED=4
    if UNPACKER_RC == 0 or UNPACKER_RC == 1 or UNPACKER_RC == 3:
        # Successfully unpacked -> re-run fileinfo to obtain fresh information.
        IN = OUT_UNPACKED
        FILEINFO_PARAMS = ['-c', CONFIG, '--similarity', IN, '--no-hashes=all']

        if _args.fileinfo_verbose != '':
            FILEINFO_PARAMS = ['-c', CONFIG, '--similarity', '--verbose', IN]

        FILEINFO_PARAMS.append('--crypto ' + ' '.join(config.FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES))

        if _args.fileinfo_use_all_external_patterns:
            FILEINFO_PARAMS.append('--crypto ' + ' '.join(config.FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES))

        if not _args.max_memory == '':
            FILEINFO_PARAMS.append('--max-memory ' + _args.max_memory)
        elif _args.no_memory_limit == '':
        # By default, we want to limit the memory of fileinfo into half of
        # system RAM to prevent potential black screens on Windows (#270).
            FILEINFO_PARAMS.append('--max-memory-half-ram')

        print()
        print('##### Gathering file information after unpacking...')
        print('RUN: ' + config.FILEINFO + ' ' + ' '.join(FILEINFO_PARAMS))

        if _args.generate_log != '':
            FILEINFO_AND_TIME_OUTPUT = os.popen(
                TIME + ' \'' + config.FILEINFO + '\' \'' + ' '.join(FILEINFO_PARAMS) + '\' 2>&1').read().rstrip(
            '\n')

            FILEINFO_RC = _rc0

            LOG_FILEINFO_RC = get_tool_rc(FILEINFO_RC, FILEINFO_AND_TIME_OUTPUT)
            FILEINFO_RUNTIME = get_tool_runtime(FILEINFO_AND_TIME_OUTPUT)
            LOG_FILEINFO_RUNTIME = (LOG_FILEINFO_RUNTIME + FILEINFO_RUNTIME)
            FILEINFO_MEMORY = get_tool_memory_usage(FILEINFO_AND_TIME_OUTPUT)
            LOG_FILEINFO_MEMORY = (LOG_FILEINFO_MEMORY + FILEINFO_MEMORY) / 2
            LOG_FILEINFO_OUTPUT = get_tool_output(FILEINFO_AND_TIME_OUTPUT)
            print(LOG_FILEINFO_OUTPUT)
        else:
            FILEINFO_RC = subprocess.call([config.FILEINFO, ' '.join(FILEINFO_PARAMS)], shell = True)

        if FILEINFO_RC != 0:
            if _args.generate_log:
                generate_log()

            cleanup()
            # The error message has been already reported by fileinfo in stderr.
            Utils.print_error_and_die('')

        print_warning_if_decompiling_bytecode()

    # Check whether the architecture was specified.
    if _args.arch:
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--arch', _args.arch], shell=True)
    else:
        # Get full name of the target architecture including comments in parentheses
        ARCH_FULL = os.popen(
            '\'' + config.CONFIGTOOL + '\' \'' + CONFIG + '\' --read --arch | awk \'{print tolower($0').read().rstrip(
            '\n')

        # Strip comments in parentheses and all trailing whitespace
        # todo (ARCH_FULL % (*) what is this
        _args.arch = ARCH_FULL # os.popen('echo ' + (ARCH_FULL % (*) + ' | sed -e s / ^ [[: space:]] * // \'').read().rstrip('\n')

    # Get object file format.
    FORMAT = os.popen(
        '\'' + config.CONFIGTOOL + '\' \'' + CONFIG + '\' --read --format | awk \'{print tolower($1').read().rstrip(
            '\n')

    # Intel HEX needs architecture to be specified
    if FORMAT == 'ihex':
        if not _args.arch or _args.arch == 'unknown' or _args.arch == '':
            Utils.print_error_and_die('Option -a|--arch must be used with format ' + FORMAT)

        if not _args.endian:
            Utils.print_error_and_die('Option -e|--endian must be used with format ' + FORMAT)

        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--arch', _args.arch], shell=True)
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--bit-size', '32'], shell=True)
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--file-class', '32'], shell=True)
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--endian', _args.endian], shell=True)

    # Check whether the correct target architecture was specified.
    if _args.arch == 'arm' or _args.arch == 'thumb':
        ORDS_DIR = config.ARM_ORDS_DIR
    elif _args.arch == 'x86':
        ORDS_DIR = config.X86_ORDS_DIR
    elif _args.arch == 'powerpc' or _args.arch == 'mips' or _args.arch == 'pic32':
        pass
    else:
        # nothing
        if _args.generate_log:
            generate_log()

            cleanup()
            Utils.print_error_and_die('Unsupported target architecture '' + (_args.arch^^) + ''. Supported architectures: Intel x86, ARM, ARM + Thumb, MIPS, PIC32, PowerPC.')

    # Check file class (e.g. 'ELF32', 'ELF64'). At present, we can only decompile 32-bit files.
    # Note: we prefer to report the 'unsupported architecture' error (above) than this 'generic' error.
    FILECLASS = os.popen('\'' + config.CONFIGTOOL + '\' \'' + CONFIG + '\' --read --file-class').read().rstrip('\n')

    if FILECLASS != '16' or FILECLASS != '32':
        if _args.generate_log != '':
            generate_log()

        cleanup()
        Utils.print_error_and_die('Unsupported target format '' + (FORMAT^^) + (FILECLASS) + ''. Supported formats: ELF32, PE32, Intel HEX 32, Mach-O 32.')

    # Set path to statically linked code signatures.
    #
    # TODO: Using ELF for IHEX is ok, but for raw, we probably should somehow decide between ELF and PE, or use both, for RAW.
    SIG_FORMAT = FORMAT

    if SIG_FORMAT == 'ihex' or SIG_FORMAT == 'raw':
        SIG_FORMAT = 'elf'

    ENDIAN = os.popen('\'' + config.CONFIGTOOL + '\' \'' + CONFIG + '\' --read --endian').read().rstrip('\n')

    if _args.endian == 'little':
        SIG_ENDIAN = 'le'
    elif _args.endian == 'big':
        SIG_ENDIAN = 'be'
    else:
        SIG_ENDIAN = ''

    SIG_ARCH = _args.arch

    if SIG_ARCH == 'pic32':
        SIG_ARCH = 'mips'

    SIGNATURES_DIR = config.GENERIC_SIGNATURES_DIR + '/' + SIG_FORMAT + '/' + FILECLASS + '/' + SIG_ENDIAN + '/' + (
        SIG_ARCH)

    print_warning_if_decompiling_bytecode()

    # Decompile unreachable functions.
    if _args.keep_unreachable_funcs:
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--keep-unreachable-funcs', 'true'], shell=True)

    # Get signatures from selected archives.
    if len(_args.static_code_archive) > 0:
        print()
        print('##### Extracting signatures from selected archives...')

    lib_index = 0
    for lib in _args.static_code_archive:

        print('Extracting signatures from file '' + (LIB) + ''')
        CROP_ARCH_PATH = os.popen('basename \'' + lib + '\' | LC_ALL=C sed -e \'s/[^A-Za-z0-9_.-]/_/g\'').read().rstrip('\n')
        SIG_OUT = OUT + '.' + CROP_ARCH_PATH + '.' + lib_index + '.yara'

        if (subprocess.call(config.SIG_FROM_LIB + ' ' + lib + ' ' + '--output' + ' ' + SIG_OUT, shell=True,
                            stderr=subprocess.STDOUT, stdout=open(os.devnull, 'wb'))):
            subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--user-signature', SIG_OUT], shell=True)
            SIGNATURES_TO_REMOVE = '(' + SIG_OUT + ')'
        else:
            Utils.print_warning('Failed extracting signatures from file \'' + lib + '\'')

        lib_index += 1

    # Store paths of signature files into config for frontend.
    if not _args.no_default_static_signatures:
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--signatures', SIGNATURES_DIR], shell=True)

    # User provided signatures.
    for i in _args.static_code_sigfile:
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--user-signature', i], shell=True)

    # Store paths of type files into config for frontend.
    # TODO doesnt even exist in sh except here
    #if os.path.isdir(GENERIC_TYPES_DIR):
    #    subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--types', GENERIC_TYPES_DIR], shell=True)

    # Store path of directory with ORD files into config for frontend (note: only directory, not files themselves).
    if os.path.isdir(ORDS_DIR):
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--ords', ORDS_DIR + '/'], shell=True)

    # Store paths to file with PDB debugging information into config for frontend.
    if os.path.exists(_args.pdb):
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--pdb-file', _args.pdb], shell=True)

    # Store file names of input and output into config for frontend.
    subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--input-file', IN], shell=True)
    subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--frontend-output-file', OUT_FRONTEND_LL],
                    shell=True)
    subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--output-file', OUT], shell=True)

    # Store decode only selected parts flag.
    if _args.selected_decode_only:
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--decode-only-selected', 'true'], shell=True)
    else:
        subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--decode-only-selected', 'false'], shell=True)

    # Store selected functions or selected ranges into config for frontend.
    if _args.selected_functions:
        for f in _args.selected_functions:
            subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--selected-func', f], shell=True)

    if _args.selected_ranges:
        for r in _args.selected_ranges:
            subprocess.call([config.CONFIGTOOL, CONFIG, '--write', '--selected-range', r], shell=True)

    # Assignment of other used variables.
    # We have to ensure that the .bc version of the decompiled .ll file is placed
    # in the same directory as are other output files. Otherwise, there may be
    # race-condition problems when the same input .ll file is decompiled in
    # parallel processes because they would overwrite each other's .bc file. This
    # is most likely to happen in regression tests in the 'll' mode.
    OUT_BACKEND = OUT + '.backend'
    # If the input file is the same as $OUT_BACKEND_LL below, then we have to change the name of
    # $OUT_BACKEND. Otherwise, the input file would get overwritten during the conversion.
    if OUT_FRONTEND_LL == OUT_BACKEND + '.ll':
        OUT_BACKEND = OUT + '.backend.backend'

    OUT_BACKEND_BC = OUT_BACKEND + '.bc'
    OUT_BACKEND_LL = OUT_BACKEND + '.ll'

    BIN2LLVMIR_PARAMS = []
    ##
    ## Decompile the binary into LLVM IR.
    ##
    if _args.keep_unreachable_funcs:
        # Prevent bin2llvmir from removing unreachable functions.
        BIN2LLVMIR_PARAMS = os.popen('sed \' s / -unreachable - funcs * // g\' <<< \'' + config.BIN2LLVMIR_PARAMS + '\'').read().rstrip('\n')

    if not CONFIG and CONFIG_DB:
        CONFIG = CONFIG_DB
        BIN2LLVMIR_PARAMS.append('-provider-init -config-path ' + CONFIG + ' -decoder')

    if _args.max_memory:
        BIN2LLVMIR_PARAMS.append('-max-memory ' + _args.max_memory)
    elif not _args.no_memory_limit:
        # By default, we want to limit the memory of bin2llvmir into half of
        # system RAM to prevent potential black screens on Windows (#270).
        BIN2LLVMIR_PARAMS.append('-max-memory-half-ram')

    print()
    print('##### Decompiling ' + IN + ' into ' + OUT_BACKEND_BC + '...')
    print('RUN: ' + config.BIN2LLVMIR + ' ' + ' '.join(BIN2LLVMIR_PARAMS) + ' -o ' + OUT_BACKEND_BC)

    if _args.generate_log != '':
        PID = 0
        BIN2LLVMIR_RC = 0

        def thread1():
            subprocess.call(
                TIME + ' ' + config.BIN2LLVMIR + ' ' + ''.join(BIN2LLVMIR_PARAMS) + ' ' + '-o' + ' ' + (
                OUT_BACKEND_BC), shell = True, stdout = open(TOOL_LOG_FILE, 'wb'), stderr = subprocess.STDOUT)

            threading.Thread(target=thread1).start()

            PID = 0 #TODO $! Expand.exclamation()

        def thread2():
            timed_kill(PID)

        threading.Thread(target=thread2).start()

        subprocess.call('wait' + ' ' + PID, shell=True, stderr=subprocess.STDOUT, stdout=open(os.devnull, 'wb'))

        BIN2LLVMIR_RC = 0# TODO use rc _rc2
        BIN2LLVMIR_AND_TIME_OUTPUT = os.popen('cat \'' + TOOL_LOG_FILE + '\'').read().rstrip('\n')
        LOG_BIN2LLVMIR_RC = get_tool_rc(BIN2LLVMIR_RC, BIN2LLVMIR_AND_TIME_OUTPUT)
        LOG_BIN2LLVMIR_RUNTIME = get_tool_runtime(BIN2LLVMIR_AND_TIME_OUTPUT)
        LOG_BIN2LLVMIR_MEMORY = get_tool_memory_usage(BIN2LLVMIR_AND_TIME_OUTPUT)
        LOG_BIN2LLVMIR_OUTPUT = get_tool_output(BIN2LLVMIR_AND_TIME_OUTPUT)
        print(LOG_BIN2LLVMIR_OUTPUT, end='')
    else:
        BIN2LLVMIR_RC = subprocess.call([config.BIN2LLVMIR, ' '.join(BIN2LLVMIR_PARAMS)]), '-o', OUT_BACKEND_BC], shell = True)

    if BIN2LLVMIR_RC != 0:
        if _args.generate_log:
            generate_log()

        cleanup()
        Utils.print_error_and_die('Decompilation to LLVM IR failed')

    check_whether_decompilation_should_be_forcefully_stopped('bin2llvmir')

# modes 'bin' || 'raw'


# LL mode goes straight to backend.
if _args.mode == 'll':
    OUT_BACKEND_BC = IN
    CONFIG = CONFIG_DB


# Create parameters for the $LLVMIR2HLL call.
LLVMIR2HLL_PARAMS = ['(-target-hll=' + HLL + ' -var-renamer=' + (
    _args.backend_var_renamer) + ' -var-name-gen=fruit -var-name-gen-prefix= -call-info-obtainer=' + (
    _args.backend_call_info_obtainer) + ' -arithm-expr-evaluator=' + (
    _args.backend_arithm_expr_evaluator) + ' -validate-module -llvmir2bir-converter=' + (
    _args.backend_llvmir2bir_converter) + ' -o ' + OUT + ' ' + OUT_BACKEND_BC + ')']

if _args.backend_no_debug:
    LLVMIR2HLL_PARAMS.append('-enable-debug')

if _args.backend_no_debug_comments:
    LLVMIR2HLL_PARAMS.append('-emit-debug-comments')

if _args.config:
    LLVMIR2HLL_PARAMS = '(-config-path=' + _args.config + ')'

if _args.keep_unreachable_funcs:
    LLVMIR2HLL_PARAMS = '(-keep-unreachable-funcs)'

if _args.backend_semantics:
    LLVMIR2HLL_PARAMS = '(-semantics ' + _args.backend_semantics + ')'

if _args.backend_enabled_opts:
    LLVMIR2HLL_PARAMS = '(-enabled-opts=' + _args.backend_enabled_opts + ')'

if _args.backend_disabled_opts:
    LLVMIR2HLL_PARAMS = '(-disabled-opts=' + _args.backend_disabled_opts + ')'

if _args.backend_no_opts:
    LLVMIR2HLL_PARAMS = '(-no-opts)'

if _args.backend_aggressive_opts:
    LLVMIR2HLL_PARAMS = '(-aggressive-opts)'

if _args.backend_no_var_renaming:
    LLVMIR2HLL_PARAMS = '(-no-var-renaming)'

if _args.backend_no_symbolic_names:
    LLVMIR2HLL_PARAMS = '(-no-symbolic-names)'

if _args.backend_keep_all_brackets:
    LLVMIR2HLL_PARAMS = ('(-keep-all-brackets)'

if _args.backend_keep_library_funcs:
    LLVMIR2HLL_PARAMS = '(-keep-library-funcs)'

if _args.backend_no_time_varying_info:
    LLVMIR2HLL_PARAMS = '(-no-time-varying-info)'

if _args.backend_no_compound_operators:
    LLVMIR2HLL_PARAMS = '(-no-compound-operators)'

if _args.backend_find_patterns:
    LLVMIR2HLL_PARAMS = '(-find-patterns ' + _args.backend_find_patterns + ')'

if _args.backend_emit_cg:
    LLVMIR2HLL_PARAMS = '(-emit-cg)'

if _args.backend_force_module_name:
    LLVMIR2HLL_PARAMS = '(-force-module-name=' + _args.backend_force_module_name + ')'

if _args.backend_strict_fpu_semantics:
    LLVMIR2HLL_PARAMS = '(-strict-fpu-semantics)'

if _args.backend_emit_cfg):
    LLVMIR2HLL_PARAMS = '(-emit-cfgs)'

if _args.backend_cfg_test:
    LLVMIR2HLL_PARAMS = '(--backend-cfg-test)'

if _args.max_memory:
    LLVMIR2HLL_PARAMS = '(-max-memory ' + _args.max_memory + ')'

elif not _args.no_memory_limit:
    # By default, we want to limit the memory of llvmir2hll into half of system
    # RAM to prevent potential black screens on Windows (#270).
    LLVMIR2HLL_PARAMS.append('-max-memory-half-ram')
    # Decompile the optimized IR code.


print()
print('##### Decompiling ' + OUT_BACKEND_BC + ' into ' + OUT + '...')
print('RUN: ' + config.LLVMIR2HLL + ' ' + ' '.join(LLVMIR2HLL_PARAMS))

if _args.generate_log:
    PID = 0

    def thread3():
        subprocess.call(
            TIME + ' ' + config.LLVMIR2HLL + ' ' + ' '.join(LLVMIR2HLL_PARAMS), shell = True, stdout = open(
                TOOL_LOG_FILE, 'wb'), stderr = subprocess.STDOUT)

        threading.Thread(target=thread3).start()

        PID = 0 #TODO Expand.exclamation()

        def thread4():
            timed_kill(PID)


    threading.Thread(target=thread4).start()

    subprocess.call('wait' + ' ' + PID, shell=True, stderr=subprocess.STDOUT, stdout=open(os.devnull, 'wb'))

    LLVMIR2HLL_RC =  0 # use rc _rc4
    LLVMIR2HLL_AND_TIME_OUTPUT = os.popen('cat \'' + TOOL_LOG_FILE + '\'').read().rstrip('\n')
    LOG_LLVMIR2HLL_RC = get_tool_rc(LLVMIR2HLL_RC,  LLVMIR2HLL_AND_TIME_OUTPUT)
    LOG_LLVMIR2HLL_RUNTIME = get_tool_runtime(LLVMIR2HLL_AND_TIME_OUTPUT)
    LOG_LLVMIR2HLL_MEMORY = get_tool_memory_usage(LLVMIR2HLL_AND_TIME_OUTPUT)
    LOG_LLVMIR2HLL_OUTPUT = get_tool_output(LLVMIR2HLL_AND_TIME_OUTPUT)

    print(LOG_LLVMIR2HLL_OUTPUT)
    # Wait a bit to ensure that all the memory that has been assigned to the tool was released.
    time.sleep(0.1)
else:
    LLVMIR2HLL_RC = subprocess.call([config.LLVMIR2HLL, ' '.join(LLVMIR2HLL_PARAMS)], shell = True)

if int(LLVMIR2HLL_RC) != 0:
    if _args.generate_log:
        generate_log()

    cleanup()
    Utils.print_error_and_die('Decompilation of file %s failed' % OUT_BACKEND_BC)

check_whether_decompilation_should_be_forcefully_stopped('llvmir2hll')


# Convert .dot graphs to desired format.
if ((_args.backend_emit_cg and _args.backend_cg_conversion == 'auto') or (
        _args.backend_emit_cfg and _args.backend_cfg_conversion == 'auto')):
    print()
    print('##### Converting .dot files to the desired format...')

if _args.backend_emit_cg and _args.backend_cg_conversion == 'auto':
    print('RUN: dot -T' + _args.graph_format + ' ' + OUT + '.cg.dot > ' + OUT + '.cg.' + _args.graph_format)
    subprocess.call('dot' + ' ' + '-T' + _args.graph_format + ' ' + OUT + '.cg.dot', shell=True,
                    stdout = open(OUT + '.cg.' + _args.graph_format, 'wb'))


if _args.backend_emit_cfg and _args.backend_cfg_conversion == 'auto':
    for cfg in glob.glob(OUT + '.cfg.*.dot'):
        print('RUN: dot -T' + _args.graph_format + ' ' + cfg + ' > ' + (os.path.splitext(cfg)[0] + '.' + _args.graph_format)
        subprocess.call('dot' + ' ' + '-T' + _args.graph_format + ' ' + cfg, shell=True,
                        stdout = open((os.path.splitext(cfg)[0]) + '.' + _args.graph_format, 'wb'))


# Remove trailing whitespace and the last redundant empty new line from the
# generated output (if any). It is difficult to do this in the back-end, so we
# do it here.
# Note: Do not use the -i flag (in-place replace) as there is apparently no way
#       of getting sed -i to work consistently on both MacOS and Linux.
_rc4 = subprocess.call(
'sed' + ' ' + '-e' + ' ' + ':a' + ' ' + '-e' + ' ' + '/^\\n*$/{$d;N;};/\\n$/ba' + ' ' + '-e' + ' ' + 's/[[:space:]]*$//',
shell = True, stdin = open(OUT, 'rb'), stdout = open(OUT + '.tmp', 'wb'))

shutil.move(OUT + '.tmp', OUT)

# Colorize output file.
if _args.color_for_ida:
    subprocess.call([config.IDA_COLORIZER, OUT, CONFIG], shell=True)

# Store the information about the decompilation into the JSON file.
if _args.generate_log:
    generate_log()

# Success!
cleanup(_args)
print()
print('##### Done!')
