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
# Generates JSON files from includes in Windows SDK and Windows Drivers Kit.
#
# On macOS, we want the GNU version of 'readlink', which is available under
# 'greadlink':
def gnureadlink () :
    if (subprocess.call("hash" + " " + "greadlink",shell=True,stderr=file("/dev/null",'wb')) ):
        subprocess.call(["greadlink",Str(Expand.at())],shell=True)
    else:
        subprocess.call(["readlink",Str(Expand.at())],shell=True)

#
# Paths.
#
SCRIPT_DIR=Bash2Py(os.popen("dirname \""+os.popen("gnureadlink -e \""+__file__+"\"").read().rstrip("\n")+"\"").read().rstrip("\n"))
SCRIPT_NAME=Bash2Py(os.popen("basename \""+str(SCRIPT_NAME.val)+"\"").read().rstrip("\n"))
EXTRACTOR=Bash2Py(str(SCRIPT_DIR.val)+"/extract_types.py")
MERGER=Bash2Py(str(SCRIPT_DIR.val)+"/merge_jsons.py")
OUT_DIR=Bash2Py(".")
#
# Windows SDK paths.
#
WIN_UCRT_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windows_ucrt")
WIN_SHARED_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windows_shared")
WIN_UM_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windows_um")
WIN_WINRT_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windows_winrt")
WIN_NETFX_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windows_netfx")
WIN_OUT_JSON=Bash2Py(str(OUT_DIR.val)+"/windows.json")
WIN_OUT_JSON_WITH_UNUSED_TYPES=Bash2Py(str(OUT_DIR.val)+"/windows_all_types.json")
#
# Windows Drivers Kit paths.
#
WDK_KM_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windrivers_km")
WDK_MMOS_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windrivers_mmos")
WDK_SHARED_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windrivers_shared")
WDK_UM_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windrivers_um")
WDK_KMDF_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windrivers_kmdf")
WDK_UMDF_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/windrivers_umdf")
WDK_OUT_JSON=Bash2Py(str(OUT_DIR.val)+"/windrivers.json")
#
# Prints help.
#
def print_help () :
    global SCRIPT_NAME

    print("Generates JSON files from includes in Windows SDK and Windows Drivers Kit.")
    print()
    print("Usage:")
    print("    "+str(SCRIPT_NAME.val)+" [OPTIONS] --sdk WIN_SDK_DIR --wdk WDK_DIR")
    print()
    print("Options:")
    print("    -h,   --help               Print this help message.")
    print("    -i    --json-indent N      Set indentation in JSON files. Default 1")
    print("    -N    --no-cleanup         Do not remove dirs with JSONs for individual header files.")

#
# Prints the given error message ($1) to stderr and exits.
#
def print_error_and_die (_p1) :
    print("Error: "+str(_p1),stderr=subprocess.STDOUT)
    exit(1)

