#! /usr/bin/env python
from __future__ import print_function
import sys,os,subprocess,glob
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
# Generates 1 JSON for C standard library and 1 for other C header files in
# /usr/include.
#
# On macOS, we want the GNU version of 'readlink', which is available under
# 'greadlink':
def gnureadlink () :
    if (subprocess.call("hash" + " " + "greadlink",shell=True,stderr=file("/dev/null",'wb')) ):
        subprocess.call(["greadlink",Str(Expand.at())],shell=True)
    else:
        subprocess.call(["readlink",Str(Expand.at())],shell=True)

#
# C standard library headers.
#
CSTDLIB_HEADERS=Bash2Py("(assert.h complex.h ctype.h errno.h fenv.h float.h inttypes.h iso646.h limits.h locale.h math.h setjmp.h signal.h stdalign.h stdarg.h stdatomic.h stdbool.h stddef.h stdint.h stdio.h stdlib.h stdnoreturn.h string.h tgmath.h threads.h time.h uchar.h wchar.h wctype.h)")
#
# Files we don't want in JSONs.
#
FILES_PATTERNS_TO_FILTER_OUT=Bash2Py(Glob("(GL/ Qt.*/ SDL.*/ X11/ alsa/ c\\+\\+/ dbus.*/ glib.*/ libdrm/ libxml2/ llvm.*/ mirclient/ php[0-9.-]*/ pulse/ python.*/ ruby.*/ wayland.*/ xcb/)"))
SEP=Bash2Py("\\|")
FILES_FILTER=Bash2Py(os.popen("printf \""+str(SEP.val)+"%s\" \""+str(FILES_PATTERNS_TO_FILTER_OUT.val[@] ])+"\"").read().rstrip("\n"))
FILES_FILTER=Bash2Py(FILES_FILTER.val:Expand.hash()SEP)
#
# Paths.
#
SCRIPT_DIR=Bash2Py(os.popen("dirname \""+os.popen("gnureadlink -e \""+__file__+"\"").read().rstrip("\n")+"\"").read().rstrip("\n"))
SCRIPT_NAME=Bash2Py(os.popen("basename \""+str(SCRIPT_NAME.val)+"\"").read().rstrip("\n"))
EXTRACTOR=Bash2Py(str(SCRIPT_DIR.val)+"/extract_types.py")
MERGER=Bash2Py(str(SCRIPT_DIR.val)+"/merge_jsons.py")
INCLUDE_DIR=Bash2Py("/usr/include/")
OUT_DIR=Bash2Py(".")
STD_LIB_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/gen_tmp_cstdlib")
STD_LIB_JSON=Bash2Py(str(OUT_DIR.val)+"/cstdlib.json")
LINUX_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/gen_tmp_linux")
LINUX_JSON=Bash2Py(str(OUT_DIR.val)+"/linux.json")
CSTDLIB_PRIORITY_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/gen_tmp_cstdlib_priority")
LINUX_PRIORITY_OUT_DIR=Bash2Py(str(OUT_DIR.val)+"/gen_tmp_linux_priority")
#
# Print help.
#
def print_help () :
    global SCRIPT_NAME

    print("Generator of JSON files containing C-types information for C standard library")
    print("and other header files in /usr/include/ directory.")
    print()
    print("Usage:")
    print("    "+str(SCRIPT_NAME.val)+" [OPTIONS]")
    print()
    print("Options:")
    print("    -f    --files-filter       Pattern to ignore specific header files.")
    print("    -h,   --help               Print this help message.")
    print("    -i    --json-indent N      Set indentation in JSON files. Default 1")
    print("    -N    --no-cleanup         Do not remove dirs with JSONs for individual header files.")
    print("          --cstdlib-headers    Set path to the C standard library headers with high-priority types info.")
    print("          --linux-headers      Set path to the Linux headers with high-priority types info.")

#
# Prints the given error message ($1) to stderr and exits.
#
def print_error_and_die (_p1) :
    print("Error: "+str(_p1),stderr=subprocess.STDOUT)
    exit(1)

#
# Parse and check script arguments.
#
GETOPT_SHORTOPT=Bash2Py("f:hi:Np:")
GETOPT_LONGOPT=Bash2Py("cstdlib-headers:,files-filter:,help,json-indent:,linux-headers:,no-cleanup")
PARSED_OPTIONS=Bash2Py(os.popen("getopt -o \""+str(GETOPT_SHORTOPT.val)+"\" -l \""+str(GETOPT_LONGOPT.val)+"\" -n \""+str(SCRIPT_NAME.val)+"\" -- \""+Str(Expand.at())+"\"").read().rstrip("\n"))
if (_rc0 != 0 ):
    print_error_and_die("Failed to parse parameters via getopt")
