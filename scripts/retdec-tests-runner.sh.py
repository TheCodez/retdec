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

#
# Runs all the installed unit tests.
#
# On macOS, we want the GNU version of 'readlink', which is available under
# 'greadlink':
def gnureadlink () :
    if (subprocess.call("hash" + " " + "greadlink",shell=True,stderr=file("/dev/null",'wb')) ):
        subprocess.call(["greadlink",Str(Expand.at())],shell=True)
    else:
        subprocess.call(["readlink",Str(Expand.at())],shell=True)

SCRIPT_DIR=Bash2Py(os.popen("dirname \""+os.popen("gnureadlink -e \""+__file__+"\"").read().rstrip("\n")+"\"").read().rstrip("\n"))
if (str(DECOMPILER_CONFIG.val) == '' ):
    Make("DECOMPILER_CONFIG").setValue(str(SCRIPT_DIR.val)+"/retdec-config.sh")
_rc0 = subprocess.call([".",str(DECOMPILER_CONFIG.val)],shell=True)
#
# First argument can be verbose.
#
if (if not str(sys.argv[1]) == "-v":
    str(sys.argv[1]) == "--verbose" ):
    Make("VERBOSE").setValue(1)
#
# Emits a colored version of the given message to the standard output (without
# a new line).
#
# 2 string argument are needed:
#    $1 message to be colored
#    $2 color (red, green, yellow)
#
# If the color is unknown, it emits just $1.
#
def echo_colored (_p1,_p2) :
    # Check the number of arguments.
    if (str(Expand.hash()) != "2" ):
        return
    
    if ( str(_p2) == 'red'):
        print( "\033[22;31m"+str(_p1)+"\033[0m" )
    
    elif ( str(_p2) == 'green'):
        print( "\033[22;32m"+str(_p1)+"\033[0m" )
    
    elif ( str(_p2) == 'yellow'):
        print( "\033[01;33m"+str(_p1)+"\033[0m" )
    
    else:
        print( str(_p1)+"\n" )
    

#
# Prints paths to all unit tests in the given directory.
#
# 1 string argument is needed:
#     $1 path to the directory with unit tests
#
def unit_tests_in_dir (_p1) :
    global OSTYPE
    global EXECUTABLE_FLAG

    # On macOS, find does not support the '-executable' parameter (#238).
    # Therefore, on macOS, we have to use '-perm +111'. To explain, + means
    # "any of these bits" and 111 is the octal representation for the
    # executable bit on owner, group, and other. Unfortunately, we cannot use
    # '-perm +111' on all systems because find on Linux/MSYS2 does not support
    # +. It supports only /, but this is not supported by find on macOS...
    # Hence, we need an if.
    # Note: $OSTYPE below is a Bash variable.
    if (str(OSTYPE.val) == Str(Glob("darwin*")) ):
        Make("EXECUTABLE_FLAG").setValue("-perm +111")
    else:
        Make("EXECUTABLE_FLAG").setValue("-executable")
    _rc0 = _rcr2, _rcw2 = os.pipe()
    if os.fork():
        os.close(_rcw2)
        os.dup2(_rcr2, 0)
        _rcr3, _rcw3 = os.pipe()
        if os.fork():
            os.close(_rcw3)
            os.dup2(_rcr3, 0)
            subprocess.call(["sort"],shell=True)
        else:
            os.close(_rcr3)
            os.dup2(_rcw3, 1)
            subprocess.call(["grep","-v","\\.sh$"],shell=True)
            sys.exit(0)
        
    else:
        os.close(_rcr2)
        os.dup2(_rcw2, 1)
        subprocess.call(["find",str(_p1),"-name","retdec-tests-*","-type","f",str(EXECUTABLE_FLAG.val)],shell=True)
        sys.exit(0)
    

#
# Runs all unit tests in the given directory.
#
# 1 string argument is needed:
#     $1 path to the directory with unit tests
#
# Returns 0 if all tests passed, 1 otherwise.
#
def run_unit_tests_in_dir (_p1) :
    global UNIT_TESTS_DIR
    global TESTS_FAILED
    global TESTS_RUN
    global unit_test_name
    global unit_test
    global VERBOSE
    global RC
    global PIPESTATUS

    Make("UNIT_TESTS_DIR").setValue(_p1)
    TESTS_FAILED=Bash2Py(0)
    TESTS_RUN=Bash2Py(0)
    for Make("unit_test").val in Array(os.popen("unit_tests_in_dir \""+str(UNIT_TESTS_DIR.val)+"\"").read().rstrip("\n")):
        print()
        Make("unit_test_name").setValue(os.popen("sed 's/^.*/bin///' <<< \""+str(unit_test.val)+"\"").read().rstrip("\n"))
        echo_colored(unit_test_name.val, "yellow")
        print()
        if (str(VERBOSE.val) != '' ):
            subprocess.call([str(unit_test.val),"--gtest_color=yes"],shell=True)
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
                        subprocess.call(["grep","-v","Running main() from gmock_main.cc"],shell=True)
                    else:
                        os.close(_rcr9)
                        os.dup2(_rcw9, 1)
                        subprocess.call(["grep","-v","^"+"$"],shell=True)
                        sys.exit(0)
                    
                else:
                    os.close(_rcr8)
                    os.dup2(_rcw8, 1)
                    subprocess.call(["grep","-v","RUN\|OK\|----------\|=========="],shell=True)
                    sys.exit(0)
                
            else:
                os.close(_rcr7)
                os.dup2(_rcw7, 1)
                subprocess.call([str(unit_test.val),"--gtest_color=yes"],shell=True)
                sys.exit(0)
        
        Make("RC").setValue(PIPESTATUS.val[0] ])
        if (str(RC.val) != "0" ):
            Make("TESTS_FAILED").setValue(1)
            if (int(RC.val) >= 127 ):
                # Segfault, floating-point exception, etc.
                echo_colored("FAILED (return code "+str(RC.val)+")\n", "red")
        Make("TESTS_RUN").setValue(1)
    if (if not str(TESTS_FAILED.val) == "1":
        str(TESTS_RUN.val) == "0" ):
        return(1)
    else:
        return(0)

#
# Run all binaries in unit test dir.
#
if (not os.path.isdir(str(UNIT_TESTS_DIR.val)) ):
    print("error: no unit tests found in "+str(UNIT_TESTS_DIR.val),stderr=subprocess.STDOUT)
    exit(1)
print("Running all unit tests in "+str(UNIT_TESTS_DIR.val)+" ...")
run_unit_tests_in_dir(UNIT_TESTS_DIR.val)
