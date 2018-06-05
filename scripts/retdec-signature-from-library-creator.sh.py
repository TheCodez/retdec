#! /usr/bin/env python
from __future__ import print_function
import sys,os,subprocess
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

class Expand(object):
  @staticmethod
  def at():
    if (len(sys.argv) < 2):
      return []
    return  sys.argv[1:]
  @staticmethod
  def hash():
    return  len(sys.argv)-1

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
##
## Prints help to stream $1.
##
def print_help (_p1) :
    print("Create Yara rules file from static libraries.",file=file(str(_p1),'wb'))
    print("Usage: "+__file__+" [OPTIONS] -o OUTPUT INPUT_1 [... INPUT_N]\n",file=file(str(_p1),'wb'))
    print("Options:",file=file(str(_p1),'wb'))
    print("    -n --no-cleanup",file=file(str(_p1),'wb'))
    print("        Temporary .pat files will be kept.",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))
    print("    -o --output path",file=file(str(_p1),'wb'))
    print("        Where result(s) will be stored.",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))
    print("    -m --min-pure unsigned",file=file(str(_p1),'wb'))
    print("        Minimum pure information needed for patterns (default 16).",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))
    print("    -i --ignore-nops opcode",file=file(str(_p1),'wb'))
    print("        Ignore trailing NOPs when computing (pure) size.",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))
    print("    -l --logfile",file=file(str(_p1),'wb'))
    print("        Add log-file with '.log' suffix from pat2yara.",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))
    print("    -b --bin2pat-only",file=file(str(_p1),'wb'))
    print("        Stop after bin2pat.",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))

##
## Exit with error message $1 and clean up temporary files.
##
def die_with_error_and_cleanup (_p1) :
    global NO_CLEANUP

    # Cleanup.
    if not str(NO_CLEANUP.val) != '':
        subprocess.call(["temporary_files_cleanup"],shell=True)
    _rc0 = subprocess.call(["print_error_and_die",str(_p1)+"."],shell=True)

##
## Removes temporary files.
##
def temporary_files_cleanup () :
    global DIR_PATH

    subprocess.call(["rm","-r",str(DIR_PATH.val)],shell=True)

# Parse arguments.
while (Expand.hash() > 0):
    
    if ( str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help'):
        print_help("/dev/stdout")
        exit(0)
    elif ( str(sys.argv[1]) == '-n' or str(sys.argv[1]) == '--no-cleanup'):
        Make("NO_CLEANUP").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '-l' or str(sys.argv[1]) == '--logfile'):
        Make("DO_LOGFILE").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '-b' or str(sys.argv[1]) == '--bin2pat-only'):
        Make("BIN2PAT_ONLY").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '-m' or str(sys.argv[1]) == '--min-pure'):
        if str(MIN_PURE.val) != '':
            die_with_error_and_cleanup("duplicate option: --min-pure")
        Make("MIN_PURE").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-i' or str(sys.argv[1]) == '--ignore-nops'):
        if str(IGNORE_NOP.val) != '':
            die_with_error_and_cleanup("duplicate option: --ignore-nops")
        Make("IGNORE_NOP").setValue("--ignore-nops")
        Make("IGNORE_OPCODE").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-o' or str(sys.argv[1]) == '--output'):
        if str(OUT_PATH.val) != '':
            die_with_error_and_cleanup("duplicate option: --output")
        Make("OUT_PATH").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    else:
        if  not (os.path.isfile(str(sys.argv[1]))):
            die_with_error_and_cleanup("input '"+str(sys.argv[1])+"' is not a valid file nor argument")
        Make("INPUT_LIBS").setValue("("+str(sys.argv[1])+")")
        subprocess.call(["shift"],shell=True)
# Check inputs.
if (Expand.hash()INPUT_LIBS[@] < 1 ):
    die_with_error_and_cleanup("no input files")
# Output directory - compulsory argument.
if (str(OUT_PATH.val) == '' ):
    die_with_error_and_cleanup("option -o|--output is compulsory")
