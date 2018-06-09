#! /usr/bin/env python3

"""Decompiles the given file into the selected target high-level language."""
import argparse
import hashlib
import sys
import os
import subprocess
import threading
import glob
import re

import retdec_config as config
import retdec_utils as utils


class Expand(object):
    @staticmethod
    def at():
        if (len(sys.argv) < 2):
            return []
        return sys.argv[1:]

    @staticmethod
    def hash():
        return len(sys.argv) - 1

    @staticmethod
    def exclamation():
        pass  # raise Bash2PyException('$! unsupported')

    @staticmethod
    def underbar():
        pass  # raise Bash2PyException('$_ unsupported')

    @staticmethod
    def colonMinus(name, value=''):
        ret = GetValue(name)
        if (ret is None or ret == ''):
            ret = value
        return ret

    @staticmethod
    def colonEq(name, value=''):
        ret = GetValue(name)
        if (ret is None or ret == ''):
            SetValue(name, value)
            ret = value
        return ret


def get_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-a', '--arch',
                        dest='arch',
                        default='autodetected',
                        help='Specify target architecture [mips|pic32|arm|thumb|powerpc|x86]. Required if it cannot be autodetected from the input (e.g. raw mode, Intel HEX).')

    parser.add_argument('-e', '--endian',
                        dest='endian',
                        default='autodetected',
                        help='Specify target endianness [little|big]. Required if it cannot be autodetected from the input (e.g. raw mode, Intel HEX).')

    parser.add_argument('-k', '--keep-unreachable-funcs',
                        dest='keep_unreachable_funcs',
                        action='store_true',
                        help='Keep functions that are unreachable from the main function.')

    parser.add_argument('-l', '--target-language',
                        dest='target_language',
                        default='c',
                        help='Target high-level language [c|py].')

    parser.add_argument('-m', '--mode',
                        dest='mode',
                        help='Force the type of decompilation mode [bin|ll|raw] (default: ll if input\'s suffix is \'.ll\', bin otherwise).')

    parser.add_argument('-o', '--output',
                        dest='output',
                        default='file.ext',
                        help='Output file.')

    parser.add_argument('-p', '--pdb',
                        dest='pdb',
                        help='File with PDB debug information.')

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



