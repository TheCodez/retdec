#! /usr/bin/env python
from __future__ import print_function
import sys,os,subprocess,glob,re
from stat import *
class Bash2Py(object):
  __slots__ = ["val"]
  def __init__(self, value=''):
    self.val = value
  def setValue(self, value=None):
    self.val = value
    return value

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
  def colonEq(name, value=''):
    ret = GetValue(name)
    if (ret is None or ret == ''):
      SetValue(name, value)
      ret = value
    return ret

#
# The script tries to unpack the given executable file by using any
# of the supported unpackers, which are at present:
#    * generic unpacker
#    * upx
#
# Required argument:
#    * (packed) binary file
#
# Optional arguments:
#    * desired name of unpacked file
#    * use extended exit codes
#
# Returns:
#  0 successfully unpacked
RET_UNPACK_OK=Bash2Py(0)
#  1 generic unpacker - nothing to do; upx succeeded (--extended-exit-codes only)
RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK=Bash2Py(1)
#  2 not packed or unknown packer
RET_NOTHING_TO_DO=Bash2Py(2)
#  3 generic unpacker failed; upx succeeded (--extended-exit-codes only)
RET_UNPACKER_FAILED_OTHERS_OK=Bash2Py(3)
#  4 generic unpacker failed; upx not succeeded
RET_UNPACKER_FAILED=Bash2Py(4)
# 10 other errors
#RET_OTHER_ERRORS=10
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
    print("Unpacking of the given executable file.")
    print()
    print("Usage:")
    print("    "+__file__+" [ options ] file")
    print()
    print("Options:")
    print("    -h,        --help                 Print this help message.")
    print("    -e,        --extended-exit-codes  Use more granular exit codes than just 0/1.")
    print("    -o FILE,   --output FILE          Output file (default: file-unpacked).")
    print("               --max-memory N         Limit the maximal memory of retdec-unpacker to N bytes.")
    print("               --max-memory-half-ram  Limit the maximal memory of retdec-unpacker to half of system RAM.")

#
# Check proper combination of input arguments.
#
def check_arguments () :
    global IN
    global OUT

    # Check whether the input file was specified.
    if (str(IN.val) == '' ):
        subprocess.call(["print_error_and_die","No input file was specified"],shell=True)
    # Conditional initialization.
    OUT=Bash2Py(Expand.colonEq("OUT","\""+str(IN.val)+"\"-unpacked"))
    # Convert to absolute paths.
    IN=Bash2Py(os.popen("get_realpath \""+str(IN.val)+"\"").read().rstrip("\n"))
    OUT=Bash2Py(os.popen("get_realpath \""+str(OUT.val)+"\"").read().rstrip("\n"))