eval("set","--",str(PARSED_OPTIONS.val))
while (True):
    
    if ( str(sys.argv[1]) == '-f' or str(sys.argv[1]) == '--files-filter'):
        Make("FILES_FILTER").setValue(str(FILES_FILTER.val)+"\|"+str(sys.argv[2]))
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-i' or str(sys.argv[1]) == '--json-indent'):
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
    elif ( str(sys.argv[1]) == '--cstdlib-headers'):
        if str(CSTDLIB_PRIORITY_PATH.val) != '':
            print_error_and_die("Duplicate option: --cstdlib-headers")
        if not os.path.isdir(str(sys.argv[2])):
            print_error_and_die("Unknown directory: "+str(sys.argv[2]))
        Make("CSTDLIB_PRIORITY_PATH").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--linux-headers'):
        if str(LINUX_PRIORITY_PATH.val) != '':
            print_error_and_die("Duplicate option: --linux-headers")
        if not os.path.isdir(str(sys.argv[2])):
            print_error_and_die("Unknown directory: "+str(sys.argv[2]))
        Make("LINUX_PRIORITY_PATH").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '--'):
        if (Expand.hash() != 1 ):
            print_error_and_die("Unrecognized parameter '"+str(sys.argv[2])+"'")
            exit(1)
        break
JSON_INDENT=Bash2Py(Expand.colonEq("JSON_INDENT","1"))
CLEANUP=Bash2Py(Expand.colonEq("CLEANUP","yes"))
#
# Initial cleanup.
#
_rc0 = subprocess.call(["rm","-rf",str(STD_LIB_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir",str(STD_LIB_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["rm","-rf",str(LINUX_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir",str(LINUX_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["rm","-rf",str(CSTDLIB_PRIORITY_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir",str(CSTDLIB_PRIORITY_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["rm","-rf",str(LINUX_PRIORITY_OUT_DIR.val)],shell=True)
_rc0 = subprocess.call(["mkdir",str(LINUX_PRIORITY_OUT_DIR.val)],shell=True)
#
# Generate JSONs for whole /usr/include path.
# Filter out unwanted headers.
# Move standard headers to other dir.
#
_rc0 = subprocess.call([str(EXTRACTOR.val),str(INCLUDE_DIR.val),"-o",str(LINUX_OUT_DIR.val)],shell=True)
FILES_FILTER=Bash2Py(FILES_FILTER.val//\//_)
_rc0 = subprocess.call(["find",str(LINUX_OUT_DIR.val)+"/","-regex",str(LINUX_OUT_DIR.val)+"/.*\("+str(FILES_FILTER.val)+"\).*","-delete"],shell=True)
#
# Move standard library headers to other directory.
# Edit standard header paths to look like type-extractor generated jsons.
#
for Make("header").val in Array(CSTDLIB_HEADERS.val[@] ]):
    for Make("f").val in Array(os.popen("find \""+str(INCLUDE_DIR.val)+"\" -name \""+str(header.val)+"\"").read().rstrip("\n")):
        Make("f").setValue(f.val#INCLUDE_DIR.val)
        Make("f").setValue(f.val////_)
        Make("f").setValue(f.val/%\.h/.json)
        if (os.path.isfile(str(LINUX_OUT_DIR.val)+"/"+str(f.val)) ):
            subprocess.call(["mv",str(LINUX_OUT_DIR.val)+"/"+str(f.val),str(STD_LIB_OUT_DIR.val)],shell=True)
#
# Extract types info from high-priority cstdlib and linux headers if paths were given.
#
if (str(CSTDLIB_PRIORITY_PATH.val) != '' ):
    subprocess.call([str(EXTRACTOR.val),str(CSTDLIB_PRIORITY_PATH.val),"-o",str(CSTDLIB_PRIORITY_OUT_DIR.val)],shell=True)
if (str(LINUX_PRIORITY_PATH.val) != '' ):
    subprocess.call([str(EXTRACTOR.val),str(LINUX_PRIORITY_PATH.val),"-o",str(LINUX_PRIORITY_OUT_DIR.val)],shell=True)
#
# Merging.
# Priority headers must be first.
# Cstdlib priority headers are merged to the C standard library JSON,
# Linux priority headers to the Linux JSON.
#
_rc0 = subprocess.call([str(MERGER.val),str(CSTDLIB_PRIORITY_OUT_DIR.val),str(STD_LIB_OUT_DIR.val),"-o",str(STD_LIB_JSON.val),"--json-indent",str(JSON_INDENT.val)],shell=True)
_rc0 = subprocess.call([str(MERGER.val),str(LINUX_PRIORITY_OUT_DIR.val),str(LINUX_OUT_DIR.val),"-o",str(LINUX_JSON.val),"--json-indent",str(JSON_INDENT.val)],shell=True)
#
# Optional cleanup at the end.
#
if (str(CLEANUP.val) == "yes" ):
    subprocess.call(["rm","-rf",str(STD_LIB_OUT_DIR.val)],shell=True)
    subprocess.call(["rm","-rf",str(LINUX_OUT_DIR.val)],shell=True)
    subprocess.call(["rm","-rf",str(PRIORITY_HEADERS_OUT_DIR.val)],shell=True)
    subprocess.call(["rm","-rf",str(CSTDLIB_PRIORITY_OUT_DIR.val)],shell=True)
    subprocess.call(["rm","-rf",str(LINUX_PRIORITY_OUT_DIR.val)],shell=True)