"""Check proper combination of input arguments.
"""
def check_arguments():
    """Check proper combination of input arguments.
    """
    global IN
    global MODE
    global ARCH
    global PDB_FILE
    global CONFIG_DB
    global NO_CONFIG
    global ENDIAN
    global RAW_ENTRY_POINT
    global RAW_SECTION_VMA
    global AR_NAME
    global AR_INDEX
    global HLL
    global OUT
    global PICKED_FILE
    global SELECTED_RANGES
    global r
    global IFS
    global vs

    # Check whether the input file was specified.
    if str(IN) == '':
        subprocess.call(['print_error_and_die', 'No input file was specified'], shell=True)
    # Try to detect desired decompilation mode if not set by user.
    # We cannot detect 'raw' mode because it overlaps with 'bin' (at least not based on extension).
    if MODE == '':
        if (str(IN: -3) == '.ll' ):
            # Suffix .ll
            MODE = 'll'
        else:
            MODE = 'bin'

    # Print warning message about unsupported combinations of options.
    if str(MODE) == 'll':
        if str(ARCH) != '':
            subprocess.call(['print_warning', 'Option -a|--arch is not used in mode ' + str(MODE)], shell=True)
        if str(PDB_FILE) != '':
            subprocess.call(['print_warning', 'Option -p|--pdb is not used in mode ' + str(MODE)], shell=True)
        if if str(CONFIG_DB) == str():
            not str(NO_CONFIG) != '':
            subprocess.call(
                ['print_error_and_die', 'Option --config or --no-config must be specified in mode ' + str(MODE)],
                shell=True)
    elif str(MODE) == 'raw':
        # Errors -- missing critical arguments.
        if not str(ARCH) != '':
            subprocess.call(['print_error_and_die', 'Option -a|--arch must be used with mode ' + str(MODE)], shell=True)
        if not str(ENDIAN) != '':
            subprocess.call(['print_error_and_die', 'Option -e|--endian must be used with mode ' + str(MODE)],
                            shell=True)
        if not str(RAW_ENTRY_POINT) != '':
            subprocess.call(['print_error_and_die', 'Option --raw-entry-point must be used with mode ' + str(MODE)],
                            shell=True)
        if not str(RAW_SECTION_VMA) != '':
            subprocess.call(['print_error_and_die', 'Option --raw-section-vma must be used with mode ' + str(MODE)],
                            shell=True)
        if not subprocess.call(['is_number', str(RAW_ENTRY_POINT)], shell=True):
            subprocess.call(['print_error_and_die',
                             'Value in option --raw-entry-point must be decimal (e.g. 123) or hexadecimal value (e.g. 0x123)'],
                            shell=True)
        if not subprocess.call(['is_number', str(RAW_SECTION_VMA)], shell=True):
            subprocess.call(['print_error_and_die',
                             'Value in option --raw-section-vma must be decimal (e.g. 123) or hexadecimal value (e.g. 0x123)'],
                            shell=True)
    # Archive decompilation errors.
    if if str(AR_NAME) != '':
        str(AR_INDEX) != '':
        subprocess.call(['print_error_and_die', 'Options --ar-name and --ar-index are mutually exclusive. Pick one.'],
                        shell=True)
    if str(MODE) != 'bin':
        if str(AR_NAME) != '':
            subprocess.call(['print_warning', 'Option --ar-name is not used in mode ' + str(MODE)], shell=True)
        if str(AR_INDEX) != '':
            subprocess.call(['print_warning', 'Option --ar-index is not used in mode ' + str(MODE)], shell=True)
    # Conditional initialization.
    HLL = Bash2Py(Expand.colonEq('HLL', 'c'))

    if str(OUT) == '':
        # No output file was given, so use the default one.
        if (str(IN  ##*.) == 'll' ):
                # Suffix .ll
                OUT = str(IN %.ll) + '.' + str(HLL))
        elif (str(IN  ##*.) == 'exe' ):
        # Suffix .exe
        OUT = str(IN %.exe) + '.' + str(HLL)
        elif (str(IN  ##*.) == 'elf' ):
        # Suffix .elf
        OUT = str(IN %.elf) + '.' + str(HLL)
        elif (str(IN  ##*.) == 'ihex' ):
        # Suffix .ihex
        OUT = str(IN %.ihex) + '.' + str(HLL)
        elif (str(IN  ##*.) == 'macho' ):
        # Suffix .macho
        OUT = str(IN %.macho) + '.' + str(HLL)
        else:
            OUT = str(IN) + str(PICKED_FILE) + '.' + str(HLL)
        # If the output file name matches the input file name, we have to change the
        # output file name. Otherwise, the input file gets overwritten.
        if str(IN) == str(OUT):
            OUT = str(IN %. *) + '.out.' + str(HLL)

        # Convert to absolute paths.
        IN = utils.get_realpath(IN)
        OUT = utils.get_realpath(OUT)

        if os.path.exists(str(PDB_FILE)):
            PDB_FILE = os.popen('get_realpath \'' + str(PDB_FILE) + '\'').read().rstrip('\n')

        # Check that selected ranges are valid.
        if str(SELECTED_RANGES) != '':
            for r in Array(SELECTED_RANGES[ @]]):
                # Check if valid range.
                if not subprocess.call(['is_range', str(r)], shell=True):
                    subprocess.call(['print_error_and_die',
                                     'Range '' + str(r) + '' in option --select-ranges is not a valid decimal (e.g. 123-456) or hexadecimal (e.g. 0x123-0xabc) range.'],
                                    shell=True)
        # Check if first <= last.
        IFS = '-'
        # parser line into array
        if ((vs[0] ] > vs[1]])):
            subprocess.call(['print_error_and_die',
                             'Range '' + str(r) + '' in option --select-ranges is not a valid range: second address must be greater or equal than the first one.'],
                            shell=True)


def print_warning_if_decompiling_bytecode():
    """Prints a warning if we are decompiling bytecode."""

    bytecode = os.popen('\'' + str(config.CONFIGTOOL) + '\' \'' + str(CONFIG) + '\' --read --bytecode').read(). \
        rstrip('\n')

    if bytecode != '':
        utils.print_warning('Detected ' + str(bytecode) + ' bytecode, which cannot be decompiled by our machine-code '
                                                          'decompiler. The decompilation result may be inaccurate.')


def check_whether_decompilation_should_be_forcefully_stopped(tool_name):
    """Checks whether the decompilation should be forcefully stopped because of the
    --stop-after parameter. If so, cleanup is run and the script exits with 0.

    Arguments:

      $1 Name of the tool.

    The function expects the $STOP_AFTER variable to be set.
    """

    global STOP_AFTER
    global GENERATE_LOG

    if STOP_AFTER == tool_name:
        if GENERATE_LOG:
            generate_log()

        cleanup()
        print()
        print('#### Forced stop due to  - -stop - after %s...' % STOP_AFTER)
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

    if CLEANUP:
        subprocess.call(['rm', '-f', str(OUT_UNPACKED)], shell=True)
        subprocess.call(['rm', '-f', str(OUT_FRONTEND_LL)], shell=True)
        subprocess.call(['rm', '-f', str(OUT_FRONTEND_BC)], shell=True)
        if CONFIG != CONFIG_DB:
            subprocess.call(['rm', '-f', str(CONFIG)], shell=True)
        subprocess.call(['rm', '-f', str(OUT_BACKEND_BC)], shell=True)
        subprocess.call(['rm', '-f', str(OUT_BACKEND_LL)], shell=True)
        subprocess.call(['rm', '-f', str(OUT_RESTORED)], shell=True)
        # Archive support
        subprocess.call(['rm', '-f', str(OUT_ARCHIVE)], shell=True)
        # Archive support (Macho-O Universal)
        subprocess.call(['rm', '-f', str(SIGNATURES_TO_REMOVE[ @]])], shell = True)
        # Signatures generated from archives
        if str(TOOL_LOG_FILE) != '':
            subprocess.call(['rm', '-f', str(TOOL_LOG_FILE)], shell=True)

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
    global ORIGINAL_RC
    global OUTPUT
    global SIGNAL_REGEX
    global SIGNAL_NUM
    global BASH_REMATCH
    global RC

    ORIGINAL_RC = return_code
    OUTPUT = output
    SIGNAL_REGEX = 'Command terminated by signal ([0-9]*)'

    if re.search(SIGNAL_REGEX, OUTPUT):
        SIGNAL_NUM = BASH_REMATCH[1]]
        RC = SIGNAL_NUM + 128
    else:
        RC = ORIGINAL_RC
        # We want to be able to distinguish assertions and memory-insufficiency
        # errors. The problem is that both assertions and memory-insufficiency
        # errors make the program exit with return code 134. We solve this by
        # replacing 134 with 135 (SIBGUS, 7) when there is 'std::bad_alloc' in the
        # output. So, 134 will mean abort (assertion error) and 135 will mean
        # memory-insufficiency error.
        if str(RC) == '134' or re.search('std::bad_alloc', OUTPUT):
            RC = 135
        print(RC)

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
    USER_TIME_F = os.popen('egrep \'User time \\(seconds\\').read().rstrip('\n') + ': <<< ' + str(_p1) + ' | cut -d: -f2)'

    SYSTEM_TIME_F = os.popen('egrep \'System time \\(seconds\\').read().rstrip('\n') + ': <<< ' + str(_p1) + ' | cut -d: -f2)'
    RUNTIME_F = os.popen('echo ' + str(USER_TIME_F) + '  +  ' + str(SYSTEM_TIME_F) + ' | bc').read().rstrip('\n')
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
        sys.exit(0)


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
    RSS_KB = os.popen('egrep \'Maximum resident set size \\(kbytes\\').read().rstrip('\n') + ': <<< ' + str(
        tool) + ' | cut -d: -f2)'

    RSS_MB = (RSS_KB // 1024)
    print((RSS_MB if (RSS_MB > 0) else 1))


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
        subprocess.Popen('sed' + ' ' + '-n' + ' ' + '/Command being timed:/q;p', shell=True, stdin=subprocess.PIPE)
        _rc0.communicate(str(_p1) + '\n')
        _rc0 = _rc0.wait()
        sys.exit(0)


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
                sys.exit(0)

        else:
            os.close(_rcr2)
            os.dup2(_rcw2, 1)
            subprocess.call(['sed', 's/\\\\/\\\\\\\\/g'], shell=True)
            sys.exit(0)

    else:
        os.close(_rcr1)
        os.dup2(_rcw1, 1)
        print(_p1)
        sys.exit(0)


#
# Removes color codes from the given text ($1).
#
def remove_colors(_p1):
    subprocess.Popen('sed' + ' ' + '-r' + ' ' + 's/\x1b[^m]*m//g', shell=True, stdin=subprocess.PIPE)
    _rc0.communicate(str(_p1) + '\n')
    _rc0 = _rc0.wait()


#
# Platform-independent alternative to `ulimit -t` or `timeout`.
# Based on http://www.bashcookbook.com/bashinfo/source/bash-4.0/examples/scripts/timeout3
# 1 argument is needed - PID
# Returns - 1 if number of arguments is incorrect
#           0 otherwise
#
def timed_kill(_p1):
    global TIMEOUT
    global timeout
    global DEV_NULL

    if str(Expand.hash()) != '1':
        return (1)
    PID = _p1
    # PID of the target process
    PROCESS_NAME = os.popen('ps -p ' + str(PID) + ' -o comm --no-heading').read().rstrip('\n')

    if str(PROCESS_NAME) == 'time':
        # The program is run through `/usr/bin/time`, so get the PID of the
        # child process (the actual program). Otherwise, if we killed
        # `/usr/bin/time`, we would obtain no output from it (user time, memory
        # usage etc.).
        PID = os.popen('ps --ppid ' + str(PID) + ' -o pid --no-heading | head -n1').read().rstrip('\n')

    if str(TIMEOUT) == '':
        TIMEOUT = 300

    timeout = TIMEOUT

    t = timeout

    while t > 0:
        subprocess.call(['sleep', '1'], shell=True)

        if not subprocess.call('kill' + ' ' + '-0' + ' ' + str(PID), shell=True, stdout=open(os.devnull, 'wb'),
                               stderr=file(str(DEV_NULL), 'wb')):
            exit(0)

    t = t - 1


_rc0 = subprocess.call('kill_tree' + ' ' + str(PID) + ' ' + 'SIGKILL', shell=True, stdout=open(os.devnull, 'wb'),
                       stderr=file(str(DEV_NULL), 'wb'))


#
# Kill process and all its children.
# Based on http://stackoverflow.com/questions/392022/best-way-to-kill-all-child-processes/3211182#3211182
# 2 arguments are needed - PID of process to kill  +  signal type
# Returns - 1 if number of arguments is incorrect
#           0 otherwise
#
def kill_tree(pid):
    if str(Expand.hash()) != '1'or str(Expand.hash()) != '2':
        return 1


    _pid = pid
    _sig = Expand.colonMinus('2', 'TERM')
    _rc0 = subprocess.call(['kill', '-stop', Expand.underbar() + 'pid'], shell=True)

    # needed to stop quickly forking parent from producing child between child killing and parent killing
    for _child in os.popen('ps -o pid --no-headers --ppid \'' + Expand.underbar() + 'pid\'').read().rstrip('\n'):
        kill_tree(Expand.underbar() + 'child', Expand.underbar() + 'sig')
    _rc0 = subprocess.call(['kill', '-' + Expand.underbar() + 'sig', Expand.underbar() + 'pid'], shell=True)



"""Generate a MD5 checksum from a given string ($1)."""
def string_to_md5(input):
    m = hashlib.md5()
    m.update(input)

    return m.hexdigest()


def generate_log():
    global LOG_FILE
    global OUT
    global LOG_DECOMPILATION_END_DATE
    global LOG_FILEINFO_OUTPUT
    global LOG_UNPACKER_OUTPUT
    global LOG_BIN2LLVMIR_OUTPUT
    global LOG_LLVMIR2HLL_OUTPUT
    global log_structure
    global IN
    global PDB_FILE
    global LOG_DECOMPILATION_START_DATE
    global MODE
    global ARCH
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
    LOG_FILEINFO_OUTPUT = os.popen('json_escape \'' + str(LOG_FILEINFO_OUTPUT) + '\'').read().rstrip('\n')
    LOG_UNPACKER_OUTPUT = os.popen('json_escape \'' + str(LOG_UNPACKER_OUTPUT) + '\'').read().rstrip('\n')
    LOG_BIN2LLVMIR_OUTPUT = os.popen('remove_colors \'' + str(LOG_BIN2LLVMIR_OUTPUT) + '\'').read().rstrip('\n')
    LOG_BIN2LLVMIR_OUTPUT = os.popen('json_escape \'' + str(LOG_BIN2LLVMIR_OUTPUT) + '\'').read().rstrip('\n')
    LOG_LLVMIR2HLL_OUTPUT = os.popen('remove_colors \'' + str(LOG_LLVMIR2HLL_OUTPUT) + '\'').read().rstrip('\n')
    LOG_LLVMIR2HLL_OUTPUT = os.popen('json_escape \'' + str(LOG_LLVMIR2HLL_OUTPUT) + '\'').read().rstrip('\n')
    log_structure = '{\n\t\'input_file\' : \'%s\',\n\t\'pdb_file\' : \'%s\',\n\t\'start_date\' :' \
                    ' \'%s\',\n\t\'end_date\' : \'%s\',\n\t\'mode\' : \'%s\',\n\t\'arch\' : \'%s\',\n\t\'format\'' \
                    ' : \'%s\',\n\t\'fileinfo_rc\' : \'%s\',\n\t\'unpacker_rc\' : \'%s\',\n\t\'bin2llvmir_rc\'' \
                    ' : \'%s\',\n\t\'llvmir2hll_rc\' : \'%s\',\n\t\'fileinfo_output\' :' \
                    ' \'%s\',\n\t\'unpacker_output\' : \'%s\',\n\t\'bin2llvmir_output\' :' \
                    ' \'%s\',\n\t\'llvmir2hll_output\' : \'%s\',\n\t\'fileinfo_runtime\' :' \
                    ' \'%s\',\n\t\'bin2llvmir_runtime\' : \'%s\',\n\t\'llvmir2hll_runtime\' :' \
                    ' \'%s\',\n\t\'fileinfo_memory\' : \'%s\',\n\t\'bin2llvmir_memory\' :' \
                    ' \'%s\',\n\t\'llvmir2hll_memory\' : \'%s\'\n}\n'

    print(str(log_structure) % (
        str(IN), str(PDB_FILE), str(LOG_DECOMPILATION_START_DATE), str(LOG_DECOMPILATION_END_DATE), str(MODE),
        str(ARCH),
        str(FORMAT), str(LOG_FILEINFO_RC), str(LOG_UNPACKER_RC), str(LOG_BIN2LLVMIR_RC), str(LOG_LLVMIR2HLL_RC),
        str(LOG_FILEINFO_OUTPUT), str(LOG_UNPACKER_OUTPUT), str(LOG_BIN2LLVMIR_OUTPUT), str(LOG_LLVMIR2HLL_OUTPUT),
        str(LOG_FILEINFO_RUNTIME), str(LOG_BIN2LLVMIR_RUNTIME), str(LOG_LLVMIR2HLL_RUNTIME), str(LOG_FILEINFO_MEMORY),
        str(LOG_BIN2LLVMIR_MEMORY), str(LOG_LLVMIR2HLL_MEMORY)))


# Check script arguments.
PARSED_OPTIONS = os.popen('getopt -o \'' + str(GETOPT_SHORTOPT) + '\' -l \'' + str(GETOPT_LONGOPT) + '\' -n \'' + str(
        SCRIPT_NAME) + '\' -- \'' + Str(Expand.at()) + '\'').read().rstrip('\n')

# Bad arguments.
if _rc0 != 0:
    utils.print_error_and_die('Getopt - parsing parameters fail')

eval('set', '--', PARSED_OPTIONS)

while True:

    if str(sys.argv[1]) == '-a' or str(sys.argv[1]) == '--arch':
        # Target architecture.
        if str(ARCH) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: -a|--arch'], shell=True)
        if str(sys.argv[
                   2]) != 'mips' os.path.exists(str(sys.argv[2])) '!='  '-a' str(sys.argv[2]) != 'arm' os.path.exists(str(sys.argv[2])) '!='  '-a' str(sys.argv[2]) != 'powerpc' os.path.exists(str(sys.argv[2]))'!=' != '':
            subprocess.call(['print_error_and_die',
                             'Unsupported target architecture '' + str(sys.argv[2]) + ''. Supported architectures: Intel x86, ARM, ARM + Thumb, MIPS, PIC32, PowerPC.'],
                            shell=True)
        ARCH = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '-e' or str(sys.argv[1]) == '--endian':
        # Endian.
        if str(ENDIAN) != '':
            utils.print_error_and_die('Duplicate option: -e|--endian')
        ENDIAN = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help':
        # Help.
        print_help()
        exit(0)
    elif str(sys.argv[1]) == '-k' or str(sys.argv[1]) == '--keep-unreachable-funcs':
        # Keep unreachable functions.
        # Do not check if this parameter is a duplicate because when both
        # --select-ranges or --select--functions and -k is specified, the
        # decompilation fails.
        KEEP_UNREACHABLE_FUNCS = 1
        subprocess.call(['shift'], shell=True)
    elif str(sys.argv[1]) == '-l' or str(sys.argv[1]) == '--target-language':
        # Target language.
        if str(HLL) != '':
            utils.print_error_and_die('Duplicate option: -l|--target-language')
        if str(sys.argv[2]) != 'c' and os.path.exists(str(sys.argv[2])) != '':
            utils.print_error_and_die('Unsupported target language '' + str(sys.argv[2]) + ''. Supported languages: C, Python.')
        HLL = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '-m' or str(sys.argv[1]) == '--mode':
        # Decompilation mode.
        if str(MODE) != '':
            utils.print_error_and_die('Duplicate option: -m|--mode')
        if str(sys.argv[2]) != 'bin' os.path.exists(str(sys.argv[2])) '!='  '-a' str(sys.argv[2]) != 'raw':
            utils.print_error_and_die('Unsupported decompilation mode '' + str(sys.argv[2]) + ''. Supported modes: bin, ll, raw.')
        MODE = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '-o' or str(sys.argv[1]) == '--output':
        # Output file.
        if str(OUT) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: -o|--output'], shell=True)
        OUT = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '-p' or str(sys.argv[1]) == '--pdb':
        # File containing PDB debug information.
        if str(PDB_FILE) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: -p|--pdb'], shell=True)
        PDB_FILE = sys.argv[2]
        if not os.access, R_OK) ):
            subprocess.call(
                ['print_error_and_die', 'The input PDB file '' + str(PDB_FILE) + '' does not exist or is not readable'],
                shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '--backend-aggressive-opts':
        # Enable aggressive optimizations.
        if str(BACKEND_AGGRESSIVE_OPTS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-aggressive-opts'], shell=True)
        BACKEND_AGGRESSIVE_OPTS = 1
        subprocess.call(['shift'], shell=True)
    elif str(sys.argv[1]) == '--backend-arithm-expr-evaluator':
        # Name of the evaluator of arithmetical expressions.
        if str(BACKEND_ARITHM_EXPR_EVALUATOR) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-arithm-expr-evaluator'], shell=True)
        BACKEND_ARITHM_EXPR_EVALUATOR = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '--backend-call-info-obtainer':
        # Name of the obtainer of information about function calls.
        if str(BACKEND_CALL_INFO_OBTAINER) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-call-info-obtainer'], shell=True)
        BACKEND_CALL_INFO_OBTAINER = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '--backend-cfg-test':
        # Unify the labels in the emitted CFG.
        if str(BACKEND_CFG_TEST) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-cfg-test'], shell=True)
        BACKEND_CFG_TEST = 1
        subprocess.call(['shift'], shell=True)
    elif str(sys.argv[1]) == '--backend-disabled-opts':
        # List of disabled optimizations in the backend.
        if str(BACKEND_DISABLED_OPTS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-disabled-opts'], shell=True)
        BACKEND_DISABLED_OPTS = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '--backend-emit-cfg':
        # Emit a CFG of each function in the backend IR.
        if str(BACKEND_EMIT_CFG) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-emit-cfg'], shell=True)
        BACKEND_EMIT_CFG = 1
        subprocess.call(['shift'], shell=True)
    elif str(sys.argv[1]) == '--backend-emit-cg':
        # Emit a CG of the decompiled module in the backend IR.
        if str(BACKEND_EMIT_CG) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-emit-cg'], shell=True)
        BACKEND_EMIT_CG = 1
        subprocess.call(['shift'], shell=True)
    elif str(sys.argv[1]) == '--backend-cg-conversion':
        # Should the CG from the backend be converted automatically into the desired format?.
        if str(BACKEND_CG_CONVERSION) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-cg-conversion'], shell=True)
        if str(sys.argv[2]) != 'auto' os.path.exists(str(sys.argv[2]))'!=' != '':
            subprocess.call(['print_error_and_die',
                             'Unsupported CG conversion mode '' + str(sys.argv[2]) + ''. Supported modes: auto, manual.'],
                            shell=True)
        BACKEND_CG_CONVERSION = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '--backend-cfg-conversion':
        # Should CFGs from the backend be converted automatically into the desired format?.
        if str(BACKEND_CFG_CONVERSION) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-cfg-conversion'], shell=True)
        if str(sys.argv[2]) != 'auto' os.path.exists(str(sys.argv[2]))'!=' != '':
            subprocess.call(['print_error_and_die',
                             'Unsupported CFG conversion mode '' + str(sys.argv[2]) + ''. Supported modes: auto, manual.'],
                            shell=True)
        BACKEND_CFG_CONVERSION = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif str(sys.argv[1]) == '--backend-enabled-opts':
        # List of enabled optimizations in the backend.
        if str(BACKEND_ENABLED_OPTS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-enabled-opts'], shell=True)
        BACKEND_ENABLED_OPTS = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--backend-find-patterns'):
        # Try to find patterns.
        if str(BACKEND_FIND_PATTERNS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-find-patterns'], shell=True)
        BACKEND_FIND_PATTERNS = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--backend-force-module-name'):
        # Force the module's name in the backend.
        if str(BACKEND_FORCED_MODULE_NAME) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-force-module-name'], shell=True)
        BACKEND_FORCED_MODULE_NAME = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--backend-keep-all-brackets'):
        # Keep all brackets.
        if str(BACKEND_KEEP_ALL_BRACKETS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-keep-all-brackets'], shell=True)
        BACKEND_KEEP_ALL_BRACKETS = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-keep-library-funcs'):
        # Keep library functions.
        if str(BACKEND_KEEP_LIBRARY_FUNCS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-keep-library-funcs'], shell=True)
        BACKEND_KEEP_LIBRARY_FUNCS = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-llvmir2bir-converter'):
        # Name of the converter of LLVM IR to BIR.
        if str(BACKEND_LLVMIR2BIR_CONVERTER) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-llvmir2bir-converter'], shell=True)
        BACKEND_LLVMIR2BIR_CONVERTER = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--backend-no-compound-operators'):
        # Do not use compound operators.
        if str(BACKEND_NO_COMPOUND_OPERATORS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-compound-operators'], shell=True)
        BACKEND_NO_COMPOUND_OPERATORS = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-no-debug'):
        # Emission of debug messages.
        if str(BACKEND_NO_DEBUG) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-debug'], shell=True)
        BACKEND_NO_DEBUG = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-no-debug-comments'):
        # Emission of debug comments.
        if str(BACKEND_NO_DEBUG_COMMENTS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-debug-comments'], shell=True)
        BACKEND_NO_DEBUG_COMMENTS = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-no-opts'):
        # Disable backend optimizations.
        if str(BACKEND_OPTS_DISABLED) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-opts'], shell=True)
        BACKEND_OPTS_DISABLED = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-no-symbolic-names'):
        # Disable the conversion of constant arguments.
        if str(BACKEND_NO_SYMBOLIC_NAMES) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-symbolic-names'], shell=True)
        BACKEND_NO_SYMBOLIC_NAMES = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-no-time-varying-info'):
        # Do not emit any time-varying information.
        if str(BACKEND_NO_TIME_VARYING_INFO) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-time-varying-info'], shell=True)
        BACKEND_NO_TIME_VARYING_INFO = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-no-var-renaming'):
        # Disable renaming of variables in the backend.
        if str(BACKEND_VAR_RENAMING_DISABLED) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-no-var-renaming'], shell=True)
        BACKEND_VAR_RENAMING_DISABLED = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-semantics'):
        # The used semantics in the backend.
        if str(BACKEND_SEMANTICS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-semantics'], shell=True)
        BACKEND_SEMANTICS = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--backend-strict-fpu-semantics'):
        # Use strict FPU semantics in the backend.
        if str(BACKEND_STRICT_FPU_SEMANTICS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-strict-fpu-semantics'], shell=True)
        BACKEND_STRICT_FPU_SEMANTICS = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--backend-var-renamer'):
        # Used renamer of variable names.
        if str(BACKEND_VAR_RENAMER) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --backend-var-renamer'], shell=True)
        if str(sys.argv[
                   2]) != 'address' os.path.exists(str(sys.argv[2])) '!='  '-a' str(sys.argv[2]) != 'readable' os.path.exists(str(sys.argv[2])) '!='  '-a' str(sys.argv[2]) != 'unified':
            subprocess.call(['print_error_and_die',
                             'Unsupported variable renamer '' + str(sys.argv[2]) + ''. Supported renamers: address, hungarian, readable, simple, unified.'],
                            shell=True)
        BACKEND_VAR_RENAMER = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--raw-entry-point'):
        # Entry point address for binary created from raw data.
        if str(RAW_ENTRY_POINT) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --raw-entry-point'], shell=True)
        RAW_ENTRY_POINT = sys.argv[2]
        # RAW_ENTRY_POINT='$(($2))'  # evaluate hex address - probably not needed
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--raw-section-vma'):
        # Virtual memory address for section created from raw data.
        if str(RAW_SECTION_VMA) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --raw-section-vma'], shell=True)
        RAW_SECTION_VMA = sys.argv[2]
        # RAW_SECTION_VMA='$(($2))'  # evaluate hex address - probably not needed
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--cleanup'):
        # Cleanup.
        if str(CLEANUP) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --cleanup'], shell=True)
        CLEANUP = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--color-for-ida'):
        if str(COLOR_IDA) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --color-for-ida'], shell=True)
        COLOR_IDA = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--config'):
        if str(CONFIG_DB) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --config'], shell=True)
        if str(NO_CONFIG) != '':
            subprocess.call(['print_error_and_die', 'Option --config can not be used with option --no-config'],
                            shell=True)
        CONFIG_DB = sys.argv[2]
        if (not os.access(str(CONFIG_DB), R_OK) ):
            subprocess.call(['print_error_and_die',
                             'The input JSON configuration file '' + str(CONFIG_DB) + '' does not exist or is not readable'],
                            shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--no-config'):
        if str(NO_CONFIG) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --no-config'], shell=True)
        if str(CONFIG_DB) != '':
            subprocess.call(['print_error_and_die', 'Option --no-config can not be used with option --config'],
                            shell=True)
        NO_CONFIG = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--graph-format'):
        # Format of graph files.
        if str(GRAPH_FORMAT) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --graph-format'], shell=True)
        if str(sys.argv[2]) != 'pdf' os.path.exists(str(sys.argv[2])) '!='  '-a' str(sys.argv[2]) != 'svg':
            subprocess.call(['print_error_and_die',
                             'Unsupported graph format '' + str(sys.argv[2]) + ''. Supported formats: pdf, png, svg.'],
                            shell=True)
        GRAPH_FORMAT = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--select-decode-only'):
        if str(SELECTED_DECODE_ONLY) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --select-decode-only'], shell=True)
        SELECTED_DECODE_ONLY = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--select-functions'):
        # List of selected functions.
        if str(SELECTED_FUNCTIONS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --select-functions'], shell=True)
        IFS').setValue(',')
        # parser line into array
        KEEP_UNREACHABLE_FUNCS = 1
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--select-ranges'):
        # List of selected ranges.
        if str(SELECTED_RANGES) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --select-ranges'], shell=True)
        SELECTED_RANGES = sys.argv[2]
        IFS').setValue(',')
        # parser line into array
        KEEP_UNREACHABLE_FUNCS = 1
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--stop-after'):
        # Stop decompilation after the given tool.
        if str(STOP_AFTER) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --stop-after'], shell=True)
        STOP_AFTER = sys.argv[2]
        if (not re.search('^(fileinfo|unpacker|bin2llvmir|llvmir2hll)' + '$', str(STOP_AFTER))):
            subprocess.call(['print_error_and_die', 'Unsupported tool '' + str(STOP_AFTER) + '' for --stop-after'],
                            shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--static-code-sigfile'):
        # User provided signature file.
        if not os.path.isfile(str(sys.argv[2])):
            subprocess.call(['print_error_and_die', 'Invalid .yara file '' + str(sys.argv[2]) + '''], shell=True)
        TEMPORARY_SIGNATURES').setValue('(' + str(sys.argv[2]) + ')')
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--static-code-archive'):
        # User provided archive to create signature file from.
        if not os.path.isfile(str(sys.argv[2])):
            subprocess.call(['print_error_and_die', 'Invalid archive file '' + str(sys.argv[2]) + '''], shell=True)
        SIGNATURE_ARCHIVE_PATHS').setValue('(' + str(sys.argv[2]) + ')')
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--no-default-static-signatures'):
        DO_NOT_LOAD_STATIC_SIGNATURES = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--fileinfo-verbose'):
        # Enable --verbose mode in fileinfo.
        if str(FILEINFO_VERBOSE) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --fileinfo-verbose'], shell=True)
        FILEINFO_VERBOSE = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--fileinfo-use-all-external-patterns'):
        if str(FILEINFO_USE_ALL_EXTERNAL_PATTERNS) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --fileinfo-use-all-external-patterns'],
                            shell=True)
        FILEINFO_USE_ALL_EXTERNAL_PATTERNS = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--ar-name'):
        # Archive decompilation by name.
        if str(AR_NAME) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --ar-name'], shell=True)
        AR_NAME = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--ar-index'):
        # Archive decompilation by index.
        if str(AR_INDEX) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --ar-index'], shell=True)
        AR_INDEX = sys.argv[2]
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--max-memory'):
        if str(MAX_MEMORY) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --max-memory'], shell=True)
        if str(NO_MEMORY_LIMIT) != '':
            subprocess.call(['print_error_and_die', 'Clashing options: --max-memory and --no-memory-limit'], shell=True)
        MAX_MEMORY = sys.argv[2]
        if (not re.search(Str(Glob('^[0-9] + ' + '$')), str(MAX_MEMORY))):
            subprocess.call(['print_error_and_die',
                             'Invalid value for --max-memory: ' + str(MAX_MEMORY) + ' (expected a positive integer)'],
                            shell=True)
        subprocess.call(['shift', '2'], shell=True)
    elif (str(sys.argv[1]) == '--no-memory-limit'):
        if str(NO_MEMORY_LIMIT) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --no-memory-limit'], shell=True)
        if str(MAX_MEMORY) != '':
            subprocess.call(['print_error_and_die', 'Clashing options: --max-memory and --no-memory-limit'], shell=True)
        NO_MEMORY_LIMIT = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--generate-log'):
        # Intentionally undocumented option.
        # Used only for internal testing.
        # NOT guaranteed it works everywhere (systems other than our internal test machines).
        if str(GENERATE_LOG) != '':
            subprocess.call(['print_error_and_die', 'Duplicate option: --generate-log'], shell=True)
        GENERATE_LOG = 1
        NO_MEMORY_LIMIT = 1
        subprocess.call(['shift'], shell=True)
    elif (str(sys.argv[1]) == '--'):
        # Input file.
        if (Expand.hash() == 2):
            IN = sys.argv[2]
            if (not os.access(str(IN), R_OK) ):
                subprocess.call(
                    ['print_error_and_die', 'The input file '' + str(IN) + '' does not exist or is not readable'],
                    shell=True)
        elif (Expand.hash() > 2):
            # Invalid options.
            subprocess.call(
                ['print_error_and_die', 'Invalid options: '' + str(sys.argv[2]) + '', '' + str(sys.argv[3]) + '' ...'],
                shell=True)
        break
# Check arguments and set default values for unset options.
check_arguments()

# Initialize variables used by logging.
if str(GENERATE_LOG) != '':
    LOG_DECOMPILATION_START_DATE = os.popen('date  + %s').read().rstrip('\n')
    # Put the tool log file and tmp file into /tmp because it uses tmpfs. This means that
    # the data are stored in RAM instead on the disk, which should provide faster access.
    TMP_DIR = '/tmp/decompiler_log'

    os.makedirs(TMP_DIR, exist_ok=True)

    FILE_MD5 = string_to_md5(OUT)
    TOOL_LOG_FILE = str(TMP_DIR) + '/' + str(FILE_MD5) + '.tool'

# Raw.
if str(MODE) == 'raw':
    # Entry point for THUMB must be odd.
    if if str(ARCH) == 'thumb':
        (RAW_ENTRY_POINT % 2) == 0:
        RAW_ENTRY_POINT = (RAW_ENTRY_POINT + 1)
    KEEP_UNREACHABLE_FUNCS = 1

# Check for archives.
if str(MODE) == 'bin':
    # Check for archives packed in Mach-O Universal Binaries.
    print('##### Checking if file is a Mach-O Universal static library...')
    print('RUN: ' + str(EXTRACT) + ' --list ' + str(IN))

    if utils.is_macho_archive(IN):
        OUT_ARCHIVE = str(OUT) + '.a'
        if str(ARCH) != '':
            print()
            print('##### Restoring static library with architecture family ' + str(ARCH) + '...')
            print('RUN: ' + str(EXTRACT) + ' --family ' + str(ARCH) + ' --out ' + str(OUT_ARCHIVE) + ' ' + str(IN))
            if (
                    not subprocess.call([str(EXTRACT), '--family', str(ARCH), '--out', str(OUT_ARCHIVE), str(IN)],
                                        shell=True)):
                # Architecture not supported
                print('Invalid --arch option \'' + str(ARCH) + '\'. File contains these architecture families:')
                subprocess.call([str(EXTRACT), '--list', str(IN)], shell=True)
                cleanup()
                exit(1)
        else:
            # Pick best architecture
            print()
            print('##### Restoring best static library for decompilation...')
            print('RUN: ' + str(EXTRACT) + ' --best --out ' + str(OUT_ARCHIVE) + ' ' + str(IN))
            subprocess.call([str(EXTRACT), '--best', '--out', str(OUT_ARCHIVE), str(IN)], shell=True)
        IN').setValue(OUT_ARCHIVE)
    print()
    print('##### Checking if file is an archive...')
    print('RUN: ' + str(AR) + ' --arch-magic ' + str(IN))
    if (subprocess.call(['has_archive_signature', str(IN)], shell=True)):
        print('This file is an archive!')

        # Check for thin signature.
        if (subprocess.call(['has_thin_archive_signature', str(IN)], shell=True)):
            cleanup()
            subprocess.call(['print_error_and_die', 'File is a thin archive and cannot be decompiled.'], shell=True)

        # Check if our tools can handle it.
        if (not subprocess.call(['is_valid_archive', str(IN)], shell=True)):
            cleanup()
            subprocess.call(['print_error_and_die', 'The input archive has invalid format.'], shell=True)

        # Get and check number of objects.
        ARCH_OBJECT_COUNT = os.popen('archive_object_count \'' + str(IN) + '\'').read().rstrip('\n')
        if ARCH_OBJECT_COUNT <= 0:
            cleanup()
            subprocess.call(['print_error_and_die', 'The input archive is empty.'], shell=True)

        # Prepare object output path.
        OUT_RESTORED = str(OUT) + '.restored'

        # Pick object by index.
        if str(AR_INDEX) != '':
            print()
            print('##### Restoring object file on index '' + str(AR_INDEX) + '' from archive...')
            print('RUN: ' + str(AR) + ' ' + str(IN) + ' --index ' + str(AR_INDEX) + ' --output ' + str(OUT_RESTORED))

            if not utils.archive_get_by_index(IN, AR_INDEX, OUT_RESTORED):
                cleanup()
                VALID_INDEX = (ARCH_OBJECT_COUNT - 1)

                if int(VALID_INDEX) != 0:
                    subprocess.call(['print_error_and_die', 'File on index \'' + str(
                        AR_INDEX) + '\' was not found in the input archive. Valid indexes are 0-' + str(
                        VALID_INDEX) + '.'], shell=True)
                else:
                    subprocess.call(['print_error_and_die', 'File on index \'' + str(
                        AR_INDEX) + '\' was not found in the input archive. The only valid index is 0.'], shell=True)
            IN').setValue(OUT_RESTORED)
        elif str(AR_NAME) != '':
            print()
            print('##### Restoring object file with name '' + str(AR_NAME) + '' from archive...')
            print('RUN: ' + str(AR) + ' ' + str(IN) + ' --name ' + str(AR_NAME) + ' --output ' + str(OUT_RESTORED))
            if not utils.archive_get_by_name(IN, AR_NAME, OUT_RESTORED):
                cleanup()
                subprocess.call(
                    ['print_error_and_die', 'File named \'' + str(AR_NAME) + '\' was not found in the input archive.'],
                    shell=True)
            IN = OUT_RESTORED
        else:
            # Print list of files.
            print('Please select file to decompile with either ' - -ar - index = n'')
            print('or ' - -ar - name = string' option. Archive contains these files:')

            utils.archive_list_numbered_content(IN)
            cleanup()
            exit(1)
    else:
        if str(AR_NAME) != '':
            subprocess.call(['print_warning', 'Option --ar-name can be used only with archives.'], shell=True)
        if str(AR_INDEX) != '':
            subprocess.call(['print_warning', 'Option --ar-index can be used only with archives.'], shell=True)
        print('Not an archive, going to the next step.')

if str(MODE) == 'bin' or str(MODE) == 'raw':
    # Assignment of other used variables.
    OUT_UNPACKED = str(OUT %. *) + '-unpacked'
    OUT_FRONTEND = str(OUT) + '.frontend'
    OUT_FRONTEND_LL = str(OUT_FRONTEND) + '.ll'
    OUT_FRONTEND_BC = str(OUT_FRONTEND) + '.bc'
    CONFIG = str(OUT) + '.json')

if str(CONFIG) != str(CONFIG_DB):
    subprocess.call(['rm', '-f', str(CONFIG)], shell=True)
if str(CONFIG_DB) != '':
    subprocess.call(['cp', str(CONFIG_DB), str(CONFIG)], shell=True)

# Preprocess existing file or create a new, empty JSON file.
if os.path.isfile(str(CONFIG)):
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--preprocess'], shell=True)
else:
    print('{}', file=file(str(CONFIG), 'wb'))

# Raw data needs architecture, endianess and optionaly sections's vma and entry point to be specified.
if (str(MODE) == 'raw'):
    if not ARCH or ARCH '='  '-o' str(ARCH) == str():
        subprocess.call(['print_error_and_die', 'Option -a|--arch must be used with mode ' + str(MODE)], shell=True)
    if not str(ENDIAN) != '':
        subprocess.call(['print_error_and_die', 'Option -e|--endian must be used with mode ' + str(MODE)], shell=True)
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--format', 'raw'], shell=True)
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--arch', str(ARCH)], shell=True)
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--bit-size', '32'], shell=True)
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--file-class', '32'], shell=True)
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--endian', str(ENDIAN)], shell=True)
    if str(RAW_ENTRY_POINT) != '':
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--entry-point', str(RAW_ENTRY_POINT)], shell=True)
    if str(RAW_SECTION_VMA) != '':
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--section-vma', str(RAW_SECTION_VMA)], shell=True)

##
## Call fileinfo to create an initial config file.
##
FILEINFO_PARAMS = '(-c ' + str(CONFIG) + ' --similarity ' + str(IN) + ' --no-hashes=all)'

if (str(FILEINFO_VERBOSE) != ''):
    FILEINFO_PARAMS = '(-c ' + str(CONFIG) + ' --similarity --verbose ' + str(IN) + ')'
for par in Array(FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES[ @]]):
    FILEINFO_PARAMS = '(--crypto ' + str(par) + ')'

if str(FILEINFO_USE_ALL_EXTERNAL_PATTERNS) != '':
    for par in Array(FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES[ @]]):
        FILEINFO_PARAMS = '(--crypto ' + str(par) + ')'
        if (not str(MAX_MEMORY) == ''):
            FILEINFO_PARAMS = '(--max-memory ' + str(MAX_MEMORY) + ')'
        elif (str(NO_MEMORY_LIMIT) == ''):
        # By default, we want to limit the memory of fileinfo into half of
        # system RAM to prevent potential black screens on Windows (#270).
            FILEINFO_PARAMS = '(--max-memory-half-ram)'

print()
print('##### Gathering file information...')
print('RUN: ' + str(FILEINFO) + ' ' + str(FILEINFO_PARAMS[ @]]))

if (str(GENERATE_LOG) != ''):
    FILEINFO_AND_TIME_OUTPUT = os.popen(str(TIME) + ' \'' + str(FILEINFO) + '\' \''
                                        + str(FILEINFO_PARAMS[ @]]) + '\' 2>&1').read().rstrip('\n')

    FILEINFO_RC = _rc0
    LOG_FILEINFO_RC = os.popen('get_tool_rc \'' + str(FILEINFO_RC) + '\' \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')

    LOG_FILEINFO_RUNTIME = os.popen('get_tool_runtime \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
    LOG_FILEINFO_MEMORY = os.popen('get_tool_memory_usage \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
    LOG_FILEINFO_OUTPUT = os.popen('get_tool_output \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
    print(LOG_FILEINFO_OUTPUT)
else:
subprocess.call([str(FILEINFO), str(FILEINFO_PARAMS[ @]])], shell = True)
FILEINFO_RC').setValue(_rc0)
if (int(FILEINFO_RC) != 0):
    if
str(GENERATE_LOG) != '':
generate_log()
cleanup()
# The error message has been already reported by fileinfo in stderr.
subprocess.call(['print_error_and_die'], shell=True)
check_whether_decompilation_should_be_forcefully_stopped('fileinfo')
##
## Unpacking.
##
UNPACK_PARAMS').setValue('(--extended-exit-codes --output ' + str(OUT_UNPACKED) + ' ' + str(IN) + ')')
if (not str(MAX_MEMORY) == ''):
    UNPACK_PARAMS').setValue('(--max-memory ' + str(MAX_MEMORY) + ')')
elif (str(NO_MEMORY_LIMIT) == ''):
# By default, we want to limit the memory of retdec-unpacker into half
# of system RAM to prevent potential black screens on Windows (#270).
    UNPACK_PARAMS').setValue('(--max-memory-half-ram)')
if (str(GENERATE_LOG) != ''):
    LOG_UNPACKER_OUTPUT').setValue(
        os.popen(str(UNPACK_SH) + ' \'' + str(UNPACK_PARAMS[ @]]) + '\' 2>&1').read().rstrip('\n'))
UNPACKER_RC').setValue(_rc0)
LOG_UNPACKER_RC').setValue(UNPACKER_RC)
else:
subprocess.call([str(UNPACK_SH), str(UNPACK_PARAMS[ @]])], shell = True)
UNPACKER_RC').setValue(_rc0)
check_whether_decompilation_should_be_forcefully_stopped('unpacker')
# RET_UNPACK_OK=0
# RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK=1
# RET_NOTHING_TO_DO=2
# RET_UNPACKER_FAILED_OTHERS_OK=3
# RET_UNPACKER_FAILED=4
if (if not if not int(UNPACKER_RC) == 0:
    int(UNPACKER_RC) == 1:
    int(UNPACKER_RC) == 3 ):
# Successfully unpacked -> re-run fileinfo to obtain fresh information.
IN').setValue(OUT_UNPACKED)
FILEINFO_PARAMS').setValue('(-c ' + str(CONFIG) + ' --similarity ' + str(IN) + ' --no-hashes=all)')
if (str(FILEINFO_VERBOSE) != ''):
    FILEINFO_PARAMS').setValue('(-c ' + str(CONFIG) + ' --similarity --verbose ' + str(IN) + ')')
for par') in Array(FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES[ @]]):
    FILEINFO_PARAMS').setValue('(--crypto ' + str(par) + ')')
if (str(FILEINFO_USE_ALL_EXTERNAL_PATTERNS) != ''):
    for
par') in Array(FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES[ @]]):
FILEINFO_PARAMS').setValue('(--crypto ' + str(par) + ')')
if (not str(MAX_MEMORY) == ''):
    FILEINFO_PARAMS').setValue('(--max-memory ' + str(MAX_MEMORY) + ')')
elif (str(NO_MEMORY_LIMIT) == ''):
# By default, we want to limit the memory of fileinfo into half of
# system RAM to prevent potential black screens on Windows (#270).
    FILEINFO_PARAMS').setValue('(--max-memory-half-ram)')
print()
print('##### Gathering file information after unpacking...')
print('RUN: ' + str(FILEINFO) + ' ' + str(FILEINFO_PARAMS[ @]]))
if (str(GENERATE_LOG) != ''):
    FILEINFO_AND_TIME_OUTPUT').setValue(
        os.popen(str(TIME) + ' \'' + str(FILEINFO) + '\' \'' + str(FILEINFO_PARAMS[ @]]) + '\' 2>&1').read().rstrip(
    '\n'))
FILEINFO_RC').setValue(_rc0)
LOG_FILEINFO_RC').setValue(
    os.popen('get_tool_rc \'' + str(FILEINFO_RC) + '\' \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n'))
FILEINFO_RUNTIME').setValue(
    os.popen('get_tool_runtime \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n'))
LOG_FILEINFO_RUNTIME').setValue((LOG_FILEINFO_RUNTIME + FILEINFO_RUNTIME))
FILEINFO_MEMORY').setValue(
    os.popen('get_tool_memory_usage \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n'))
LOG_FILEINFO_MEMORY').setValue(((LOG_FILEINFO_MEMORY + FILEINFO_MEMORY) // 2))
LOG_FILEINFO_OUTPUT').setValue(
    os.popen('get_tool_output \'' + str(FILEINFO_AND_TIME_OUTPUT) + '\'').read().rstrip('\n'))
print(LOG_FILEINFO_OUTPUT)
else:
subprocess.call([str(FILEINFO), str(FILEINFO_PARAMS[ @]])], shell = True)
FILEINFO_RC').setValue(_rc0)
if (int(FILEINFO_RC) != 0):
    if
str(GENERATE_LOG) != '':
generate_log()
cleanup()
# The error message has been already reported by fileinfo in stderr.
subprocess.call(['print_error_and_die'], shell=True)
print_warning_if_decompiling_bytecode()
# Check whether the architecture was specified.
if str(ARCH) != '':
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--arch', str(ARCH)], shell=True)
else:
# Get full name of the target architecture including comments in parentheses
    ARCH_FULL = os.popen(
        '\'' + str(CONFIGTOOL) + '\' \'' + str(CONFIG) + '\' --read --arch | awk \'{print tolower($0').read().rstrip(
        '\n') + '})')
# Strip comments in parentheses and all trailing whitespace
ARCH = os.popen('echo ' + str(ARCH_FULL % (*) + ' | sed -e '
s / ^ [[: space:]] * // '').read().rstrip('\n')

# Get object file format.
FORMAT = os.popen(
    '\'' + str(CONFIGTOOL) + '\' \'' + str(CONFIG) + '\' --read --format | awk \'{print tolower($1').read().rstrip(
    '\n') + ';})'

# Intel HEX needs architecture to be specified
if str(FORMAT) == 'ihex':
    if
not ARCH or ARCH
'='  '-o'
str(ARCH) == str():
subprocess.call(['print_error_and_die', 'Option -a|--arch must be used with format ' + str(FORMAT)], shell=True)
if not str(ENDIAN) != '':
    subprocess.call(['print_error_and_die', 'Option -e|--endian must be used with format ' + str(FORMAT)], shell=True)
subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--arch', str(ARCH)], shell=True)
subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--bit-size', '32'], shell=True)
subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--file-class', '32'], shell=True)
subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--endian', str(ENDIAN)], shell=True)

# Check whether the correct target architecture was specified.
if (str(ARCH) == 'arm' - o str(ARCH)
'=' != '' ):
    ORDS_DIR = ARM_ORDS_DIR
elif (str(ARCH) == 'x86'):
    ORDS_DIR = X86_ORDS_DIR
elif (str(ARCH) == 'powerpc' - o str(ARCH)
'='  '-o'
str(ARCH) == 'pic32' ):
    pass
else:
# nothing
if str(GENERATE_LOG) != '':
    generate_log()
cleanup()
subprocess.call(['print_error_and_die',
                 'Unsupported target architecture '' + str(ARCH^^) + ''. Supported architectures: Intel x86, ARM, ARM + Thumb, MIPS, PIC32, PowerPC.'],
                shell=True)
# Check file class (e.g. 'ELF32', 'ELF64'). At present, we can only decompile 32-bit files.
# Note: we prefer to report the 'unsupported architecture' error (above) than this 'generic' error.
FILECLASS = os.popen('\'' + str(CONFIGTOOL) + '\' \'' + str(CONFIG) + '\' --read --file-class').read().rstrip('\n')

if (if str(FILECLASS) != '16':
    str(FILECLASS) != '32' ):
if str(GENERATE_LOG) != '':
    generate_log()
cleanup()
subprocess.call(['print_error_and_die',
                 'Unsupported target format '' + str(FORMAT^^) + str(FILECLASS) + ''. Supported formats: ELF32, PE32, Intel HEX 32, Mach-O 32.'],
                shell=True)
# Set path to statically linked code signatures.
#
# TODO: Useing ELF for IHEX is ok, but for raw, we probably should somehow decide between ELF and PE, or use both, for RAW.
SIG_FORMAT = FORMAT

if (if not str(SIG_FORMAT) == 'ihex':
    str(SIG_FORMAT) == 'raw' ):
    SIG_FORMAT = 'elf'

ENDIAN = os.popen('\'' + str(CONFIGTOOL) + '\' \'' + str(CONFIG) + '\' --read --endian').read().rstrip('\n')

if (str(ENDIAN) == 'little'):
    SIG_ENDIAN = 'le'
elif (str(ENDIAN) == 'big'):
    SIG_ENDIAN = 'be'
else:
    SIG_ENDIAN = ''

SIG_ARCH = ARCH

if str(SIG_ARCH) == 'pic32':
    SIG_ARCH = 'mips'

SIGNATURES_DIR = str(GENERIC_SIGNATURES_DIR) + '/' + str(SIG_FORMAT) + '/' + str(FILECLASS,, ) + '/' + str(SIG_ENDIAN,,) + '/' + str(
    SIG_ARCH)

print_warning_if_decompiling_bytecode()

# Decompile unreachable functions.
if KEEP_UNREACHABLE_FUNCS:
    subprocess.call([CONFIGTOOL, CONFIG, '--write', '--keep-unreachable-funcs', 'true'], shell=True)

# Get signatures from selected archives.
if (Expand.hash()SIGNATURE_ARCHIVE_PATHS[@] != 0):
    print()

print('##### Extracting signatures from selected archives...')

l = 0

while (l < Expand.hash()SIGNATURE_ARCHIVE_PATHS[@]):
    LIB = SIGNATURE_ARCHIVE_PATHS[l]]
    print('Extracting signatures from file '' + str(LIB) + ''')
    CROP_ARCH_PATH = os.popen('basename \'' + str(LIB) + '\' | LC_ALL=C sed -e \'s/[^A-Za-z0-9_.-]/_/g\'').read().rstrip('\n')
    SIG_OUT = str(OUT) + '.' + str(CROP_ARCH_PATH) + '.' + str(l) + '.yara'

    if (subprocess.call(str(SIG_FROM_LIB_SH) + ' ' + str(LIB) + ' ' + '--output' + ' ' + str(SIG_OUT), shell=True,
                        stderr=subprocess.STDOUT, stdout=file(str(DEV_NULL), 'wb'))):
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--user-signature', str(SIG_OUT)], shell=True)
        SIGNATURES_TO_REMOVE = '(' + str(SIG_OUT) + ')'
    else:
        subprocess.call(['print_warning', 'Failed extracting signatures from file \'' + str(LIB) + '\''], shell=True)

    l += 1

    # Store paths of signature files into config for frontend.
    if not DO_NOT_LOAD_STATIC_SIGNATURES:
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--signatures', str(SIGNATURES_DIR)], shell=True)
    # User provided signatures.

    for i in Array(TEMPORARY_SIGNATURES[ @]]):
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--user-signature', str(i)], shell=True)

    # Store paths of type files into config for frontend.
    if os.path.isdir(str(GENERIC_TYPES_DIR)):
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--types', str(GENERIC_TYPES_DIR)], shell=True)

    # Store path of directory with ORD files into config for frontend (note: only directory, not files themselves).
    if os.path.isdir(str(ORDS_DIR)):
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--ords', str(ORDS_DIR) + '/'], shell=True)

    # Store paths to file with PDB debugging information into config for frontend.
    if os.path.exists(str(PDB_FILE)):
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--pdb-file', str(PDB_FILE)], shell=True)

    # Store file names of input and output into config for frontend.
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--input-file', str(IN)], shell=True)
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--frontend-output-file', str(OUT_FRONTEND_LL)],
                    shell=True)
    subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--output-file', str(OUT)], shell=True)
    # Store decode only selected parts flag.
    if SELECTED_DECODE_ONLY:
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--decode-only-selected', 'true'], shell=True)
    else:
        subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--decode-only-selected', 'false'], shell=True)

    # Store selected functions or selected ranges into config for frontend.
    if SELECTED_FUNCTIONS:
        for f in Array(SELECTED_FUNCTIONS[ @]]):
            subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--selected-func', str(f)], shell=True)

    if SELECTED_RANGES:
        for r in Array(SELECTED_RANGES[ @]]):
            subprocess.call([str(CONFIGTOOL), str(CONFIG), '--write', '--selected-range', str(r)], shell=True)

    # Assignment of other used variables.
    # We have to ensure that the .bc version of the decompiled .ll file is placed
    # in the same directory as are other output files. Otherwise, there may be
    # race-condition problems when the same input .ll file is decompiled in
    # parallel processes because they would overwrite each other's .bc file. This
    # is most likely to happen in regression tests in the 'll' mode.
    OUT_BACKEND = str(OUT) + '.backend'
    # If the input file is the same as $OUT_BACKEND_LL below, then we have to change the name of
    # $OUT_BACKEND. Otherwise, the input file would get overwritten during the conversion.
    if OUT_FRONTEND_LL == OUT_BACKEND + '.ll':
        OUT_BACKENDstr(OUT) + '.backend.backend'

    OUT_BACKEND_BC = str(OUT_BACKEND) + '.bc'
    OUT_BACKEND_LL = str(OUT_BACKEND) + '.ll'
    ##
    ## Decompile the binary into LLVM IR.
    ##
    if KEEP_UNREACHABLE_FUNCS:
        # Prevent bin2llvmir from removing unreachable functions.
        BIN2LLVMIR_PARAMS = os.popen('sed ' s / -unreachable - funcs * // g' <<< \'' + str(BIN2LLVMIR_PARAMS) + '\'').read().rstrip('\n')

    if (if str(CONFIG) == str():
        str(CONFIG_DB) != str() ):
        CONFIG = CONFIG_DB
        BIN2LLVMIR_PARAMS = '(-provider-init -config-path ' + str(CONFIG) + ' -decoder ' + str(BIN2LLVMIR_PARAMS) + ')'

    if (not str(MAX_MEMORY) == ''):
        BIN2LLVMIR_PARAMS = '(-max-memory ' + str(MAX_MEMORY) + ')'
    elif (str(NO_MEMORY_LIMIT) == ''):
        # By default, we want to limit the memory of bin2llvmir into half of
        # system RAM to prevent potential black screens on Windows (#270).
        BIN2LLVMIR_PARAMS = '(-max-memory-half-ram)'
    print()
    print('##### Decompiling ' + str(IN) + ' into ' + str(OUT_BACKEND_BC) + '...')
    print('RUN: ' + str(BIN2LLVMIR) + ' ' + str(BIN2LLVMIR_PARAMS[ @]]) + ' -o ' + str(OUT_BACKEND_BC))
    if (str(GENERATE_LOG) != ''):


    def thread1():
        subprocess.call(
            str(TIME) + ' ' + str(BIN2LLVMIR) + ' ' + str(BIN2LLVMIR_PARAMS[ @]])  +  ' ' + '-o' + ' ' + str(
            OUT_BACKEND_BC), shell = True, stdout = file(str(TOOL_LOG_FILE), 'wb'), stderr = subprocess.STDOUT)

        threading.Thread(target=thread1).start()

        PID = Expand.exclamation()

        def thread2():
            timed_kill(PID)