#
# Try to unpack the given file.
#
def try_to_unpack (_p1,_p2) :
    global RET_NOTHING_TO_DO
    global UNPACKER_PARAMS
    global MAX_MEMORY
    global MAX_MEMORY_HALF_RAM
    global UNPACKER
    global UNPACKER_RETCODE
    global RET_UNPACK_OK
    global DEV_NULL
    global EXTENDED
    global RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK
    global RET_UNPACKER_FAILED_OTHERS_OK
    global RET_UNPACKER_FAILED

    if (if not if not Expand.hash() != 2:
        not (os.path.exists(str(_p1)) and os.stat(str(_p1)).st_size > 0):
        str(_p2) == '' ):
        print("UNPACKER: wrong arguments",stderr=subprocess.STDOUT)
        return(int(RET_NOTHING_TO_DO.val))
    IN=Bash2Py(_p1)
    OUT=Bash2Py(_p2)
    # Try to unpack via inhouse generic unpacker.
    # Create parameters.
    # Generic unpacker exit codes:
    # 0 Unpacker ended successfully.
    UNPACKER_EXIT_CODE_OK=Bash2Py(0)
    # 1 There was not found matching plugin.
    UNPACKER_EXIT_CODE_NOTHING_TO_DO=Bash2Py(1)
    # 2 At least one plugin failed at the unpacking of the file.
    UNPACKER_EXIT_CODE_UNPACKING_FAILED=Bash2Py(2)
    # 3 Error with preprocessing of input file before unpacking.
    UNPACKER_EXIT_CODE_PREPROCESSING_ERROR=Bash2Py(3)
    UNPACKER_PARAMS=Bash2Py("("+str(IN.val)+" -o "+str(OUT.val)+")")
    if (not str(MAX_MEMORY.val) == '' ):
        Make("UNPACKER_PARAMS").setValue("(--max-memory "+str(MAX_MEMORY.val)+")")
    elif (not str(MAX_MEMORY_HALF_RAM.val) == '' ):
        Make("UNPACKER_PARAMS").setValue("(--max-memory-half-ram)")
    print()
    print("##### Trying to unpack "+str(IN.val)+" into "+str(OUT.val)+" by using generic unpacker...")
    print("RUN: "+str(UNPACKER.val)+" "+str(UNPACKER_PARAMS.val[@] ]))
    _rc0 = subprocess.call([str(UNPACKER.val),str(UNPACKER_PARAMS.val[@] ])],shell=True)
    UNPACKER_RETCODE=Bash2Py(_rc0)
    if (str(UNPACKER_RETCODE.val) == str(UNPACKER_EXIT_CODE_OK.val) ):
        print("##### Unpacking by using generic unpacker: successfully unpacked")
        return(int(RET_UNPACK_OK.val))
    elif (str(UNPACKER_RETCODE.val) == str(UNPACKER_EXIT_CODE_NOTHING_TO_DO.val) ):
        print("##### Unpacking by using generic unpacker: nothing to do")
    else:
        # Do not return -> try the next unpacker
        # UNPACKER_EXIT_CODE_UNPACKING_FAILED
        # UNPACKER_EXIT_CODE_PREPROCESSING_ERROR
        print("##### Unpacking by using generic unpacker: failed")
    # Do not return -> try the next unpacker
    # Try to unpack via UPX
    print()
    print("##### Trying to unpack "+str(IN.val)+" into "+str(OUT.val)+" by using UPX...")
    print("RUN: upx -d "+str(IN.val)+" -o "+str(OUT.val))
    _rc0 = subprocess.call("upx" + " " + "-d" + " " + str(IN.val) + " " + "-o" + " " + str(OUT.val),shell=True,stdout=file(str(DEV_NULL.val),'wb'))
    
    if (str(_rc0) == "0" ):
        print("##### Unpacking by using UPX: successfully unpacked")
        if (str(EXTENDED.val) == "yes" ):
            if (str(UNPACKER_RETCODE.val) == str(UNPACKER_EXIT_CODE_NOTHING_TO_DO.val) ):
                return(int(RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK.val))
            elif (int(UNPACKER_RETCODE.val) >= int(UNPACKER_EXIT_CODE_UNPACKING_FAILED.val) ):
                return(int(RET_UNPACKER_FAILED_OTHERS_OK.val))
        else:
            return(int(RET_UNPACK_OK.val))
    else:
        # We cannot distinguish whether upx failed or the input file was
        # not upx-packed
        print("##### Unpacking by using UPX: nothing to do")
    # Do not return -> try the next unpacker
    # Return.
    if (int(UNPACKER_RETCODE.val) >= int(UNPACKER_EXIT_CODE_UNPACKING_FAILED.val) ):
        return(int(RET_UNPACKER_FAILED.val))
    else:
        return(int(RET_NOTHING_TO_DO.val))