else:
    Make("FILE_PATH").setValue(OUT_PATH.val)
    Make("DIR").setValue(os.popen("dirname \""+os.popen("get_realpath \""+str(FILE_PATH.val)+"\"").read().rstrip("\n")+"\"").read().rstrip("\n"))
    Make("DIR_PATH").setValue(os.popen("mktemp -d \""+str(DIR.val)+"/XXXXXXXXX\"").read().rstrip("\n"))
# Set default --min-pure information argument.
if ( not (str(MIN_PURE.val) != '') ):
    Make("MIN_PURE").setValue(16)
# Create .pat files for every library.
for Make("LIB_PATH").val in Array(INPUT_LIBS.val[@] ]):
    # Check for invalid archives.
    if (not subprocess.call(["is_valid_archive",str(LIB_PATH.val)],shell=True) ):
        print("ignoring file '"+str(LIB_PATH.val)+"' - not valid archive")
        continue
    # Get library name for .pat file.
    Make("LIB_NAME_TMP").setValue(os.popen("basename \""+str(LIB_PATH.val)+"\"").read().rstrip("\n"))
    Make("LIB_NAME").setValue(LIB_NAME_TMP.val%%.*)
    # Create sub-directory for object files.
    Make("OBJECT_DIRECTORY").setValue(str(DIR_PATH.val)+"/"+str(LIB_NAME.val)+"-objects")
    Make("OBJECT_DIRECTORIES").setValue("("+str(OBJECT_DIRECTORY.val)+")")
    subprocess.call(["mkdir",str(OBJECT_DIRECTORY.val)],shell=True)
    # Extract all files to temporary folder.
    subprocess.call([str(AR.val),str(LIB_PATH.val),"--extract","--output",str(OBJECT_DIRECTORY.val)],shell=True)
    # List all extracted objects.
    Make("IFS_OLD").setValue(IFS.val)
    Make("IFS").setValue("\n")
    Make("OBJECTS").setValue("("+os.popen("find \""+str(OBJECT_DIRECTORY.val)+"\" -type f").read().rstrip("\n")+")")
    Make("IFS").setValue(IFS_OLD.val)
    # Extract patterns from library.
    Make("PATTERN_FILE").setValue(str(DIR_PATH.val)+"/"+str(LIB_NAME.val)+".pat")
    Make("PATTERN_FILES").setValue("("+str(PATTERN_FILE.val)+")")
    subprocess.call([str(BIN2PAT.val),"-o",str(PATTERN_FILE.val),str(OBJECTS.val[@] ])],shell=True)
    if _rc0 != 0:
        die_with_error_and_cleanup("utility bin2pat failed when processing '"+str(LIB_PATH.val)+"'")
    # Remove extracted objects continuously.
    if not str(NO_CLEANUP.val) != '':
        subprocess.call(["rm","-r",str(OBJECT_DIRECTORY.val)],shell=True)
# Skip second step - only .pat files will be created.
if (str(BIN2PAT_ONLY.val) != '' ):
    if not str(NO_CLEANUP.val) != '':
        subprocess.call(["rm","-f",str(OBJECT_DIRECTORIES.val[@] ])],shell=True)
    exit(0)
# Create final .yara file from .pat files.
if (str(DO_LOGFILE.val) != '' ):
    subprocess.call([str(PAT2YARA.val),str(PATTERN_FILES.val[@] ]),"--min-pure",str(MIN_PURE.val),"-o",str(FILE_PATH.val),"-l",str(FILE_PATH.val)+".log",str(IGNORE_NOP.val),str(IGNORE_OPCODE.val)],shell=True)
    if _rc0 != 0:
        die_with_error_and_cleanup("utility pat2yara failed")
else:
    subprocess.call([str(PAT2YARA.val),str(PATTERN_FILES.val[@] ]),"--min-pure",str(MIN_PURE.val),"-o",str(FILE_PATH.val),str(IGNORE_NOP.val),str(IGNORE_OPCODE.val)],shell=True)
    if _rc0 != 0:
        die_with_error_and_cleanup("utility pat2yara failed")
# Do cleanup.
if not str(NO_CLEANUP.val) != '':
    temporary_files_cleanup()
