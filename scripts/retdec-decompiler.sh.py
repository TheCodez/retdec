#! /usr/bin/env python
from __future__ import print_function
import sys,os,subprocess,threading,glob,re
class Bash2PyException(Exception):
  def __init__(self, value=None):
    self.value = value
  def __str__(self):
    return repr(self.value)

class Bash2Py(object):
  __slots__ = ["val"]
  def __init__(self, value=''):
    self.val = value
  def setValue(self, value=None):
    self.val = value
    return value
  def postinc(self,inc=1):
    tmp = self.val
    self.val += inc
    return tmp

def GetVariable(name, local=locals()):
  if name in local:
    return local[name]
  if name in globals():
    return globals()[name]
  return None

def Make(name, local=locals()):
  ret = GetVariable(name, local)
  if ret is None:
    ret = Bash2Py(0)
    globals()[name] = ret
  return ret

def GetValue(name, local=locals()):
  variable = GetVariable(name,local)
  if variable is None or variable.val is None:
    return ''
  return variable.val

def SetValue(name, value, local=locals()):
  variable = GetVariable(name,local)
  if variable is None:
    globals()[name] = Bash2Py(value)
  else:
    variable.val = value
  return value

def Str(value):
  if isinstance(value, list):
    return " ".join(value)
  if isinstance(value, basestring):
    return value
  return str(value)

def Array(value):
  if isinstance(value, list):
    return value
  if isinstance(value, basestring):
    return value.strip().split(' ')
  return [ value ]

def Glob(value):
  ret = glob.glob(value)
  if (len(ret) < 1):
    ret = [ value ]
  return ret

class Expand(object):
  @staticmethod
  def at():
    if (len(sys.argv) < 2):
      return []
    return  sys.argv[1:]
  @staticmethod
  def hash():
    return  len(sys.argv)-1
  @staticmethod
  def exclamation():
    raise Bash2PyException("$! unsupported")
  @staticmethod
  def underbar():
    raise Bash2PyException("$_ unsupported")
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

#
# The script decompiles the given file into the selected target high-level language.
#
# On macOS, we want the GNU version of 'readlink', which is available under
# 'greadlink':
def gnureadlink () :
    if (subprocess.call("hash" + " " + "greadlink",shell=True,stderr=file("/dev/null",'wb')) ):
        subprocess.call(["greadlink",Str(Expand.at())],shell=True)
    else:
        subprocess.call(["readlink",Str(Expand.at())],shell=True)

SCRIPT_DIR=Bash2Py(os.popen("dirname \""+os.popen("gnureadlink -e \""+__file__+"\"").read().rstrip("\n")+"\"").read().rstrip("\n"))
if (str(DECOMPILER_UTILS.val) == '' ):
    Make("DECOMPILER_UTILS").setValue(str(SCRIPT_DIR.val)+"/retdec-utils.sh")
_rc0 = subprocess.call([".",str(DECOMPILER_UTILS.val)],shell=True)
#
# Print help.
#
def print_help () :
    print("Decompiles the given file into the selected target high-level language.")
    print()
    print("Usage:")
    print("    "+__file__+" [ options ] file")
    print()
    print("Options:")
    print("    -a name,   --arch name                            Specify target architecture [mips|pic32|arm|thumb|powerpc|x86] (default: autodetected).")
    print("                                                      Required if it cannot be autodetected from the input (e.g. raw mode, Intel HEX).")
    print("    -e name,   --endian name                          Specify target endianness [little|big] (default: autodetected).")
    print("                                                      Required if it cannot be autodetected from the input (e.g. raw mode, Intel HEX).")
    print("    -h,        --help                                 Print this help message.")
    print("    -k         --keep-unreachable-funcs               Keep functions that are unreachable from the main function.")
    print("    -l string, --target-language string               Target high-level language [c|py] (default: c).")
    print("    -m name,   --mode name                            Force the type of decompilation mode [bin|ll|raw] (default: ll if input's suffix is '.ll', bin otherwise).")
    print("    -o file,   --output file                          Output file (default: file.ext).")
    print("    -p file,   --pdb file                             File with PDB debug information.")
    print("               --ar-index name                        Pick file from archive for decompilation by its zero-based index.")
    print("               --ar-name string                       Pick file from archive for decompilation by its name.")
    print("               --backend-aggressive-opts              Enables aggressive optimizations.")
    print("               --backend-arithm-expr-evaluator string Name of the used evaluator of arithmetical expressions (default: c).")
    print("               --backend-call-info-obtainer string    Name of the obtainer of information about function calls (default: optim).")
    print("               --backend-cfg-test                     Unifies the labels of all nodes in the emitted CFG (this has to be used in tests).")
    print("               --backend-disabled-opts list           Prevents the optimizations from the given comma-separated list of optimizations to be run.")
    print("               --backend-emit-cfg                     Emits a CFG for each function in the backend IR (in the .dot format).")
    print("               --backend-emit-cg                      Emits a CG for the decompiled module in the backend IR (in the .dot format).")
    print("               --backend-cg-conversion string         Should the CG from the backend be converted automatically into the desired format? [auto|manual] (default: auto).")
    print("               --backend-cfg-conversion string        Should CFGs from the backend be converted automatically into the desired format? [auto|manual] (default: auto).")
    print("               --backend-enabled-opts list            Runs only the optimizations from the given comma-separated list of optimizations.")
    print("               --backend-find-patterns list           Runs the finders of patterns specified in the given comma-separated list (use 'all' to run them all).")
    print("               --backend-force-module-name string     Overwrites the module name that was detected/generated by the front-end.")
    print("               --backend-keep-all-brackets            Keeps all brackets in the generated code.")
    print("               --backend-keep-library-funcs           Keep functions from standard libraries.")
    print("               --backend-llvmir2bir-converter string  Name of the converter from LLVM IR to BIR (default: orig).")
    print("               --backend-no-compound-operators        Do not emit compound operators (like +=) instead of assignments.")
    print("               --backend-no-debug                     Disables the emission of debug messages, such as phases.")
    print("               --backend-no-debug-comments            Disables the emission of debug comments in the generated code.")
    print("               --backend-no-opts                      Disables backend optimizations.")
    print("               --backend-no-symbolic-names            Disables the conversion of constant arguments to their symbolic names.")
    print("               --backend-no-time-varying-info         Do not emit time-varying information, like dates.")
    print("               --backend-no-var-renaming              Disables renaming of variables in the backend.")
    print("               --backend-semantics                    A comma-separated list of the used semantics.")
    print("               --backend-strict-fpu-semantics         Forces strict FPU semantics to be used.")
    print("               --backend-var-renamer string           Used renamer of variables [address|hungarian|readable|simple|unified] (default: readable).")
    print("               --cleanup                              Removes temporary files created during the decompilation.")
    print("               --color-for-ida                        Put IDA Pro color tags to output C file.")
    print("               --config name                          Specify JSON decompilation configuration file.")
    print("               --no-config                            State explicitly that config file is not to be used.")
    print("               --fileinfo-verbose                     Print all detected information about input file.")
    print("               --fileinfo-use-all-external-patterns   Use all detection rules from external YARA databases.")
    print("               --graph-format name                    Specify format of a all generated graphs (e.g. CG, CFG) [pdf|png|svg] (default: png).")
    print("               --raw-entry-point addr                 Entry point address used for raw binary (default: architecture dependent).")
    print("               --raw-section-vma addr                 Virtual address where section created from the raw binary will be placed (default: architecture dependent).")
    print("               --select-decode-only                   Decode only selected parts (functions/ranges). Faster decompilation, but worse results.")
    print("               --select-functions list                Specify a comma separated list of functions to decompile (example: fnc1,fnc2,fnc3).")
    print("               --select-ranges list                   Specify a comma separated list of ranges to decompile (example: 0x100-0x200,0x300-0x400,0x500-0x600).")
    print("               --stop-after tool                      Stop the decompilation after the given tool (supported tools: fileinfo, unpacker, bin2llvmir, llvmir2hll).")
    print("               --static-code-sigfile path             Adds additional signature file for static code detection.")
    print("               --static-code-archive path             Adds additional signature file for static code detection from given archive.")
    print("               --no-default-static-signatures         No default signatures for statically linked code analysis are loaded (options static-code-sigfile/archive are still available).")
    print("               --max-memory bytes                     Limits the maximal memory of fileinfo, unpacker, bin2llvmir, and llvmir2hll into the given number of bytes.")
    print("               --no-memory-limit                      Disables the default memory limit (half of system RAM) of fileinfo, unpacker, bin2llvmir, and llvmir2hll.")