SCRIPT_NAME=Bash2Py(__file__)
GETOPT_SHORTOPT=Bash2Py("eho:")
GETOPT_LONGOPT=Bash2Py("extended-exit-codes,help,output:,max-memory:,max-memory-half-ram")
# Check script arguments.
PARSED_OPTIONS=Bash2Py(os.popen("getopt -o \""+str(GETOPT_SHORTOPT.val)+"\" -l \""+str(GETOPT_LONGOPT.val)+"\" -n \""+str(SCRIPT_NAME.val)+"\" -- \""+Str(Expand.at())+"\"").read().rstrip("\n"))
# Bad arguments.
if _rc0 != 0:
    subprocess.call(["print_error_and_die","Getopt - parsing parameters failed"],shell=True)
eval("set","--",str(PARSED_OPTIONS.val))
while (True):
    
    if ( str(sys.argv[1]) == '-e' or str(sys.argv[1]) == '--extended-exit-codes'):
        # Use extented exit codes.
        if str(EXTENDED.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -e|--extended-exit-codes"],shell=True)
        Make("EXTENDED").setValue("yes")
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help'):
        # Help.
        print_help()
        exit(int(RET_UNPACK_OK.val))
    elif ( str(sys.argv[1]) == '-o' or str(sys.argv[1]) == '--output'):
        # Output file.
        if str(OUT.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: -o|--output"],shell=True)
        Make("OUT").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--max-memory-half-ram'):
        if str(MAX_MEMORY_HALF_RAM.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --max-memory-half-ram"],shell=True)
        if str(MAX_MEMORY.val) != '':
            subprocess.call(["print_error_and_die","Clashing options: --max-memory-half-ram and --max-memory"],shell=True)
        Make("MAX_MEMORY_HALF_RAM").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--max-memory'):
        if str(MAX_MEMORY.val) != '':
            subprocess.call(["print_error_and_die","Duplicate option: --max-memory"],shell=True)
        if str(MAX_MEMORY_HALF_RAM.val) != '':
            subprocess.call(["print_error_and_die","Clashing options: --max-memory and --max-memory-half-ram"],shell=True)
        Make("MAX_MEMORY").setValue(sys.argv[2])
        if (not re.search(Str(Glob("^[0-9]+"+"$")),str(MAX_MEMORY.val)) ):
            subprocess.call(["print_error_and_die","Invalid value for --max-memory: "+str(MAX_MEMORY.val)+" (expected a positive integer)"],shell=True)
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--'):
        # Input file.
        if (Expand.hash() == 2 ):
            Make("IN").setValue(sys.argv[2])
            if not os.access(str(IN.val),R_OK):
                subprocess.call(["print_error_and_die","The input file '"+str(IN.val)+"' does not exist or is not readable"],shell=True)
        elif (Expand.hash() > 2 ):
            # Invalid options.
            subprocess.call(["print_error_and_die","Invalid options: '"+str(sys.argv[2])+"', '"+str(sys.argv[3])+"' ..."],shell=True)
        break
# Check arguments and set default values for unset options.
check_arguments()
CONTINUE=Bash2Py(1)
FINAL_RC=Bash2Py(-1)
while (str(CONTINUE.val) == "1"):
    try_to_unpack(IN.val, str(OUT.val)+".tmp")
    Make("RC").setValue(_rc0)
    if (if not if not str(RC.val) == str(RET_UNPACK_OK.val):
        str(RC.val) == str(RET_UNPACKER_NOTHING_TO_DO_OTHERS_OK.val):
        str(RC.val) == str(RET_UNPACKER_FAILED_OTHERS_OK.val) ):
        Make("FINAL_RC").setValue(RC.val)
        subprocess.call(["mv",str(OUT.val)+".tmp",str(OUT.val)],shell=True)
        Make("IN").setValue(OUT.val)
    else:
        # Remove the temporary file, just in case some of the unpackers crashed
        # during unpacking and left it on the disk (e.g. upx).
        subprocess.call(["rm","-f",str(OUT.val)+".tmp"],shell=True)
        Make("CONTINUE").setValue(0)
if (str(FINAL_RC.val) == "-1" ):
    exit(int(RC.val))
else:
    exit(int(FINAL_RC.val))