threading.Thread(target=thread2).start()

subprocess.call('wait' + ' ' + str(PID), shell=True, stderr=subprocess.STDOUT, stdout=file(str(DEV_NULL), 'wb'))

BIN2LLVMIR_RC = _rc2
BIN2LLVMIR_AND_TIME_OUTPUT = os.popen('cat \'' + str(TOOL_LOG_FILE) + '\'').read().rstrip('\n')
LOG_BIN2LLVMIR_RC = os.popen('get_tool_rc \'' + str(BIN2LLVMIR_RC) + '\' \'' + str(BIN2LLVMIR_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
LOG_BIN2LLVMIR_RUNTIME = os.popen('get_tool_runtime \'' + str(BIN2LLVMIR_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
LOG_BIN2LLVMIR_MEMORY = os.popen('get_tool_memory_usage \'' + str(BIN2LLVMIR_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
LOG_BIN2LLVMIR_OUTPUT = os.popen('get_tool_output \'' + str(BIN2LLVMIR_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
print(LOG_BIN2LLVMIR_OUTPUT, end='')
else:
subprocess.call([str(BIN2LLVMIR), str(BIN2LLVMIR_PARAMS[ @]]), '-o', str(OUT_BACKEND_BC)], shell = True)
BIN2LLVMIR_RC').setValue(_rc2)
if (int(BIN2LLVMIR_RC) != 0):
    if
str(GENERATE_LOG) != '':
generate_log()
cleanup()
subprocess.call(['print_error_and_die', 'Decompilation to LLVM IR failed'], shell=True)
check_whether_decompilation_should_be_forcefully_stopped('bin2llvmir')
# modes 'bin' || 'raw'
# LL mode goes straight to backend.
if str(MODE) == 'll':
    OUT_BACKEND_BC = IN

CONFIG = CONFIG_DB
# Conditional initialization.
BACKEND_VAR_RENAMER = Expand.colonEq('BACKEND_VAR_RENAMER', 'readable')
BACKEND_CALL_INFO_OBTAINER = Expand.colonEq('BACKEND_CALL_INFO_OBTAINER', 'optim')
BACKEND_ARITHM_EXPR_EVALUATOR = Expand.colonEq('BACKEND_ARITHM_EXPR_EVALUATOR', 'c')
BACKEND_LLVMIR2BIR_CONVERTER = Expand.colonEq('BACKEND_LLVMIR2BIR_CONVERTER', 'orig')
# Create parameters for the $LLVMIR2HLL call.
LLVMIR2HLL_PARAMS = '(-target-hll=' + str(HLL) + ' -var-renamer=' + str(
    BACKEND_VAR_RENAMER) + ' -var-name-gen=fruit -var-name-gen-prefix= -call-info-obtainer=' + str(
    BACKEND_CALL_INFO_OBTAINER) + ' -arithm-expr-evaluator=' + str(
    BACKEND_ARITHM_EXPR_EVALUATOR) + ' -validate-module -llvmir2bir-converter=' + str(
    BACKEND_LLVMIR2BIR_CONVERTER) + ' -o ' + str(OUT) + ' ' + str(OUT_BACKEND_BC) + ')'

if BACKEND_NO_DEBUG:
    LLVMIR2HLL_PARAMS = '(-enable-debug)'

if BACKEND_NO_DEBUG_COMMENTS:
    LLVMIR2HLL_PARAMS = '(-emit-debug-comments)'

if CONFIG:
    LLVMIR2HLL_PARAMS = '(-config-path=' + str(CONFIG) + ')'

if KEEP_UNREACHABLE_FUNCS:
    LLVMIR2HLL_PARAMS = '(-keep-unreachable-funcs)'

if BACKEND_SEMANTICS:
    LLVMIR2HLL_PARAMS = '(-semantics ' + str(BACKEND_SEMANTICS) + ')'

if BACKEND_ENABLED_OPTS:
    LLVMIR2HLL_PARAMS = '(-enabled-opts=' + str(BACKEND_ENABLED_OPTS) + ')'

if BACKEND_DISABLED_OPTS:
    LLVMIR2HLL_PARAMS = '(-disabled-opts=' + str(BACKEND_DISABLED_OPTS) + ')'

if BACKEND_OPTS_DISABLED:
    LLVMIR2HLL_PARAMS = '(-no-opts)'

if BACKEND_AGGRESSIVE_OPTS:
    LLVMIR2HLL_PARAMS = '(-aggressive-opts)'

if BACKEND_VAR_RENAMING_DISABLED:
    LLVMIR2HLL_PARAMS = '(-no-var-renaming)'

if BACKEND_NO_SYMBOLIC_NAMES:
    LLVMIR2HLL_PARAMS = '(-no-symbolic-names)'

if BACKEND_KEEP_ALL_BRACKETS:
    LLVMIR2HLL_PARAMS = ('(-keep-all-brackets)'

if BACKEND_KEEP_LIBRARY_FUNCS:
    LLVMIR2HLL_PARAMS = '(-keep-library-funcs)'

if BACKEND_NO_TIME_VARYING_INFO:
    LLVMIR2HLL_PARAMS = '(-no-time-varying-info)'

if BACKEND_NO_COMPOUND_OPERATORS:
    LLVMIR2HLL_PARAMS = '(-no-compound-operators)'

if BACKEND_FIND_PATTERNS:
    LLVMIR2HLL_PARAMS = '(-find-patterns ' + str(BACKEND_FIND_PATTERNS) + ')'

if BACKEND_EMIT_CG:
    LLVMIR2HLL_PARAMS = '(-emit-cg)'

if BACKEND_FORCED_MODULE_NAME:
    LLVMIR2HLL_PARAMS = '(-force-module-name=' + str(BACKEND_FORCED_MODULE_NAME) + ')'

if BACKEND_STRICT_FPU_SEMANTICS:
    LLVMIR2HLL_PARAMS = '(-strict-fpu-semantics)'

if BACKEND_EMIT_CFG):
    LLVMIR2HLL_PARAMS = '(-emit-cfgs)'

if BACKEND_CFG_TEST:
    LLVMIR2HLL_PARAMS = '(--backend-cfg-test)'

if (not str(MAX_MEMORY) == ''):
    LLVMIR2HLL_PARAMS = '(-max-memory ' + str(MAX_MEMORY) + ')'

elif (str(NO_MEMORY_LIMIT) == ''):
# By default, we want to limit the memory of llvmir2hll into half of system
# RAM to prevent potential black screens on Windows (#270).
    LLVMIR2HLL_PARAMS = '(-max-memory-half-ram)'
# Decompile the optimized IR code.
print()
print('##### Decompiling ' + str(OUT_BACKEND_BC) + ' into ' + str(OUT) + '...')
print('RUN: ' + str(LLVMIR2HLL) + ' ' + str(LLVMIR2HLL_PARAMS[ @]]))
if (str(GENERATE_LOG) != ''):


def thread3():
    subprocess.call(
        str(TIME) + ' ' + str(LLVMIR2HLL) + ' ' + str(LLVMIR2HLL_PARAMS[ @]]), shell = True, stdout = file(
        str(TOOL_LOG_FILE), 'wb'), stderr = subprocess.STDOUT)

    threading.Thread(target=thread3).start()

    PID = Expand.exclamation()

    def thread4():
        timed_kill(PID)


threading.Thread(target=thread4).start()

subprocess.call('wait' + ' ' + str(PID), shell=True, stderr=subprocess.STDOUT, stdout=file(str(DEV_NULL), 'wb'))

LLVMIR2HLL_RC = _rc4
LLVMIR2HLL_AND_TIME_OUTPUT = os.popen('cat \'' + str(TOOL_LOG_FILE) + '\'').read().rstrip('\n')
LOG_LLVMIR2HLL_RC = os.popen('get_tool_rc \'' + str(LLVMIR2HLL_RC) + '\' \'' + str(LLVMIR2HLL_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
LOG_LLVMIR2HLL_RUNTIME = os.popen('get_tool_runtime \'' + str(LLVMIR2HLL_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
LOG_LLVMIR2HLL_MEMORY = os.popen('get_tool_memory_usage \'' + str(LLVMIR2HLL_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')
LOG_LLVMIR2HLL_OUTPUT = os.popen('get_tool_output \'' + str(LLVMIR2HLL_AND_TIME_OUTPUT) + '\'').read().rstrip('\n')

print(LOG_LLVMIR2HLL_OUTPUT)
# Wait a bit to ensure that all the memory that has been assigned to the tool was released.
subprocess.call(['sleep', '0.1'], shell=True)
else:
subprocess.call([str(LLVMIR2HLL), str(LLVMIR2HLL_PARAMS[ @]])], shell = True)
LLVMIR2HLL_RC').setValue(_rc4)
if (int(LLVMIR2HLL_RC) != 0):
    if
str(GENERATE_LOG) != '':
generate_log()
cleanup()
subprocess.call(['print_error_and_die', 'Decompilation of file '' + str(OUT_BACKEND_BC) + '' failed'], shell=True)
check_whether_decompilation_should_be_forcefully_stopped('llvmir2hll')
# Conditional initialization.
GRAPH_FORMAT = Expand.colonEq('GRAPH_FORMAT', 'png')
BACKEND_CG_CONVERSION = Expand.colonEq('BACKEND_CG_CONVERSION', 'auto')
BACKEND_CFG_CONVERSION = Expand.colonEq('BACKEND_CFG_CONVERSION', 'auto')

# Convert .dot graphs to desired format.
if ((str(BACKEND_EMIT_CG) != '' and str(BACKEND_CG_CONVERSION) == 'auto') or (
        str(BACKEND_EMIT_CFG) != '' and str(BACKEND_CFG_CONVERSION) == 'auto')):
    print()

print('##### Converting .dot files to the desired format...')

if (if str(BACKEND_EMIT_CG) != '':
    str(BACKEND_CG_CONVERSION) == 'auto' ):
    print('RUN: dot -T' + str(GRAPH_FORMAT) + ' ' + str(OUT) + '.cg.dot > ' + str(OUT) + '.cg.' + str(GRAPH_FORMAT))
    subprocess.call('dot' + ' ' + '-T' + str(GRAPH_FORMAT) + ' ' + str(OUT) + '.cg.dot', shell=True,
    stdout = file(str(OUT) + '.cg.' + str(GRAPH_FORMAT), 'wb'))

    if (if str(BACKEND_EMIT_CFG) != '':
str(BACKEND_CFG_CONVERSION) == 'auto' ):
for cfg in Glob(str(OUT) + '.cfg.*.dot'):
    print('RUN: dot -T' + str(GRAPH_FORMAT) + ' ' + str(cfg) + ' > ' + str(cfg %. *) + '.' + str(GRAPH_FORMAT))
subprocess.call('dot' + ' ' + '-T' + str(GRAPH_FORMAT) + ' ' + str(cfg), shell=True,
stdout = file(str(cfg %. *) + '.' + str(GRAPH_FORMAT), 'wb'))

# Remove trailing whitespace and the last redundant empty new line from the
# generated output (if any). It is difficult to do this in the back-end, so we
# do it here.
# Note: Do not use the -i flag (in-place replace) as there is apparently no way
#       of getting sed -i to work consistently on both MacOS and Linux.
_rc4 = subprocess.call(
'sed' + ' ' + '-e' + ' ' + ':a' + ' ' + '-e' + ' ' + '/^\\n*$/{$d;N;};/\\n$/ba' + ' ' + '-e' + ' ' + 's/[[:space:]]*$//',
shell = True, stdin = file(str(OUT), 'rb'), stdout = file(str(OUT) + '.tmp', 'wb'))

_rc4 = subprocess.call(['mv', str(OUT) + '.tmp', str(OUT)], shell=True)

# Colorize output file.
if str(COLOR_IDA) != '':
    subprocess.call([str(IDA_COLORIZER), str(OUT), str(CONFIG)], shell=True)

# Store the information about the decompilation into the JSON file.
if GENERATE_LOG:
    generate_log()

# Success!
cleanup()
print()
print('##### Done!')