SCRIPT_NAME=Bash2Py(__file__)
GETOPT_SHORTOPT=Bash2Py("a:e:hkl:m:o:p:")
GETOPT_LONGOPT=Bash2Py("arch:,help,keep-unreachable-funcs,target-language:,mode:,output:,pdb:,backend-aggressive-opts,backend-arithm-expr-evaluator:,backend-call-info-obtainer:,backend-cfg-test,backend-disabled-opts:,backend-emit-cfg,backend-emit-cg,backend-cg-conversion:,backend-cfg-conversion:,backend-enabled-opts:,backend-find-patterns:,backend-force-module-name:,backend-keep-all-brackets,backend-keep-library-funcs,backend-llvmir2bir-converter:,backend-no-compound-operators,backend-no-debug,backend-no-debug-comments,backend-no-opts,backend-no-symbolic-names,backend-no-time-varying-info,backend-no-var-renaming,backend-semantics,backend-strict-fpu-semantics,backend-var-renamer:,cleanup,graph-format:,raw-entry-point:,raw-section-vma:,endian:,select-decode-only,select-functions:,select-ranges:,fileinfo-verbose,fileinfo-use-all-external-patterns,generate-log,config:,color-for-ida,no-config,stop-after:,static-code-sigfile:,static-code-archive:,no-default-static-signatures,ar-name:,ar-index:,max-memory:,no-memory-limit")
#
# Check proper combination of input arguments.
#
def check_arguments () :
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
    if (str(IN.val) == '' ):
        subprocess.call(["print_error_and_die","No input file was specified"],shell=True)
    # Try to detect desired decompilation mode if not set by user.
    # We cannot detect "raw" mode because it overlaps with "bin" (at least not based on extension).
    if (str(MODE.val) == '' ):
        if (str(IN.val: -3) == ".ll" ):
            # Suffix .ll
            Make("MODE").setValue("ll")
        else:
            Make("MODE").setValue("bin")
    # Print warning message about unsupported combinations of options.
    if (str(MODE.val) == "ll" ):
        if str(ARCH.val) != '':
            subprocess.call(["print_warning","Option -a|--arch is not used in mode "+str(MODE.val)],shell=True)
        if str(PDB_FILE.val) != '':
            subprocess.call(["print_warning","Option -p|--pdb is not used in mode "+str(MODE.val)],shell=True)
        if if str(CONFIG_DB.val) == str():
            not str(NO_CONFIG.val) != '':
            subprocess.call(["print_error_and_die","Option --config or --no-config must be specified in mode "+str(MODE.val)],shell=True)
    elif (str(MODE.val) == "raw" ):
        # Errors -- missing critical arguments.
        if not str(ARCH.val) != '':
            subprocess.call(["print_error_and_die","Option -a|--arch must be used with mode "+str(MODE.val)],shell=True)
        if not str(ENDIAN.val) != '':
            subprocess.call(["print_error_and_die","Option -e|--endian must be used with mode "+str(MODE.val)],shell=True)
        if not str(RAW_ENTRY_POINT.val) != '':
            subprocess.call(["print_error_and_die","Option --raw-entry-point must be used with mode "+str(MODE.val)],shell=True)
        if not str(RAW_SECTION_VMA.val) != '':
            subprocess.call(["print_error_and_die","Option --raw-section-vma must be used with mode "+str(MODE.val)],shell=True)
        if (not subprocess.call(["is_number",str(RAW_ENTRY_POINT.val)],shell=True) ):
            subprocess.call(["print_error_and_die","Value in option --raw-entry-point must be decimal (e.g. 123) or hexadecimal value (e.g. 0x123)"],shell=True)
        if (not subprocess.call(["is_number",str(RAW_SECTION_VMA.val)],shell=True) ):
            subprocess.call(["print_error_and_die","Value in option --raw-section-vma must be decimal (e.g. 123) or hexadecimal value (e.g. 0x123)"],shell=True)
    # Archive decompilation errors.
    if if str(AR_NAME.val) != '':
        str(AR_INDEX.val) != '':
        subprocess.call(["print_error_and_die","Options --ar-name and --ar-index are mutually exclusive. Pick one."],shell=True)
    if (str(MODE.val) != "bin" ):
        if str(AR_NAME.val) != '':
            subprocess.call(["print_warning","Option --ar-name is not used in mode "+str(MODE.val)],shell=True)
        if str(AR_INDEX.val) != '':
            subprocess.call(["print_warning","Option --ar-index is not used in mode "+str(MODE.val)],shell=True)
    # Conditional initialization.
    HLL=Bash2Py(Expand.colonEq("HLL","c"))
    if (str(OUT.val) == '' ):
        # No output file was given, so use the default one.
        if (str(IN.val##*.) == "ll" ):
            # Suffix .ll
            Make("OUT").setValue(str(IN.val%.ll)+"."+str(HLL.val))
        elif (str(IN.val##*.) == "exe" ):
            # Suffix .exe
            Make("OUT").setValue(str(IN.val%.exe)+"."+str(HLL.val))
        elif (str(IN.val##*.) == "elf" ):
            # Suffix .elf
            Make("OUT").setValue(str(IN.val%.elf)+"."+str(HLL.val))
        elif (str(IN.val##*.) == "ihex" ):
            # Suffix .ihex
            Make("OUT").setValue(str(IN.val%.ihex)+"."+str(HLL.val))
        elif (str(IN.val##*.) == "macho" ):
            # Suffix .macho
            Make("OUT").setValue(str(IN.val%.macho)+"."+str(HLL.val))
        else:
            Make("OUT").setValue(str(IN.val)+str(PICKED_FILE.val)+"."+str(HLL.val))
    # If the output file name matches the input file name, we have to change the
    # output file name. Otherwise, the input file gets overwritten.
    if (str(IN.val) == str(OUT.val) ):
        Make("OUT").setValue(str(IN.val%.*)+".out."+str(HLL.val))
    # Convert to absolute paths.
    IN=Bash2Py(os.popen("get_realpath \""+str(IN.val)+"\"").read().rstrip("\n"))
    OUT=Bash2Py(os.popen("get_realpath \""+str(OUT.val)+"\"").read().rstrip("\n"))
    if (os.path.exists(str(PDB_FILE.val)) ):
        Make("PDB_FILE").setValue(os.popen("get_realpath \""+str(PDB_FILE.val)+"\"").read().rstrip("\n"))
    # Check that selected ranges are valid.
    if (str(SELECTED_RANGES.val) != '' ):
        for Make("r").val in Array(SELECTED_RANGES.val[@] ]):
            # Check if valid range.
            if (not subprocess.call(["is_range",str(r.val)],shell=True) ):
                subprocess.call(["print_error_and_die","Range '"+str(r.val)+"' in option --select-ranges is not a valid decimal (e.g. 123-456) or hexadecimal (e.g. 0x123-0xabc) range."],shell=True)
            # Check if first <= last.
            Make("IFS").setValue("-")
            # parser line into array
            if ((vs[0] ].val > vs[1] ].val) ):
                subprocess.call(["print_error_and_die","Range '"+str(r.val)+"' in option --select-ranges is not a valid range: second address must be greater or equal than the first one."],shell=True)

#
# Prints a warning if we are decompiling bytecode.
#
def print_warning_if_decompiling_bytecode () :
    global BYTECODE
    global CONFIGTOOL
    global CONFIG

    Make("BYTECODE").setValue(os.popen("\""+str(CONFIGTOOL.val)+"\" \""+str(CONFIG.val)+"\" --read --bytecode").read().rstrip("\n"))
    if (str(BYTECODE.val) != str() ):
        subprocess.call(["print_warning","Detected "+str(BYTECODE.val)+" bytecode, which cannot be decompiled by our machine-code decompiler. The decompilation result may be inaccurate."],shell=True)

#
# Checks whether the decompilation should be forcefully stopped because of the
# --stop-after parameter. If so, cleanup is run and the script exits with 0.
#
# Arguments:
#
#   $1 Name of the tool.
#
# The function expects the $STOP_AFTER variable to be set.
#
def check_whether_decompilation_should_be_forcefully_stopped (_p1) :
    global STOP_AFTER
    global GENERATE_LOG

    if (str(STOP_AFTER.val) == str(_p1) ):
        if str(GENERATE_LOG.val) != '':
            subprocess.call(["generate_log"],shell=True)
        subprocess.call(["cleanup"],shell=True)
        print()
        print("#### Forced stop due to '--stop-after "+str(STOP_AFTER.val)+"'...")
        exit(0)

#
# Clean working directory.
#
def cleanup () :
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

    if (str(CLEANUP.val) != '' ):
        subprocess.call(["rm","-f",str(OUT_UNPACKED.val)],shell=True)
        subprocess.call(["rm","-f",str(OUT_FRONTEND_LL.val)],shell=True)
        subprocess.call(["rm","-f",str(OUT_FRONTEND_BC.val)],shell=True)
        if (str(CONFIG.val) != str(CONFIG_DB.val) ):
            subprocess.call(["rm","-f",str(CONFIG.val)],shell=True)
        subprocess.call(["rm","-f",str(OUT_BACKEND_BC.val)],shell=True)
        subprocess.call(["rm","-f",str(OUT_BACKEND_LL.val)],shell=True)
        subprocess.call(["rm","-f",str(OUT_RESTORED.val)],shell=True)
        # Archive support
        subprocess.call(["rm","-f",str(OUT_ARCHIVE.val)],shell=True)
        # Archive support (Macho-O Universal)
        subprocess.call(["rm","-f",str(SIGNATURES_TO_REMOVE.val[@] ])],shell=True)
        # Signatures generated from archives
        if str(TOOL_LOG_FILE.val) != '':
            subprocess.call(["rm","-f",str(TOOL_LOG_FILE.val)],shell=True)

#
# An alternative to the `time` shell builtin that provides more information. It
# is used in decompilation log to get the running time and used memory of a command.
#
TIME=Bash2Py("/usr/bin/time -v")
TIMEOUT=Bash2Py(300)
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
def get_tool_rc (_p1,_p2) :
    global ORIGINAL_RC
    global OUTPUT
    global SIGNAL_REGEX
    global SIGNAL_NUM
    global BASH_REMATCH
    global RC

    Make("ORIGINAL_RC").setValue(_p1)
    OUTPUT=Bash2Py(_p2)
    SIGNAL_REGEX=Bash2Py("Command terminated by signal ([0-9]*)")
    if (re.search(str(SIGNAL_REGEX.val),str(OUTPUT.val)) ):
        Make("SIGNAL_NUM").setValue(BASH_REMATCH.val[1] ])
        Make("RC").setValue((SIGNAL_NUM.val + 128))
    else:
        Make("RC").setValue(ORIGINAL_RC.val)
    # We want to be able to distinguish assertions and memory-insufficiency
    # errors. The problem is that both assertions and memory-insufficiency
    # errors make the program exit with return code 134. We solve this by
    # replacing 134 with 135 (SIBGUS, 7) when there is 'std::bad_alloc' in the
    # output. So, 134 will mean abort (assertion error) and 135 will mean
    # memory-insufficiency error.
    if (str(RC.val) == "134" ):
        if (re.search("std::bad_alloc",str(OUTPUT.val)) ):
            Make("RC").setValue(135)
    print(RC.val)

#
# Parses the given output ($1) from a tool that was run through
# `/usr/bin/time -v` and prints the running time in seconds.
#
def get_tool_runtime (_p1) :
    global USER_TIME_F
    global SYSTEM_TIME_F
    global RUNTIME_F

    # The output from `/usr/bin/time -v` looks like this:
    #
    #    [..] (output from the tool)
    #        Command being timed: "tool"
    #        User time (seconds): 0.04
    #        System time (seconds): 0.00
    #        [..] (other data)
    #
    # We combine the user and system times into a single time in seconds.
    Make("USER_TIME_F").setValue(os.popen("egrep \"User time \\(seconds\\").read().rstrip("\n")+": <<< "+str(_p1)+" | cut -d: -f2)")
    SYSTEM_TIME_F=Bash2Py(os.popen("egrep \"System time \\(seconds\\").read().rstrip("\n")+": <<< "+str(_p1)+" | cut -d: -f2)")
    RUNTIME_F=Bash2Py(os.popen("echo "+str(USER_TIME_F.val)+" + "+str(SYSTEM_TIME_F.val)+" | bc").read().rstrip("\n"))
    # Convert the runtime from float to int (http://unix.stackexchange.com/a/89843).
    # By adding 1, we make sure that the runtime is at least one second. This
    # also takes care of proper rounding (we want to round runtime 1.1 to 2).
    _rc0 = _rcr2, _rcw2 = os.pipe()
    if os.fork():
        os.close(_rcw2)
        os.dup2(_rcr2, 0)
        subprocess.call(["bc"],shell=True)
    else:
        os.close(_rcr2)
        os.dup2(_rcw2, 1)
        print("("+str(RUNTIME_F.val)+" + 1)/1")
        sys.exit(0)
    

#
# Parses the given output ($1) from a tool that was run through
# `/usr/bin/time -v` and prints the memory usage in MB.
#
def get_tool_memory_usage (_p1) :
    global RSS_KB
    global RSS_MB

    # The output from `/usr/bin/time -v` looks like this:
    #
    #    [..] (output from the tool)
    #        Command being timed: "tool"
    #        [..] (other data)
    #        Maximum resident set size (kbytes): 1808
    #        [..] (other data)
    #
    # We want the value of "resident set size" (RSS), which we convert from KB
    # to MB. If the resulting value is less than 1 MB, round it to 1 MB.
    Make("RSS_KB").setValue(os.popen("egrep \"Maximum resident set size \\(kbytes\\").read().rstrip("\n")+": <<< "+str(_p1)+" | cut -d: -f2)")
    RSS_MB=Bash2Py((RSS_KB.val // 1024))
    print((RSS_MB.val if (RSS_MB.val > 0) else 1))

#
# Prints the actual output of a tool that was run through `/usr/bin/time -v`.
# The parameter ($1) is the combined output from the tool and `/usr/bin/time -v`.
#
def get_tool_output (_p1) :
    # The output from `/usr/bin/time -v` looks either like this (success):
    #
    #    [..] (output from the tool)
    #        Command being timed: "tool"
    #        [..] (other data)
    #
    # or like this (when there was an error):
    #
    #    [..] (output from the tool)
    #        Command exited with non-zero status X
    #        [..] (other data)
    #
    # Remove everything after and including "Command..."
    # (http://stackoverflow.com/a/5227429/2580955).
    _rcr1, _rcw1 = os.pipe()
    if os.fork():
        os.close(_rcw1)
        os.dup2(_rcr1, 0)
        subprocess.call(["sed","-n","/Command exited with non-zero status/q;p"],shell=True)
    else:
        os.close(_rcr1)
        os.dup2(_rcw1, 1)
        subprocess.Popen("sed" + " " + "-n" + " " + "/Command being timed:/q;p",shell=True,stdin=subprocess.PIPE)
        _rc0.communicate(str(_p1)+'\n')
        _rc0 = _rc0.wait()
        sys.exit(0)
    

#
# Prints an escaped version of the given text so it can be inserted into JSON.
#
# Parameters:
#   - $1 Text to be escaped.
#
def json_escape (_p1) :
    # We need to escape backslashes (\), double quotes ("), and replace new lines with '\n'.
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
                subprocess.call(["sed","{:q;N;s/\\n/\\\\n/g;t q}"],shell=True)
            else:
                os.close(_rcr3)
                os.dup2(_rcw3, 1)
                subprocess.call(["sed","s/\"/\\\\\"/g"],shell=True)
                sys.exit(0)
            
        else:
            os.close(_rcr2)
            os.dup2(_rcw2, 1)
            subprocess.call(["sed","s/\\\\/\\\\\\\\/g"],shell=True)
            sys.exit(0)
        
    else:
        os.close(_rcr1)
        os.dup2(_rcw1, 1)
        print(_p1)
        sys.exit(0)
    

#
# Removes color codes from the given text ($1).
#
def remove_colors (_p1) :
    subprocess.Popen("sed" + " " + "-r" + " " + "s/\x1b[^m]*m//g",shell=True,stdin=subprocess.PIPE)
    _rc0.communicate(str(_p1)+'\n')
    _rc0 = _rc0.wait()

#
# Platform-independent alternative to `ulimit -t` or `timeout`.
# Based on http://www.bashcookbook.com/bashinfo/source/bash-4.0/examples/scripts/timeout3
# 1 argument is needed - PID
# Returns - 1 if number of arguments is incorrect
#           0 otherwise
#
def timed_kill (_p1) :
    global TIMEOUT
    global timeout
    global DEV_NULL

    if (str(Expand.hash()) != "1" ):
        return(1)
    PID=Bash2Py(_p1)
    # PID of the target process
    PROCESS_NAME=Bash2Py(os.popen("ps -p "+str(PID.val)+" -o comm --no-heading").read().rstrip("\n"))
    if (str(PROCESS_NAME.val) == "time" ):
        # The program is run through `/usr/bin/time`, so get the PID of the
        # child process (the actual program). Otherwise, if we killed
        # `/usr/bin/time`, we would obtain no output from it (user time, memory
        # usage etc.).
        Make("PID").setValue(os.popen("ps --ppid "+str(PID.val)+" -o pid --no-heading | head -n1").read().rstrip("\n"))
    if (str(TIMEOUT.val) == '' ):
        Make("TIMEOUT").setValue(300)
    timeout=Bash2Py(TIMEOUT.val)
    
    Make("t").setValue(timeout.val)
    while ((t.val > 0)):
        subprocess.call(["sleep","1"],shell=True)
        if not subprocess.call("kill" + " " + "-0" + " " + str(PID.val),shell=True,stdout=file(str(DEV_NULL.val),'wb'),stderr=file(str(DEV_NULL.val),'wb'))
        :
            exit(0)
        Make("t").setValue((t.val - 1))
    _rc0 = subprocess.call("kill_tree" + " " + str(PID.val) + " " + "SIGKILL",shell=True,stdout=file(str(DEV_NULL.val),'wb'),stderr=file(str(DEV_NULL.val),'wb'))
    

#
# Kill process and all its children.
# Based on http://stackoverflow.com/questions/392022/best-way-to-kill-all-child-processes/3211182#3211182
# 2 arguments are needed - PID of process to kill + signal type
# Returns - 1 if number of arguments is incorrect
#           0 otherwise
#
def kill_tree (_p1) :

    if (if str(Expand.hash()) != "1":
        str(Expand.hash()) != "2" ):
        return(1)
    _pid=Bash2Py(_p1)
    _sig=Bash2Py(Expand.colonMinus("2","TERM"))
    _rc0 = subprocess.call(["kill","-stop",Expand.underbar()+"pid"],shell=True)
    # needed to stop quickly forking parent from producing child between child killing and parent killing
    for Make("_child").val in Array(os.popen("ps -o pid --no-headers --ppid \""+Expand.underbar()+"pid\"").read().rstrip("\n")):
        kill_tree(Expand.underbar()+"child", Expand.underbar()+"sig")
    _rc0 = subprocess.call(["kill","-"+Expand.underbar()+"sig",Expand.underbar()+"pid"],shell=True)

#
# Generate a MD5 checksum from a given string ($1).
#
def string_to_md5 (_p1) :
    _rcr1, _rcw1 = os.pipe()
    if os.fork():
        os.close(_rcw1)
        os.dup2(_rcr1, 0)
        _rcr2, _rcw2 = os.pipe()
        if os.fork():
            os.close(_rcw2)
            os.dup2(_rcr2, 0)
            subprocess.call(["awk","{print $1}"],shell=True)
        else:
            os.close(_rcr2)
            os.dup2(_rcw2, 1)
            subprocess.call(["md5sum"],shell=True)
            sys.exit(0)
        
    else:
        os.close(_rcr1)
        os.dup2(_rcw1, 1)
        print(_p1,end="")
        sys.exit(0)
    

#
#
#
def generate_log () :
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

    Make("LOG_FILE").setValue(str(OUT.val)+".decompilation.log")
    LOG_DECOMPILATION_END_DATE=Bash2Py(os.popen("date +%s").read().rstrip("\n"))
    LOG_FILEINFO_OUTPUT=Bash2Py(os.popen("json_escape \""+str(LOG_FILEINFO_OUTPUT.val)+"\"").read().rstrip("\n"))
    LOG_UNPACKER_OUTPUT=Bash2Py(os.popen("json_escape \""+str(LOG_UNPACKER_OUTPUT.val)+"\"").read().rstrip("\n"))
    LOG_BIN2LLVMIR_OUTPUT=Bash2Py(os.popen("remove_colors \""+str(LOG_BIN2LLVMIR_OUTPUT.val)+"\"").read().rstrip("\n"))
    LOG_BIN2LLVMIR_OUTPUT=Bash2Py(os.popen("json_escape \""+str(LOG_BIN2LLVMIR_OUTPUT.val)+"\"").read().rstrip("\n"))
    LOG_LLVMIR2HLL_OUTPUT=Bash2Py(os.popen("remove_colors \""+str(LOG_LLVMIR2HLL_OUTPUT.val)+"\"").read().rstrip("\n"))
    LOG_LLVMIR2HLL_OUTPUT=Bash2Py(os.popen("json_escape \""+str(LOG_LLVMIR2HLL_OUTPUT.val)+"\"").read().rstrip("\n"))
    log_structure=Bash2Py("{\n\t\"input_file\" : \"%s\",\n\t\"pdb_file\" : \"%s\",\n\t\"start_date\" : \"%s\",\n\t\"end_date\" : \"%s\",\n\t\"mode\" : \"%s\",\n\t\"arch\" : \"%s\",\n\t\"format\" : \"%s\",\n\t\"fileinfo_rc\" : \"%s\",\n\t\"unpacker_rc\" : \"%s\",\n\t\"bin2llvmir_rc\" : \"%s\",\n\t\"llvmir2hll_rc\" : \"%s\",\n\t\"fileinfo_output\" : \"%s\",\n\t\"unpacker_output\" : \"%s\",\n\t\"bin2llvmir_output\" : \"%s\",\n\t\"llvmir2hll_output\" : \"%s\",\n\t\"fileinfo_runtime\" : \"%s\",\n\t\"bin2llvmir_runtime\" : \"%s\",\n\t\"llvmir2hll_runtime\" : \"%s\",\n\t\"fileinfo_memory\" : \"%s\",\n\t\"bin2llvmir_memory\" : \"%s\",\n\t\"llvmir2hll_memory\" : \"%s\"\n}\n")
    print( str(log_structure.val) % (str(IN.val), str(PDB_FILE.val), str(LOG_DECOMPILATION_START_DATE.val), str(LOG_DECOMPILATION_END_DATE.val), str(MODE.val), str(ARCH.val), str(FORMAT.val), str(LOG_FILEINFO_RC.val), str(LOG_UNPACKER_RC.val), str(LOG_BIN2LLVMIR_RC.val), str(LOG_LLVMIR2HLL_RC.val), str(LOG_FILEINFO_OUTPUT.val), str(LOG_UNPACKER_OUTPUT.val), str(LOG_BIN2LLVMIR_OUTPUT.val), str(LOG_LLVMIR2HLL_OUTPUT.val), str(LOG_FILEINFO_RUNTIME.val), str(LOG_BIN2LLVMIR_RUNTIME.val), str(LOG_LLVMIR2HLL_RUNTIME.val), str(LOG_FILEINFO_MEMORY.val), str(LOG_BIN2LLVMIR_MEMORY.val), str(LOG_LLVMIR2HLL_MEMORY.val)) )
    

# Check script arguments.
PARSED_OPTIONS=Bash2Py(os.popen("getopt -o \""+str(GETOPT_SHORTOPT.val)+"\" -l \""+str(GETOPT_LONGOPT.val)+"\" -n \""+str(SCRIPT_NAME.val)+"\" -- \""+Str(Expand.at())+"\"").read().rstrip("\n"))
# Bad arguments.
if _rc0 != 0:
    subprocess.call(["print_error_and_die","Getopt - parsing parameters fail"],shell=True)
eval("set","--",str(PARSED_OPTIONS.val))
while (True):
    
    if ( str(sys.argv[1]) == '-a' or str(sys.argv[1]) == '--arch'):
        # Target architecture.
        if str(ARCH.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -a|--arch"],shell=True)
        if str(sys.argv[2]) != "mips" os.path.exists(str(sys.argv[2])) "!="  "-a" str(sys.argv[2]) != "arm" os.path.exists(str(sys.argv[2])) "!="  "-a" str(sys.argv[2]) != "powerpc" os.path.exists(str(sys.argv[2]))"!=" != '':
            subprocess.call(["print_error_and_die","Unsupported target architecture '"+str(sys.argv[2])+"'. Supported architectures: Intel x86, ARM, ARM+Thumb, MIPS, PIC32, PowerPC."],shell=True)
        Make("ARCH").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-e' or str(sys.argv[1]) == '--endian'):
        # Endian.
        if str(ENDIAN.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -e|--endian"],shell=True)
        Make("ENDIAN").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help'):
        # Help.
        print_help()
        exit(0)
    elif ( str(sys.argv[1]) == '-k' or str(sys.argv[1]) == '--keep-unreachable-funcs'):
        # Keep unreachable functions.
        # Do not check if this parameter is a duplicate because when both
        # --select-ranges or --select--functions and -k is specified, the
        # decompilation fails.
        Make("KEEP_UNREACHABLE_FUNCS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '-l' or str(sys.argv[1]) == '--target-language'):
        # Target language.
        if str(HLL.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -l|--target-language"],shell=True)
        if str(sys.argv[2]) != "c" os.path.exists(str(sys.argv[2]))"!=" != '':
            subprocess.call(["print_error_and_die","Unsupported target language '"+str(sys.argv[2])+"'. Supported languages: C, Python."],shell=True)
        Make("HLL").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-m' or str(sys.argv[1]) == '--mode'):
        # Decompilation mode.
        if str(MODE.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -m|--mode"],shell=True)
        if str(sys.argv[2]) != "bin" os.path.exists(str(sys.argv[2])) "!="  "-a" str(sys.argv[2]) != "raw":
            subprocess.call(["print_error_and_die","Unsupported decompilation mode '"+str(sys.argv[2])+"'. Supported modes: bin, ll, raw."],shell=True)
        Make("MODE").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-o' or str(sys.argv[1]) == '--output'):
        # Output file.
        if str(OUT.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -o|--output"],shell=True)
        Make("OUT").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-p' or str(sys.argv[1]) == '--pdb'):
        # File containing PDB debug information.
        if str(PDB_FILE.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -p|--pdb"],shell=True)
        Make("PDB_FILE").setValue(sys.argv[2])
        if (not os.access(str(PDB_FILE.val),R_OK) ):
            subprocess.call(["print_error_and_die","The input PDB file '"+str(PDB_FILE.val)+"' does not exist or is not readable"],shell=True)
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-aggressive-opts'):
        # Enable aggressive optimizations.
        if str(BACKEND_AGGRESSIVE_OPTS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-aggressive-opts"],shell=True)
        Make("BACKEND_AGGRESSIVE_OPTS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-arithm-expr-evaluator'):
        # Name of the evaluator of arithmetical expressions.
        if str(BACKEND_ARITHM_EXPR_EVALUATOR.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-arithm-expr-evaluator"],shell=True)
        Make("BACKEND_ARITHM_EXPR_EVALUATOR").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-call-info-obtainer'):
        # Name of the obtainer of information about function calls.
        if str(BACKEND_CALL_INFO_OBTAINER.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-call-info-obtainer"],shell=True)
        Make("BACKEND_CALL_INFO_OBTAINER").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-cfg-test'):
        # Unify the labels in the emitted CFG.
        if str(BACKEND_CFG_TEST.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-cfg-test"],shell=True)
        Make("BACKEND_CFG_TEST").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-disabled-opts'):
        # List of disabled optimizations in the backend.
        if str(BACKEND_DISABLED_OPTS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-disabled-opts"],shell=True)
        Make("BACKEND_DISABLED_OPTS").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-emit-cfg'):
        # Emit a CFG of each function in the backend IR.
        if str(BACKEND_EMIT_CFG.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-emit-cfg"],shell=True)
        Make("BACKEND_EMIT_CFG").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-emit-cg'):
        # Emit a CG of the decompiled module in the backend IR.
        if str(BACKEND_EMIT_CG.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-emit-cg"],shell=True)
        Make("BACKEND_EMIT_CG").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-cg-conversion'):
        # Should the CG from the backend be converted automatically into the desired format?.
        if str(BACKEND_CG_CONVERSION.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-cg-conversion"],shell=True)
        if str(sys.argv[2]) != "auto" os.path.exists(str(sys.argv[2]))"!=" != '':
            subprocess.call(["print_error_and_die","Unsupported CG conversion mode '"+str(sys.argv[2])+"'. Supported modes: auto, manual."],shell=True)
        Make("BACKEND_CG_CONVERSION").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-cfg-conversion'):
        # Should CFGs from the backend be converted automatically into the desired format?.
        if str(BACKEND_CFG_CONVERSION.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-cfg-conversion"],shell=True)
        if str(sys.argv[2]) != "auto" os.path.exists(str(sys.argv[2]))"!=" != '':
            subprocess.call(["print_error_and_die","Unsupported CFG conversion mode '"+str(sys.argv[2])+"'. Supported modes: auto, manual."],shell=True)
        Make("BACKEND_CFG_CONVERSION").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-enabled-opts'):
        # List of enabled optimizations in the backend.
        if str(BACKEND_ENABLED_OPTS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-enabled-opts"],shell=True)
        Make("BACKEND_ENABLED_OPTS").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-find-patterns'):
        # Try to find patterns.
        if str(BACKEND_FIND_PATTERNS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-find-patterns"],shell=True)
        Make("BACKEND_FIND_PATTERNS").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-force-module-name'):
        # Force the module's name in the backend.
        if str(BACKEND_FORCED_MODULE_NAME.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-force-module-name"],shell=True)
        Make("BACKEND_FORCED_MODULE_NAME").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-keep-all-brackets'):
        # Keep all brackets.
        if str(BACKEND_KEEP_ALL_BRACKETS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-keep-all-brackets"],shell=True)
        Make("BACKEND_KEEP_ALL_BRACKETS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-keep-library-funcs'):
        # Keep library functions.
        if str(BACKEND_KEEP_LIBRARY_FUNCS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-keep-library-funcs"],shell=True)
        Make("BACKEND_KEEP_LIBRARY_FUNCS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-llvmir2bir-converter'):
        # Name of the converter of LLVM IR to BIR.
        if str(BACKEND_LLVMIR2BIR_CONVERTER.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-llvmir2bir-converter"],shell=True)
        Make("BACKEND_LLVMIR2BIR_CONVERTER").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-no-compound-operators'):
        # Do not use compound operators.
        if str(BACKEND_NO_COMPOUND_OPERATORS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-no-compound-operators"],shell=True)
        Make("BACKEND_NO_COMPOUND_OPERATORS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-no-debug'):
        # Emission of debug messages.
        if str(BACKEND_NO_DEBUG.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-no-debug"],shell=True)
        Make("BACKEND_NO_DEBUG").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-no-debug-comments'):
        # Emission of debug comments.
        if str(BACKEND_NO_DEBUG_COMMENTS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-no-debug-comments"],shell=True)
        Make("BACKEND_NO_DEBUG_COMMENTS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-no-opts'):
        # Disable backend optimizations.
        if str(BACKEND_OPTS_DISABLED.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-no-opts"],shell=True)
        Make("BACKEND_OPTS_DISABLED").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-no-symbolic-names'):
        # Disable the conversion of constant arguments.
        if str(BACKEND_NO_SYMBOLIC_NAMES.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-no-symbolic-names"],shell=True)
        Make("BACKEND_NO_SYMBOLIC_NAMES").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-no-time-varying-info'):
        # Do not emit any time-varying information.
        if str(BACKEND_NO_TIME_VARYING_INFO.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-no-time-varying-info"],shell=True)
        Make("BACKEND_NO_TIME_VARYING_INFO").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-no-var-renaming'):
        # Disable renaming of variables in the backend.
        if str(BACKEND_VAR_RENAMING_DISABLED.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-no-var-renaming"],shell=True)
        Make("BACKEND_VAR_RENAMING_DISABLED").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-semantics'):
        # The used semantics in the backend.
        if str(BACKEND_SEMANTICS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-semantics"],shell=True)
        Make("BACKEND_SEMANTICS").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-strict-fpu-semantics'):
        # Use strict FPU semantics in the backend.
        if str(BACKEND_STRICT_FPU_SEMANTICS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-strict-fpu-semantics"],shell=True)
        Make("BACKEND_STRICT_FPU_SEMANTICS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--backend-var-renamer'):
        # Used renamer of variable names.
        if str(BACKEND_VAR_RENAMER.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --backend-var-renamer"],shell=True)
        if str(sys.argv[2]) != "address" os.path.exists(str(sys.argv[2])) "!="  "-a" str(sys.argv[2]) != "readable" os.path.exists(str(sys.argv[2])) "!="  "-a" str(sys.argv[2]) != "unified":
            subprocess.call(["print_error_and_die","Unsupported variable renamer '"+str(sys.argv[2])+"'. Supported renamers: address, hungarian, readable, simple, unified."],shell=True)
        Make("BACKEND_VAR_RENAMER").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--raw-entry-point'):
        # Entry point address for binary created from raw data.
        if str(RAW_ENTRY_POINT.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --raw-entry-point"],shell=True)
        Make("RAW_ENTRY_POINT").setValue(sys.argv[2])
        #RAW_ENTRY_POINT="$(($2))"  # evaluate hex address - probably not needed
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--raw-section-vma'):
        # Virtual memory address for section created from raw data.
        if str(RAW_SECTION_VMA.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --raw-section-vma"],shell=True)
        Make("RAW_SECTION_VMA").setValue(sys.argv[2])
        #RAW_SECTION_VMA="$(($2))"  # evaluate hex address - probably not needed
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--cleanup'):
        # Cleanup.
        if str(CLEANUP.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --cleanup"],shell=True)
        Make("CLEANUP").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--color-for-ida'):
        if str(COLOR_IDA.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --color-for-ida"],shell=True)
        Make("COLOR_IDA").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--config'):
        if str(CONFIG_DB.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --config"],shell=True)
        if str(NO_CONFIG.val) != '':
            subprocess.call(["print_error_and_die","Option --config can not be used with option --no-config"],shell=True)
        Make("CONFIG_DB").setValue(sys.argv[2])
        if (not os.access(str(CONFIG_DB.val),R_OK) ):
            subprocess.call(["print_error_and_die","The input JSON configuration file '"+str(CONFIG_DB.val)+"' does not exist or is not readable"],shell=True)
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--no-config'):
        if str(NO_CONFIG.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --no-config"],shell=True)
        if str(CONFIG_DB.val) != '':
            subprocess.call(["print_error_and_die","Option --no-config can not be used with option --config"],shell=True)
        Make("NO_CONFIG").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--graph-format'):
        # Format of graph files.
        if str(GRAPH_FORMAT.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --graph-format"],shell=True)
        if str(sys.argv[2]) != "pdf" os.path.exists(str(sys.argv[2])) "!="  "-a" str(sys.argv[2]) != "svg":
            subprocess.call(["print_error_and_die","Unsupported graph format '"+str(sys.argv[2])+"'. Supported formats: pdf, png, svg."],shell=True)
        Make("GRAPH_FORMAT").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--select-decode-only'):
        if str(SELECTED_DECODE_ONLY.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --select-decode-only"],shell=True)
        Make("SELECTED_DECODE_ONLY").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--select-functions'):
        # List of selected functions.
        if str(SELECTED_FUNCTIONS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --select-functions"],shell=True)
        Make("IFS").setValue(",")
        # parser line into array
        Make("KEEP_UNREACHABLE_FUNCS").setValue(1)
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--select-ranges'):
        # List of selected ranges.
        if str(SELECTED_RANGES.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --select-ranges"],shell=True)
        Make("SELECTED_RANGES").setValue(sys.argv[2])
        Make("IFS").setValue(",")
        # parser line into array
        Make("KEEP_UNREACHABLE_FUNCS").setValue(1)
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--stop-after'):
        # Stop decompilation after the given tool.
        if str(STOP_AFTER.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --stop-after"],shell=True)
        Make("STOP_AFTER").setValue(sys.argv[2])
        if (not re.search("^(fileinfo|unpacker|bin2llvmir|llvmir2hll)"+"$",str(STOP_AFTER.val)) ):
            subprocess.call(["print_error_and_die","Unsupported tool '"+str(STOP_AFTER.val)+"' for --stop-after"],shell=True)
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--static-code-sigfile'):
        # User provided signature file.
        if not os.path.isfile(str(sys.argv[2])):
            subprocess.call(["print_error_and_die","Invalid .yara file '"+str(sys.argv[2])+"'"],shell=True)
        Make("TEMPORARY_SIGNATURES").setValue("("+str(sys.argv[2])+")")
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--static-code-archive'):
        # User provided archive to create signature file from.
        if not os.path.isfile(str(sys.argv[2])):
            subprocess.call(["print_error_and_die","Invalid archive file '"+str(sys.argv[2])+"'"],shell=True)
        Make("SIGNATURE_ARCHIVE_PATHS").setValue("("+str(sys.argv[2])+")")
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--no-default-static-signatures'):
        Make("DO_NOT_LOAD_STATIC_SIGNATURES").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--fileinfo-verbose'):
        # Enable --verbose mode in fileinfo.
        if str(FILEINFO_VERBOSE.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --fileinfo-verbose"],shell=True)
        Make("FILEINFO_VERBOSE").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--fileinfo-use-all-external-patterns'):
        if str(FILEINFO_USE_ALL_EXTERNAL_PATTERNS.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --fileinfo-use-all-external-patterns"],shell=True)
        Make("FILEINFO_USE_ALL_EXTERNAL_PATTERNS").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--ar-name'):
        # Archive decompilation by name.
        if str(AR_NAME.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --ar-name"],shell=True)
        Make("AR_NAME").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--ar-index'):
        # Archive decompilation by index.
        if str(AR_INDEX.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --ar-index"],shell=True)
        Make("AR_INDEX").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--max-memory'):
        if str(MAX_MEMORY.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --max-memory"],shell=True)
        if str(NO_MEMORY_LIMIT.val) != '':
            subprocess.call(["print_error_and_die","Clashing options: --max-memory and --no-memory-limit"],shell=True)
        Make("MAX_MEMORY").setValue(sys.argv[2])
        if (not re.search(Str(Glob("^[0-9]+"+"$")),str(MAX_MEMORY.val)) ):
            subprocess.call(["print_error_and_die","Invalid value for --max-memory: "+str(MAX_MEMORY.val)+" (expected a positive integer)"],shell=True)
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--no-memory-limit'):
        if str(NO_MEMORY_LIMIT.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --no-memory-limit"],shell=True)
        if str(MAX_MEMORY.val) != '':
            subprocess.call(["print_error_and_die","Clashing options: --max-memory and --no-memory-limit"],shell=True)
        Make("NO_MEMORY_LIMIT").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--generate-log'):
        # Intentionally undocumented option.
        # Used only for internal testing.
        # NOT guaranteed it works everywhere (systems other than our internal test machines).
        if str(GENERATE_LOG.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --generate-log"],shell=True)
        Make("GENERATE_LOG").setValue(1)
        Make("NO_MEMORY_LIMIT").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--'):
        # Input file.
        if (Expand.hash() == 2 ):
            Make("IN").setValue(sys.argv[2])
            if (not os.access(str(IN.val),R_OK) ):
                subprocess.call(["print_error_and_die","The input file '"+str(IN.val)+"' does not exist or is not readable"],shell=True)
        elif (Expand.hash() > 2 ):
            # Invalid options.
            subprocess.call(["print_error_and_die","Invalid options: '"+str(sys.argv[2])+"', '"+str(sys.argv[3])+"' ..."],shell=True)
        break
# Check arguments and set default values for unset options.
check_arguments()
# Initialize variables used by logging.
if (str(GENERATE_LOG.val) != '' ):
    Make("LOG_DECOMPILATION_START_DATE").setValue(os.popen("date +%s").read().rstrip("\n"))
    # Put the tool log file and tmp file into /tmp because it uses tmpfs. This means that
    # the data are stored in RAM instead on the disk, which should provide faster access.
    Make("TMP_DIR").setValue("/tmp/decompiler_log")
    subprocess.call(["mkdir","-p",str(TMP_DIR.val)],shell=True)
    Make("FILE_MD5").setValue(os.popen("string_to_md5 \""+str(OUT.val)+"\"").read().rstrip("\n"))
    Make("TOOL_LOG_FILE").setValue(str(TMP_DIR.val)+"/"+str(FILE_MD5.val)+".tool")
# Raw.
if (str(MODE.val) == "raw" ):
    # Entry point for THUMB must be odd.
    if if str(ARCH.val) == "thumb":
        (RAW_ENTRY_POINT.val % 2) == 0:
        Make("RAW_ENTRY_POINT").setValue((RAW_ENTRY_POINT.val + 1))
    Make("KEEP_UNREACHABLE_FUNCS").setValue(1)
# Check for archives.
if (str(MODE.val) == "bin" ):
    # Check for archives packed in Mach-O Universal Binaries.
    print("##### Checking if file is a Mach-O Universal static library...")
    print("RUN: "+str(EXTRACT.val)+" --list "+str(IN.val))
    if (subprocess.call(["is_macho_archive",str(IN.val)],shell=True) ):
        Make("OUT_ARCHIVE").setValue(str(OUT.val)+".a")
        if (str(ARCH.val) != '' ):
            print()
            print("##### Restoring static library with architecture family "+str(ARCH.val)+"...")
            print("RUN: "+str(EXTRACT.val)+" --family "+str(ARCH.val)+" --out "+str(OUT_ARCHIVE.val)+" "+str(IN.val))
            if (not subprocess.call([str(EXTRACT.val),"--family",str(ARCH.val),"--out",str(OUT_ARCHIVE.val),str(IN.val)],shell=True) ):
                # Architecture not supported
                print("Invalid --arch option \""+str(ARCH.val)+"\". File contains these architecture families:")
                subprocess.call([str(EXTRACT.val),"--list",str(IN.val)],shell=True)
                cleanup()
                exit(1)
        else:
            # Pick best architecture
            print()
            print("##### Restoring best static library for decompilation...")
            print("RUN: "+str(EXTRACT.val)+" --best --out "+str(OUT_ARCHIVE.val)+" "+str(IN.val))
            subprocess.call([str(EXTRACT.val),"--best","--out",str(OUT_ARCHIVE.val),str(IN.val)],shell=True)
        Make("IN").setValue(OUT_ARCHIVE.val)
    print()
    print("##### Checking if file is an archive...")
    print("RUN: "+str(AR.val)+" --arch-magic "+str(IN.val))
    if (subprocess.call(["has_archive_signature",str(IN.val)],shell=True) ):
        print("This file is an archive!")
        # Check for thin signature.
        if (subprocess.call(["has_thin_archive_signature",str(IN.val)],shell=True) ):
            cleanup()
            subprocess.call(["print_error_and_die","File is a thin archive and cannot be decompiled."],shell=True)
        # Check if our tools can handle it.
        if (not subprocess.call(["is_valid_archive",str(IN.val)],shell=True) ):
            cleanup()
            subprocess.call(["print_error_and_die","The input archive has invalid format."],shell=True)
        # Get and check number of objects.
        Make("ARCH_OBJECT_COUNT").setValue(os.popen("archive_object_count \""+str(IN.val)+"\"").read().rstrip("\n"))
        if (int(ARCH_OBJECT_COUNT.val) <= 0 ):
            cleanup()
            subprocess.call(["print_error_and_die","The input archive is empty."],shell=True)
        # Prepare object output path.
        Make("OUT_RESTORED").setValue(str(OUT.val)+".restored")
        # Pick object by index.
        if (str(AR_INDEX.val) != '' ):
            print()
            print("##### Restoring object file on index '"+str(AR_INDEX.val)+"' from archive...")
            print("RUN: "+str(AR.val)+" "+str(IN.val)+" --index "+str(AR_INDEX.val)+" --output "+str(OUT_RESTORED.val))
            if (not subprocess.call(["archive_get_by_index",str(IN.val),str(AR_INDEX.val),str(OUT_RESTORED.val)],shell=True) ):
                cleanup()
                Make("VALID_INDEX").setValue((ARCH_OBJECT_COUNT.val - 1))
                if (int(VALID_INDEX.val) != 0 ):
                    subprocess.call(["print_error_and_die","File on index \""+str(AR_INDEX.val)+"\" was not found in the input archive. Valid indexes are 0-"+str(VALID_INDEX.val)+"."],shell=True)
                else:
                    subprocess.call(["print_error_and_die","File on index \""+str(AR_INDEX.val)+"\" was not found in the input archive. The only valid index is 0."],shell=True)
            Make("IN").setValue(OUT_RESTORED.val)
        elif (# Pick object by name.
        str(AR_NAME.val) != '' ):
            print()
            print("##### Restoring object file with name '"+str(AR_NAME.val)+"' from archive...")
            print("RUN: "+str(AR.val)+" "+str(IN.val)+" --name "+str(AR_NAME.val)+" --output "+str(OUT_RESTORED.val))
            if (not subprocess.call(["archive_get_by_name",str(IN.val),str(AR_NAME.val),str(OUT_RESTORED.val)],shell=True) ):
                cleanup()
                subprocess.call(["print_error_and_die","File named \""+str(AR_NAME.val)+"\" was not found in the input archive."],shell=True)
            Make("IN").setValue(OUT_RESTORED.val)
        else:
            # Print list of files.
            print("Please select file to decompile with either '--ar-index=n'")
            print("or '--ar-name=string' option. Archive contains these files:")
            subprocess.call(["archive_list_numbered_content",str(IN.val)],shell=True)
            cleanup()
            exit(1)
    else:
        if str(AR_NAME.val) != '':
            subprocess.call(["print_warning","Option --ar-name can be used only with archives."],shell=True)
        if str(AR_INDEX.val) != '':
            subprocess.call(["print_warning","Option --ar-index can be used only with archives."],shell=True)
        print("Not an archive, going to the next step.")
if (if not str(MODE.val) == "bin":
    str(MODE.val) == "raw" ):
    # Assignment of other used variables.
    Make("OUT_UNPACKED").setValue(str(OUT.val%.*)+"-unpacked")
    Make("OUT_FRONTEND").setValue(str(OUT.val)+".frontend")
    Make("OUT_FRONTEND_LL").setValue(str(OUT_FRONTEND.val)+".ll")
    Make("OUT_FRONTEND_BC").setValue(str(OUT_FRONTEND.val)+".bc")
    Make("CONFIG").setValue(str(OUT.val)+".json")
    if (str(CONFIG.val) != str(CONFIG_DB.val) ):
        subprocess.call(["rm","-f",str(CONFIG.val)],shell=True)
    if (str(CONFIG_DB.val) != '' ):
        subprocess.call(["cp",str(CONFIG_DB.val),str(CONFIG.val)],shell=True)
    # Preprocess existing file or create a new, empty JSON file.
    if (os.path.isfile(str(CONFIG.val)) ):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--preprocess"],shell=True)
    else:
        print("{}",file=file(str(CONFIG.val),'wb'))
    # Raw data needs architecture, endianess and optionaly sections's vma and entry point to be specified.
    if (str(MODE.val) == "raw" ):
        if not ARCH.val or ARCH.val "="  "-o" str(ARCH.val) == str():
            subprocess.call(["print_error_and_die","Option -a|--arch must be used with mode "+str(MODE.val)],shell=True)
        if not str(ENDIAN.val) != '':
            subprocess.call(["print_error_and_die","Option -e|--endian must be used with mode "+str(MODE.val)],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--format","raw"],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--arch",str(ARCH.val)],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--bit-size","32"],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--file-class","32"],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--endian",str(ENDIAN.val)],shell=True)
        if (str(RAW_ENTRY_POINT.val) != '' ):
            subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--entry-point",str(RAW_ENTRY_POINT.val)],shell=True)
        if (str(RAW_SECTION_VMA.val) != '' ):
            subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--section-vma",str(RAW_SECTION_VMA.val)],shell=True)
    ##
    ## Call fileinfo to create an initial config file.
    ##
    Make("FILEINFO_PARAMS").setValue("(-c "+str(CONFIG.val)+" --similarity "+str(IN.val)+" --no-hashes=all)")
    if (str(FILEINFO_VERBOSE.val) != '' ):
        Make("FILEINFO_PARAMS").setValue("(-c "+str(CONFIG.val)+" --similarity --verbose "+str(IN.val)+")")
    for Make("par").val in Array(FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES.val[@] ]):
        Make("FILEINFO_PARAMS").setValue("(--crypto "+str(par.val)+")")
    if (str(FILEINFO_USE_ALL_EXTERNAL_PATTERNS.val) != '' ):
        for Make("par").val in Array(FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES.val[@] ]):
            Make("FILEINFO_PARAMS").setValue("(--crypto "+str(par.val)+")")
    if (not str(MAX_MEMORY.val) == '' ):
        Make("FILEINFO_PARAMS").setValue("(--max-memory "+str(MAX_MEMORY.val)+")")
    elif (str(NO_MEMORY_LIMIT.val) == '' ):
        # By default, we want to limit the memory of fileinfo into half of
        # system RAM to prevent potential black screens on Windows (#270).
        Make("FILEINFO_PARAMS").setValue("(--max-memory-half-ram)")
    print()
    print("##### Gathering file information...")
    print("RUN: "+str(FILEINFO.val)+" "+str(FILEINFO_PARAMS.val[@] ]))
    if (str(GENERATE_LOG.val) != '' ):
        Make("FILEINFO_AND_TIME_OUTPUT").setValue(os.popen(str(TIME.val)+" \""+str(FILEINFO.val)+"\" \""+str(FILEINFO_PARAMS.val[@] ])+"\" 2>&1").read().rstrip("\n"))
        Make("FILEINFO_RC").setValue(_rc0)
        Make("LOG_FILEINFO_RC").setValue(os.popen("get_tool_rc \""+str(FILEINFO_RC.val)+"\" \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        Make("LOG_FILEINFO_RUNTIME").setValue(os.popen("get_tool_runtime \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        Make("LOG_FILEINFO_MEMORY").setValue(os.popen("get_tool_memory_usage \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        Make("LOG_FILEINFO_OUTPUT").setValue(os.popen("get_tool_output \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        print(LOG_FILEINFO_OUTPUT.val)
    else:
        subprocess.call([str(FILEINFO.val),str(FILEINFO_PARAMS.val[@] ])],shell=True)
        Make("FILEINFO_RC").setValue(_rc0)
    if (int(FILEINFO_RC.val) != 0 ):
        if str(GENERATE_LOG.val) != '':
            generate_log()
        cleanup()
        # The error message has been already reported by fileinfo in stderr.
        subprocess.call(["print_error_and_die"],shell=True)
    check_whether_decompilation_should_be_forcefully_stopped("fileinfo")
    ##
    ## Unpacking.
    ##
    Make("UNPACK_PARAMS").setValue("(--extended-exit-codes --output "+str(OUT_UNPACKED.val)+" "+str(IN.val)+")")
    if (not str(MAX_MEMORY.val) == '' ):
        Make("UNPACK_PARAMS").setValue("(--max-memory "+str(MAX_MEMORY.val)+")")
    elif (str(NO_MEMORY_LIMIT.val) == '' ):
        # By default, we want to limit the memory of retdec-unpacker into half
        # of system RAM to prevent potential black screens on Windows (#270).
        Make("UNPACK_PARAMS").setValue("(--max-memory-half-ram)")
    if (str(GENERATE_LOG.val) != '' ):
        Make("LOG_UNPACKER_OUTPUT").setValue(os.popen(str(UNPACK_SH.val)+" \""+str(UNPACK_PARAMS.val[@] ])+"\" 2>&1").read().rstrip("\n"))
        Make("UNPACKER_RC").setValue(_rc0)
        Make("LOG_UNPACKER_RC").setValue(UNPACKER_RC.val)
    else:
        subprocess.call([str(UNPACK_SH.val),str(UNPACK_PARAMS.val[@] ])],shell=True)
        Make("UNPACKER_RC").setValue(_rc0)
    check_whether_decompilation_should_be_forcefully_stopped("unpacker")
    # RET_UNPACK_OK=0
    # RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK=1
    # RET_NOTHING_TO_DO=2
    # RET_UNPACKER_FAILED_OTHERS_OK=3
    # RET_UNPACKER_FAILED=4
    if (if not if not int(UNPACKER_RC.val) == 0:
        int(UNPACKER_RC.val) == 1:
        int(UNPACKER_RC.val) == 3 ):
        # Successfully unpacked -> re-run fileinfo to obtain fresh information.
        Make("IN").setValue(OUT_UNPACKED.val)
        Make("FILEINFO_PARAMS").setValue("(-c "+str(CONFIG.val)+" --similarity "+str(IN.val)+" --no-hashes=all)")
        if (str(FILEINFO_VERBOSE.val) != '' ):
            Make("FILEINFO_PARAMS").setValue("(-c "+str(CONFIG.val)+" --similarity --verbose "+str(IN.val)+")")
        for Make("par").val in Array(FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES.val[@] ]):
            Make("FILEINFO_PARAMS").setValue("(--crypto "+str(par.val)+")")
        if (str(FILEINFO_USE_ALL_EXTERNAL_PATTERNS.val) != '' ):
            for Make("par").val in Array(FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES.val[@] ]):
                Make("FILEINFO_PARAMS").setValue("(--crypto "+str(par.val)+")")
        if (not str(MAX_MEMORY.val) == '' ):
            Make("FILEINFO_PARAMS").setValue("(--max-memory "+str(MAX_MEMORY.val)+")")
        elif (str(NO_MEMORY_LIMIT.val) == '' ):
            # By default, we want to limit the memory of fileinfo into half of
            # system RAM to prevent potential black screens on Windows (#270).
            Make("FILEINFO_PARAMS").setValue("(--max-memory-half-ram)")
        print()
        print("##### Gathering file information after unpacking...")
        print("RUN: "+str(FILEINFO.val)+" "+str(FILEINFO_PARAMS.val[@] ]))
        if (str(GENERATE_LOG.val) != '' ):
            Make("FILEINFO_AND_TIME_OUTPUT").setValue(os.popen(str(TIME.val)+" \""+str(FILEINFO.val)+"\" \""+str(FILEINFO_PARAMS.val[@] ])+"\" 2>&1").read().rstrip("\n"))
            Make("FILEINFO_RC").setValue(_rc0)
            Make("LOG_FILEINFO_RC").setValue(os.popen("get_tool_rc \""+str(FILEINFO_RC.val)+"\" \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
            Make("FILEINFO_RUNTIME").setValue(os.popen("get_tool_runtime \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
            Make("LOG_FILEINFO_RUNTIME").setValue((LOG_FILEINFO_RUNTIME.val + FILEINFO_RUNTIME.val))
            Make("FILEINFO_MEMORY").setValue(os.popen("get_tool_memory_usage \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
            Make("LOG_FILEINFO_MEMORY").setValue(((LOG_FILEINFO_MEMORY.val + FILEINFO_MEMORY.val) // 2))
            Make("LOG_FILEINFO_OUTPUT").setValue(os.popen("get_tool_output \""+str(FILEINFO_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
            print(LOG_FILEINFO_OUTPUT.val)
        else:
            subprocess.call([str(FILEINFO.val),str(FILEINFO_PARAMS.val[@] ])],shell=True)
            Make("FILEINFO_RC").setValue(_rc0)
        if (int(FILEINFO_RC.val) != 0 ):
            if str(GENERATE_LOG.val) != '':
                generate_log()
            cleanup()
            # The error message has been already reported by fileinfo in stderr.
            subprocess.call(["print_error_and_die"],shell=True)
        print_warning_if_decompiling_bytecode()
    # Check whether the architecture was specified.
    if (str(ARCH.val) != '' ):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--arch",str(ARCH.val)],shell=True)
    else:
        # Get full name of the target architecture including comments in parentheses
        Make("ARCH_FULL").setValue(os.popen("\""+str(CONFIGTOOL.val)+"\" \""+str(CONFIG.val)+"\" --read --arch | awk \"{print tolower($0").read().rstrip("\n")+"})")
        # Strip comments in parentheses and all trailing whitespace
        Make("ARCH").setValue(os.popen("echo "+str(ARCH_FULL.val%(*)+" | sed -e 's/^[[:space:]]*//'").read().rstrip("\n"))
    # Get object file format.
    Make("FORMAT").setValue(os.popen("\""+str(CONFIGTOOL.val)+"\" \""+str(CONFIG.val)+"\" --read --format | awk \"{print tolower($1").read().rstrip("\n")+";})")
    # Intel HEX needs architecture to be specified
    if (str(FORMAT.val) == "ihex" ):
        if not ARCH.val or ARCH.val "="  "-o" str(ARCH.val) == str():
            subprocess.call(["print_error_and_die","Option -a|--arch must be used with format "+str(FORMAT.val)],shell=True)
        if not str(ENDIAN.val) != '':
            subprocess.call(["print_error_and_die","Option -e|--endian must be used with format "+str(FORMAT.val)],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--arch",str(ARCH.val)],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--bit-size","32"],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--file-class","32"],shell=True)
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--endian",str(ENDIAN.val)],shell=True)
    # Check whether the correct target architecture was specified.
    if (str(ARCH.val) == "arm" -o str(ARCH.val)"=" != '' ):
        Make("ORDS_DIR").setValue(ARM_ORDS_DIR.val)
    elif (str(ARCH.val) == "x86" ):
        Make("ORDS_DIR").setValue(X86_ORDS_DIR.val)
    elif (str(ARCH.val) == "powerpc" -o str(ARCH.val) "="  "-o" str(ARCH.val) == "pic32" ):
        pass
    else:
        # nothing
        if str(GENERATE_LOG.val) != '':
            generate_log()
        cleanup()
        subprocess.call(["print_error_and_die","Unsupported target architecture '"+str(ARCH.val^^)+"'. Supported architectures: Intel x86, ARM, ARM+Thumb, MIPS, PIC32, PowerPC."],shell=True)
    # Check file class (e.g. "ELF32", "ELF64"). At present, we can only decompile 32-bit files.
    # Note: we prefer to report the "unsupported architecture" error (above) than this "generic" error.
    Make("FILECLASS").setValue(os.popen("\""+str(CONFIGTOOL.val)+"\" \""+str(CONFIG.val)+"\" --read --file-class").read().rstrip("\n"))
    if (if str(FILECLASS.val) != "16":
        str(FILECLASS.val) != "32" ):
        if str(GENERATE_LOG.val) != '':
            generate_log()
        cleanup()
        subprocess.call(["print_error_and_die","Unsupported target format '"+str(FORMAT.val^^)+str(FILECLASS.val)+"'. Supported formats: ELF32, PE32, Intel HEX 32, Mach-O 32."],shell=True)
    # Set path to statically linked code signatures.
    #
    # TODO: Useing ELF for IHEX is ok, but for raw, we probably should somehow decide between ELF and PE, or use both, for RAW.
    Make("SIG_FORMAT").setValue(FORMAT.val,,)
    if (if not str(SIG_FORMAT.val) == "ihex":
        str(SIG_FORMAT.val) == "raw" ):
        Make("SIG_FORMAT").setValue("elf")
    Make("ENDIAN").setValue(os.popen("\""+str(CONFIGTOOL.val)+"\" \""+str(CONFIG.val)+"\" --read --endian").read().rstrip("\n"))
    
    if ( str(ENDIAN.val) == 'little'):
        Make("SIG_ENDIAN").setValue("le")
    elif ( str(ENDIAN.val) == 'big'):
        Make("SIG_ENDIAN").setValue("be")
    else:
        Make("SIG_ENDIAN").setValue()
    Make("SIG_ARCH").setValue(ARCH.val,,)
    if (str(SIG_ARCH.val) == "pic32" ):
        Make("SIG_ARCH").setValue("mips")
    Make("SIGNATURES_DIR").setValue(str(GENERIC_SIGNATURES_DIR.val)+"/"+str(SIG_FORMAT.val)+"/"+str(FILECLASS.val,,)+"/"+str(SIG_ENDIAN.val,,)+"/"+str(SIG_ARCH.val))
    print_warning_if_decompiling_bytecode()
    # Decompile unreachable functions.
    if (str(KEEP_UNREACHABLE_FUNCS.val) != '' ):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--keep-unreachable-funcs","true"],shell=True)
    # Get signatures from selected archives.
    if (Expand.hash()SIGNATURE_ARCHIVE_PATHS[@] != 0 ):
        print()
        print("##### Extracting signatures from selected archives...")
    Make("l").setValue(0)
    while (l.val < Expand.hash()SIGNATURE_ARCHIVE_PATHS[@].val):
        Make("LIB").setValue(SIGNATURE_ARCHIVE_PATHS.val[l.val] ])
        print("Extracting signatures from file '"+str(LIB.val)+"'")
        Make("CROP_ARCH_PATH").setValue(os.popen("basename \""+str(LIB.val)+"\" | LC_ALL=C sed -e \"s/[^A-Za-z0-9_.-]/_/g\"").read().rstrip("\n"))
        Make("SIG_OUT").setValue(str(OUT.val)+"."+str(CROP_ARCH_PATH.val)+"."+str(l.val)+".yara")
        if (subprocess.call(str(SIG_FROM_LIB_SH.val) + " " + str(LIB.val) + " " + "--output" + " " + str(SIG_OUT.val),shell=True,stderr=subprocess.STDOUT,stdout=file(str(DEV_NULL.val),'wb')) ):
            subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--user-signature",str(SIG_OUT.val)],shell=True)
            Make("SIGNATURES_TO_REMOVE").setValue("("+str(SIG_OUT.val)+")")
        else:
            subprocess.call(["print_warning","Failed extracting signatures from file \""+str(LIB.val)+"\""],shell=True)
        Make("l").postinc()
    # Store paths of signature files into config for frontend.
    if not str(DO_NOT_LOAD_STATIC_SIGNATURES.val) != '':
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--signatures",str(SIGNATURES_DIR.val)],shell=True)
    # User provided signatures.
    for Make("i").val in Array(TEMPORARY_SIGNATURES.val[@] ]):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--user-signature",str(i.val)],shell=True)
    # Store paths of type files into config for frontend.
    if (os.path.isdir(str(GENERIC_TYPES_DIR.val)) ):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--types",str(GENERIC_TYPES_DIR.val)],shell=True)
    # Store path of directory with ORD files into config for frontend (note: only directory, not files themselves).
    if (os.path.isdir(str(ORDS_DIR.val)) ):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--ords",str(ORDS_DIR.val)+"/"],shell=True)
    # Store paths to file with PDB debugging information into config for frontend.
    if (os.path.exists(str(PDB_FILE.val)) ):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--pdb-file",str(PDB_FILE.val)],shell=True)
    # Store file names of input and output into config for frontend.
    subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--input-file",str(IN.val)],shell=True)
    subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--frontend-output-file",str(OUT_FRONTEND_LL.val)],shell=True)
    subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--output-file",str(OUT.val)],shell=True)
    # Store decode only selected parts flag.
    if (str(SELECTED_DECODE_ONLY.val) != '' ):
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--decode-only-selected","true"],shell=True)
    else:
        subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--decode-only-selected","false"],shell=True)
    # Store selected functions or selected ranges into config for frontend.
    if (str(SELECTED_FUNCTIONS.val) != '' ):
        for Make("f").val in Array(SELECTED_FUNCTIONS.val[@] ]):
            subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--selected-func",str(f.val)],shell=True)
    if (str(SELECTED_RANGES.val) != '' ):
        for Make("r").val in Array(SELECTED_RANGES.val[@] ]):
            subprocess.call([str(CONFIGTOOL.val),str(CONFIG.val),"--write","--selected-range",str(r.val)],shell=True)
    # Assignment of other used variables.
    # We have to ensure that the .bc version of the decompiled .ll file is placed
    # in the same directory as are other output files. Otherwise, there may be
    # race-condition problems when the same input .ll file is decompiled in
    # parallel processes because they would overwrite each other's .bc file. This
    # is most likely to happen in regression tests in the "ll" mode.
    Make("OUT_BACKEND").setValue(str(OUT.val)+".backend")
    # If the input file is the same as $OUT_BACKEND_LL below, then we have to change the name of
    # $OUT_BACKEND. Otherwise, the input file would get overwritten during the conversion.
    if str(OUT_FRONTEND_LL.val) == str(OUT_BACKEND.val)+".ll":
        Make("OUT_BACKEND").setValue(str(OUT.val)+".backend.backend")
    Make("OUT_BACKEND_BC").setValue(str(OUT_BACKEND.val)+".bc")
    Make("OUT_BACKEND_LL").setValue(str(OUT_BACKEND.val)+".ll")
    ##
    ## Decompile the binary into LLVM IR.
    ##
    if (str(KEEP_UNREACHABLE_FUNCS.val) != '' ):
        # Prevent bin2llvmir from removing unreachable functions.
        Make("BIN2LLVMIR_PARAMS").setValue(os.popen("sed 's/-unreachable-funcs *//g' <<< \""+str(BIN2LLVMIR_PARAMS.val)+"\"").read().rstrip("\n"))
    if (if str(CONFIG.val) == str():
        str(CONFIG_DB.val) != str() ):
        Make("CONFIG").setValue(CONFIG_DB.val)
    Make("BIN2LLVMIR_PARAMS").setValue("(-provider-init -config-path "+str(CONFIG.val)+" -decoder "+str(BIN2LLVMIR_PARAMS.val)+")")
    if (not str(MAX_MEMORY.val) == '' ):
        Make("BIN2LLVMIR_PARAMS").setValue("(-max-memory "+str(MAX_MEMORY.val)+")")
    elif (str(NO_MEMORY_LIMIT.val) == '' ):
        # By default, we want to limit the memory of bin2llvmir into half of
        # system RAM to prevent potential black screens on Windows (#270).
        Make("BIN2LLVMIR_PARAMS").setValue("(-max-memory-half-ram)")
    print()
    print("##### Decompiling "+str(IN.val)+" into "+str(OUT_BACKEND_BC.val)+"...")
    print("RUN: "+str(BIN2LLVMIR.val)+" "+str(BIN2LLVMIR_PARAMS.val[@] ])+" -o "+str(OUT_BACKEND_BC.val))
    if (str(GENERATE_LOG.val) != '' ):
        def thread1():
            subprocess.call(str(TIME.val) + " " + str(BIN2LLVMIR.val) + " " + str(BIN2LLVMIR_PARAMS.val[@] ]) + " " + "-o" + " " + str(OUT_BACKEND_BC.val),shell=True,stdout=file(str(TOOL_LOG_FILE.val),'wb'),stderr=subprocess.STDOUT)
            
        threading.Thread(target=thread1).start()
        
        Make("PID").setValue(Expand.exclamation())
        
        def thread2():
            timed_kill(PID.val)
        threading.Thread(target=thread2).start()
        
        subprocess.call("wait" + " " + str(PID.val),shell=True,stderr=subprocess.STDOUT,stdout=file(str(DEV_NULL.val),'wb'))
        
        
        Make("BIN2LLVMIR_RC").setValue(_rc2)
        Make("BIN2LLVMIR_AND_TIME_OUTPUT").setValue(os.popen("cat \""+str(TOOL_LOG_FILE.val)+"\"").read().rstrip("\n"))
        Make("LOG_BIN2LLVMIR_RC").setValue(os.popen("get_tool_rc \""+str(BIN2LLVMIR_RC.val)+"\" \""+str(BIN2LLVMIR_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        Make("LOG_BIN2LLVMIR_RUNTIME").setValue(os.popen("get_tool_runtime \""+str(BIN2LLVMIR_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        Make("LOG_BIN2LLVMIR_MEMORY").setValue(os.popen("get_tool_memory_usage \""+str(BIN2LLVMIR_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        Make("LOG_BIN2LLVMIR_OUTPUT").setValue(os.popen("get_tool_output \""+str(BIN2LLVMIR_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
        print(LOG_BIN2LLVMIR_OUTPUT.val,end="")
    else:
        subprocess.call([str(BIN2LLVMIR.val),str(BIN2LLVMIR_PARAMS.val[@] ]),"-o",str(OUT_BACKEND_BC.val)],shell=True)
        Make("BIN2LLVMIR_RC").setValue(_rc2)
    if (int(BIN2LLVMIR_RC.val) != 0 ):
        if str(GENERATE_LOG.val) != '':
            generate_log()
        cleanup()
        subprocess.call(["print_error_and_die","Decompilation to LLVM IR failed"],shell=True)
    check_whether_decompilation_should_be_forcefully_stopped("bin2llvmir")
# modes "bin" || "raw"
# LL mode goes straight to backend.
if (str(MODE.val) == "ll" ):
    Make("OUT_BACKEND_BC").setValue(IN.val)
    Make("CONFIG").setValue(CONFIG_DB.val)
# Conditional initialization.
BACKEND_VAR_RENAMER=Bash2Py(Expand.colonEq("BACKEND_VAR_RENAMER","readable"))
BACKEND_CALL_INFO_OBTAINER=Bash2Py(Expand.colonEq("BACKEND_CALL_INFO_OBTAINER","optim"))
BACKEND_ARITHM_EXPR_EVALUATOR=Bash2Py(Expand.colonEq("BACKEND_ARITHM_EXPR_EVALUATOR","c"))
BACKEND_LLVMIR2BIR_CONVERTER=Bash2Py(Expand.colonEq("BACKEND_LLVMIR2BIR_CONVERTER","orig"))
# Create parameters for the $LLVMIR2HLL call.
LLVMIR2HLL_PARAMS=Bash2Py("(-target-hll="+str(HLL.val)+" -var-renamer="+str(BACKEND_VAR_RENAMER.val)+" -var-name-gen=fruit -var-name-gen-prefix= -call-info-obtainer="+str(BACKEND_CALL_INFO_OBTAINER.val)+" -arithm-expr-evaluator="+str(BACKEND_ARITHM_EXPR_EVALUATOR.val)+" -validate-module -llvmir2bir-converter="+str(BACKEND_LLVMIR2BIR_CONVERTER.val)+" -o "+str(OUT.val)+" "+str(OUT_BACKEND_BC.val)+")")
if str(BACKEND_NO_DEBUG.val) == '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-enable-debug)")
if str(BACKEND_NO_DEBUG_COMMENTS.val) == '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-emit-debug-comments)")
if str(CONFIG.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-config-path="+str(CONFIG.val)+")")
if str(KEEP_UNREACHABLE_FUNCS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-keep-unreachable-funcs)")
if str(BACKEND_SEMANTICS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-semantics "+str(BACKEND_SEMANTICS.val)+")")
if str(BACKEND_ENABLED_OPTS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-enabled-opts="+str(BACKEND_ENABLED_OPTS.val)+")")
if str(BACKEND_DISABLED_OPTS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-disabled-opts="+str(BACKEND_DISABLED_OPTS.val)+")")
if str(BACKEND_OPTS_DISABLED.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-no-opts)")
if str(BACKEND_AGGRESSIVE_OPTS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-aggressive-opts)")
if str(BACKEND_VAR_RENAMING_DISABLED.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-no-var-renaming)")
if str(BACKEND_NO_SYMBOLIC_NAMES.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-no-symbolic-names)")
if str(BACKEND_KEEP_ALL_BRACKETS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-keep-all-brackets)")
if str(BACKEND_KEEP_LIBRARY_FUNCS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-keep-library-funcs)")
if str(BACKEND_NO_TIME_VARYING_INFO.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-no-time-varying-info)")
if str(BACKEND_NO_COMPOUND_OPERATORS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-no-compound-operators)")
if str(BACKEND_FIND_PATTERNS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-find-patterns "+str(BACKEND_FIND_PATTERNS.val)+")")
if str(BACKEND_EMIT_CG.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-emit-cg)")
if str(BACKEND_FORCED_MODULE_NAME.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-force-module-name="+str(BACKEND_FORCED_MODULE_NAME.val)+")")
if str(BACKEND_STRICT_FPU_SEMANTICS.val) != '':
    Make("LLVMIR2HLL_PARAMS").setValue("(-strict-fpu-semantics)")
if (str(BACKEND_EMIT_CFG.val) != '' ):
    Make("LLVMIR2HLL_PARAMS").setValue("(-emit-cfgs)")
    if str(BACKEND_CFG_TEST.val) != '':
        Make("LLVMIR2HLL_PARAMS").setValue("(--backend-cfg-test)")
if (not str(MAX_MEMORY.val) == '' ):
    Make("LLVMIR2HLL_PARAMS").setValue("(-max-memory "+str(MAX_MEMORY.val)+")")
elif (str(NO_MEMORY_LIMIT.val) == '' ):
    # By default, we want to limit the memory of llvmir2hll into half of system
    # RAM to prevent potential black screens on Windows (#270).
    Make("LLVMIR2HLL_PARAMS").setValue("(-max-memory-half-ram)")
# Decompile the optimized IR code.
print()
print("##### Decompiling "+str(OUT_BACKEND_BC.val)+" into "+str(OUT.val)+"...")
print("RUN: "+str(LLVMIR2HLL.val)+" "+str(LLVMIR2HLL_PARAMS.val[@] ]))
if (str(GENERATE_LOG.val) != '' ):
    def thread3():
        subprocess.call(str(TIME.val) + " " + str(LLVMIR2HLL.val) + " " + str(LLVMIR2HLL_PARAMS.val[@] ]),shell=True,stdout=file(str(TOOL_LOG_FILE.val),'wb'),stderr=subprocess.STDOUT)
        
    threading.Thread(target=thread3).start()
    
    Make("PID").setValue(Expand.exclamation())
    
    def thread4():
        timed_kill(PID.val)
    threading.Thread(target=thread4).start()
    
    subprocess.call("wait" + " " + str(PID.val),shell=True,stderr=subprocess.STDOUT,stdout=file(str(DEV_NULL.val),'wb'))
    
    
    Make("LLVMIR2HLL_RC").setValue(_rc4)
    Make("LLVMIR2HLL_AND_TIME_OUTPUT").setValue(os.popen("cat \""+str(TOOL_LOG_FILE.val)+"\"").read().rstrip("\n"))
    Make("LOG_LLVMIR2HLL_RC").setValue(os.popen("get_tool_rc \""+str(LLVMIR2HLL_RC.val)+"\" \""+str(LLVMIR2HLL_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
    Make("LOG_LLVMIR2HLL_RUNTIME").setValue(os.popen("get_tool_runtime \""+str(LLVMIR2HLL_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
    Make("LOG_LLVMIR2HLL_MEMORY").setValue(os.popen("get_tool_memory_usage \""+str(LLVMIR2HLL_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
    Make("LOG_LLVMIR2HLL_OUTPUT").setValue(os.popen("get_tool_output \""+str(LLVMIR2HLL_AND_TIME_OUTPUT.val)+"\"").read().rstrip("\n"))
    print(LOG_LLVMIR2HLL_OUTPUT.val)
    # Wait a bit to ensure that all the memory that has been assigned to the tool was released.
    subprocess.call(["sleep","0.1"],shell=True)
else:
    subprocess.call([str(LLVMIR2HLL.val),str(LLVMIR2HLL_PARAMS.val[@] ])],shell=True)
    Make("LLVMIR2HLL_RC").setValue(_rc4)
if (int(LLVMIR2HLL_RC.val) != 0 ):
    if str(GENERATE_LOG.val) != '':
        generate_log()
    cleanup()
    subprocess.call(["print_error_and_die","Decompilation of file '"+str(OUT_BACKEND_BC.val)+"' failed"],shell=True)
check_whether_decompilation_should_be_forcefully_stopped("llvmir2hll")
# Conditional initialization.
GRAPH_FORMAT=Bash2Py(Expand.colonEq("GRAPH_FORMAT","png"))
BACKEND_CG_CONVERSION=Bash2Py(Expand.colonEq("BACKEND_CG_CONVERSION","auto"))
BACKEND_CFG_CONVERSION=Bash2Py(Expand.colonEq("BACKEND_CFG_CONVERSION","auto"))
# Convert .dot graphs to desired format.
if (( str(BACKEND_EMIT_CG.val) != '' and str(BACKEND_CG_CONVERSION.val) == "auto" ) or ( str(BACKEND_EMIT_CFG.val) != '' and str(BACKEND_CFG_CONVERSION.val) == "auto" ) ):
    print()
    print("##### Converting .dot files to the desired format...")
if (if str(BACKEND_EMIT_CG.val) != '':
    str(BACKEND_CG_CONVERSION.val) == "auto" ):
    print("RUN: dot -T"+str(GRAPH_FORMAT.val)+" "+str(OUT.val)+".cg.dot > "+str(OUT.val)+".cg."+str(GRAPH_FORMAT.val))
    subprocess.call("dot" + " " + "-T"+str(GRAPH_FORMAT.val) + " " + str(OUT.val)+".cg.dot",shell=True,stdout=file(str(OUT.val)+".cg."+str(GRAPH_FORMAT.val),'wb'))

if (if str(BACKEND_EMIT_CFG.val) != '':
    str(BACKEND_CFG_CONVERSION.val) == "auto" ):
    for Make("cfg").val in Glob(str(OUT.val)+".cfg.*.dot"):
        print("RUN: dot -T"+str(GRAPH_FORMAT.val)+" "+str(cfg.val)+" > "+str(cfg.val%.*)+"."+str(GRAPH_FORMAT.val))
        subprocess.call("dot" + " " + "-T"+str(GRAPH_FORMAT.val) + " " + str(cfg.val),shell=True,stdout=file(str(cfg.val%.*)+"."+str(GRAPH_FORMAT.val),'wb'))

# Remove trailing whitespace and the last redundant empty new line from the
# generated output (if any). It is difficult to do this in the back-end, so we
# do it here.
# Note: Do not use the -i flag (in-place replace) as there is apparently no way
#       of getting sed -i to work consistently on both MacOS and Linux.
_rc4 = subprocess.call("sed" + " " + "-e" + " " + ":a" + " " + "-e" + " " + "/^\\n*$/{$d;N;};/\\n$/ba" + " " + "-e" + " " + "s/[[:space:]]*$//",shell=True,stdin=file(str(OUT.val),'rb'),stdout=file(str(OUT.val)+".tmp",'wb'))

_rc4 = subprocess.call(["mv",str(OUT.val)+".tmp",str(OUT.val)],shell=True)
# Colorize output file.
if (str(COLOR_IDA.val) != '' ):
    subprocess.call([str(IDA_COLORIZER.val),str(OUT.val),str(CONFIG.val)],shell=True)
# Store the information about the decompilation into the JSON file.
if str(GENERATE_LOG.val) != '':
    generate_log()
# Success!
cleanup()
print()
print("##### Done!")