#
# Removes temporary dirs and files used to generate JSONS that are merged later.
#
def remove_tmp_dirs_and_files () :
    global WIN_UCRT_OUT_DIR
    global WIN_SHARED_OUT_DIR
    global WIN_UM_OUT_DIR
    global WIN_WINRT_OUT_DIR
    global WIN_NETFX_OUT_DIR
    global WIN_OUT_JSON_WITH_UNUSED_TYPES
    global WDK_KM_OUT_DIR
    global WDK_MMOS_OUT_DIR
    global WDK_SHARED_OUT_DIR
    global WDK_UM_OUT_DIR
    global WDK_KMDF_OUT_DIR
    global WDK_UMDF_OUT_DIR

    subprocess.call(["rm","-rf",str(WIN_UCRT_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WIN_SHARED_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WIN_UM_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WIN_WINRT_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WIN_NETFX_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-f",str(WIN_OUT_JSON_WITH_UNUSED_TYPES.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WDK_KM_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WDK_MMOS_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WDK_SHARED_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WDK_UM_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WDK_KMDF_OUT_DIR.val)],shell=True)
    _rc0 = subprocess.call(["rm","-rf",str(WDK_UMDF_OUT_DIR.val)],shell=True)

#
# Parse and check script arguments.
#
GETOPT_SHORTOPT=Bash2Py("hi:N")
GETOPT_LONGOPT=Bash2Py("help,json-indent:,no-cleanup,sdk:,wdk:")
PARSED_OPTIONS=Bash2Py(os.popen("getopt -o \""+str(GETOPT_SHORTOPT.val)+"\" -l \""+str(GETOPT_LONGOPT.val)+"\" -n \""+str(SCRIPT_NAME.val)+"\" -- \""+Str(Expand.at())+"\"").read().rstrip("\n"))
if (_rc0 != 0 ):
    print_error_and_die("Failed to parse parameters via getopt")
eval("set","--",str(PARSED_OPTIONS.val))
while (True):
    
    if ( str(sys.argv[1]) == '-i' or str(sys.argv[1]) == '--json-indent'):
        if str(JSON_INDENT.val) != '':
            print_error_and_die("Duplicate option: -i|--json-indent")
        Make("JSON_INDENT").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help'):
        print_help()
        exit(0)
    elif ( str(sys.argv[1]) == '-N' or str(sys.argv[1]) == '--no-cleanup'):
        if str(CLEANUP.val) != '':
            print_error_and_die("Duplicate option: -N|--no-cleanup")
        Make("CLEANUP").setValue("no")
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--sdk'):
        Make("WIN_SDK_DIR").setValue(sys.argv[2])
        if (not os.access(str(WIN_SDK_DIR.val),R_OK) ):
            print_error_and_die(str(WIN_SDK_DIR.val)+": No such file or directory")
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--wdk'):
        Make("WDK_DIR").setValue(sys.argv[2])
        if (not os.access(str(WDK_DIR.val),R_OK) ):
            print_error_and_die(str(WDK_DIR.val)+": No such file or directory")
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--'):
        if (Expand.hash() != 1 ):
            print_error_and_die("Invalid options: '"+str(sys.argv[2])+"'")
            exit(1)
        break
CLEANUP=Bash2Py(Expand.colonEq("CLEANUP","yes"))
JSON_INDENT=Bash2Py(Expand.colonEq("JSON_INDENT","1"))
# Path to the Windows SDK directory is required.
if (if not str(WIN_SDK_DIR.val) == '':
    str(WDK_DIR.val) == '' ):
    print_help()
    exit(1)
WIN_UCRT_IN_DIR=Bash2Py(str(WIN_SDK_DIR.val)+"/10/Include/10.0.10150.0/ucrt")
WIN_SHARED_IN_DIR=Bash2Py(str(WIN_SDK_DIR.val)+"/10/Include/10.0.10240.0/shared")
WIN_UM_IN_DIR=Bash2Py(str(WIN_SDK_DIR.val)+"/10/Include/10.0.10240.0/um")
WIN_WINRT_IN_DIR=Bash2Py(str(WIN_SDK_DIR.val)+"/10/Include/10.0.10240.0/winrt")
WIN_NETFX_IN_DIR=Bash2Py(str(WIN_SDK_DIR.val)+"/NETFXSDK/4.6/Include/um")
WDK_KM_IN_DIR=Bash2Py(str(WDK_DIR.val)+"/10.0.10586.0/km")
WDK_MMOS_IN_DIR=Bash2Py(str(WDK_DIR.val)+"/10.0.10586.0/mmos")
WDK_SHARED_IN_DIR=Bash2Py(str(WDK_DIR.val)+"/10.0.10586.0/shared")
WDK_UM_IN_DIR=Bash2Py(str(WDK_DIR.val)+"/10.0.10586.0/um")
WDK_KMDF_IN_DIR=Bash2Py(str(WDK_DIR.val)+"/wdf/kmdf")
WDK_UMDF_IN_DIR=Bash2Py(str(WDK_DIR.val)+"/wdf/umdf")
#
# Initial cleanup.
#
remove_tmp_dirs_and_files()
_rc0 = subprocess.call(["mkdir","-p",str(WIN_UCRT_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WIN_SHARED_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WIN_UM_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WIN_WINRT_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WIN_NETFX_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WDK_KM_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WDK_MMOS_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WDK_SHARED_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WDK_UM_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WDK_KMDF_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir","-p",str(WDK_UMDF_OUT_DIR.val)],shell=True)
#
# Parse the includes in the given Windows SDK directory and merge the generated
# JSON files.
#
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WIN_UCRT_IN_DIR.val),"-o",str(WIN_UCRT_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WIN_SHARED_IN_DIR.val),"-o",str(WIN_SHARED_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WIN_UM_IN_DIR.val),"-o",str(WIN_UM_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WIN_WINRT_IN_DIR.val),"-o",str(WIN_WINRT_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WIN_NETFX_IN_DIR.val),"-o",str(WIN_NETFX_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(MERGER.val),str(WIN_SHARED_OUT_DIR.val),str(WIN_UM_OUT_DIR.val),str(WIN_UCRT_OUT_DIR.val),str(WIN_WINRT_OUT_DIR.val),str(WIN_NETFX_OUT_DIR.val),"-o",str(WIN_OUT_JSON.val),"--json-indent",str(JSON_INDENT.val)],shell=True)
#
# Parse the includes in the given WDK directory and merge the generated
# JSON files.
#
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WDK_KM_IN_DIR.val),"-o",str(WDK_KM_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WDK_MMOS_IN_DIR.val),"-o",str(WDK_MMOS_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WDK_SHARED_IN_DIR.val),"-o",str(WDK_SHARED_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(EXTRACTOR.val),str(WDK_UM_IN_DIR.val),"-o",str(WDK_UM_OUT_DIR.val)],shell=True)
for Make("dir").val in Array(os.popen("ls "+str(WDK_KMDF_IN_DIR.val)).read().rstrip("\n")):
    subprocess.call([str(EXTRACTOR.val),str(WDK_KMDF_IN_DIR.val)+"/"+str(dir.val),"-o",str(WDK_KMDF_OUT_DIR.val)],shell=True)
for Make("dir").val in Array(os.popen("ls "+str(WDK_UMDF_IN_DIR.val)).read().rstrip("\n")):
    subprocess.call([str(EXTRACTOR.val),str(WDK_UMDF_IN_DIR.val)+"/"+str(dir.val),"-o",str(WDK_UMDF_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call([str(MERGER.val),str(WDK_SHARED_OUT_DIR.val),str(WDK_UM_OUT_DIR.val),str(WDK_KM_OUT_DIR.val),str(WDK_MMOS_OUT_DIR.val),str(WDK_KMDF_OUT_DIR.val),str(WDK_UMDF_OUT_DIR.val),"-o",str(WDK_OUT_JSON.val),"--json-indent",str(JSON_INDENT.val)],shell=True)
#
# WDK uses many types defined in Windows SDK. We need SDK JSON with all types extracted
# and merge it with WDK. SDK functions must be removed!
#
_rc0 = subprocess.call([str(MERGER.val),str(WIN_SHARED_OUT_DIR.val),str(WIN_UM_OUT_DIR.val),str(WIN_UCRT_OUT_DIR.val),str(WIN_WINRT_OUT_DIR.val),str(WIN_NETFX_OUT_DIR.val),"-o",str(WIN_OUT_JSON_WITH_UNUSED_TYPES.val),"--json-indent",str(JSON_INDENT.val),"--keep-unused-types"],shell=True)
if (int(JSON_INDENT.val) == 0 ):
    subprocess.call(["sed","-i","-e","s/^.*\}, \"types\": \{/\{\"functions\": \{\}, \"types\": \{/",str(WIN_OUT_JSON_WITH_UNUSED_TYPES.val)],shell=True)
else:
    Make("TYPES_LINE_NUMBER").setValue(os.popen("egrep -n \"^s*"types": {\" \""+str(WIN_OUT_JSON_WITH_UNUSED_TYPES.val)+"\" | cut -f1 -d:").read().rstrip("\n"))
    Make("TYPES_LINE_NUMBER").setValue((TYPES_LINE_NUMBER.val - 1))
    subprocess.call(["sed","-i","-e","1,"+str(TYPES_LINE_NUMBER.val)+" d",str(WIN_OUT_JSON_WITH_UNUSED_TYPES.val)],shell=True)
    subprocess.call(["sed","-i","-e","1s/^/\{\"functions\": \{\},\n/",str(WIN_OUT_JSON_WITH_UNUSED_TYPES.val)],shell=True)
_rc0 = subprocess.call([str(MERGER.val),str(WDK_OUT_JSON.val),str(WIN_OUT_JSON_WITH_UNUSED_TYPES.val),"-o",str(WDK_OUT_JSON.val),"--json-indent",str(JSON_INDENT.val)],shell=True)
#
# Optional cleanup at the end.
#
if (str(CLEANUP.val) == "yes" ):
    remove_tmp_dirs_and_files()
