#! /usr/bin/env python
from __future__ import print_function
import sys,os,subprocess,glob,re
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
# Compilation and decompilation utility functions.
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
# On macOS, 'timeout' from GNU coreutils is by default available under
# 'gtimeout'.
def gnutimeout () :
    if (subprocess.call("hash" + " " + "gtimeout",shell=True,stderr=file("/dev/null",'wb')) ):
        subprocess.call(["gtimeout",Str(Expand.at())],shell=True)
    else:
        subprocess.call(["timeout",Str(Expand.at())],shell=True)

#
# Prints the real, physical location of a directory or file, relative or
# absolute.
# 1 argument is needed
#
def get_realpath (_p1) :

    Make("input_path").setValue(_p1)
    # Use cygpath.exe on cygwin, due to cygwins virtual folder mountpoints
    # (i.e., "/cygdrive/c/foo/bar" becomes "c:/foo/bar").
    # cygpath args:
    #   -m -- mixed mode, that is, forward slashes, instead of backward slashes
    #   -a -- absolute path (regardless if input is relative or not)
    if (os.popen("uname -s").read().rstrip("\n") == Str(Glob("*CYGWIN*")) ):
        subprocess.call(["cygpath","-ma",str(input_path.val)],shell=True)
    else:
        gnureadlink("-f", input_path.val)

#
# Print error message to stderr and die.
# 1 argument is needed
# Returns - 1 if number of arguments is incorrect
#
def print_error_and_die (_p1) :
    if (str(Expand.hash()) != "1" ):
        exit(1)
    print("Error: "+str(_p1),stderr=subprocess.STDOUT)
    exit(1)

#
# Print warning message to stderr.
# 1 argument is needed
# Returns - 1 if number of arguments is incorrect
#
def print_warning (_p1) :
    if (str(Expand.hash()) != "1" ):
        return(1)
    print("Warning: "+str(_p1),stderr=subprocess.STDOUT)
    return(0)

#
# Check if file has any ar signature.
# 1 argument is needed - file path
# Returns - 0 if file has ar signature
#           1 if number of arguments is incorrect
#           2 no signature
#
def has_archive_signature (_p1) :
    global AR

    if (str(Expand.hash()) != "1" ):
        return(1)
    if subprocess.call([str(AR.val),str(_p1),"--arch-magic"],shell=True):
        return(0)
    return(2)

#
# Check if file has thin ar signature.
# 1 argument is needed - file path
# Returns - 0 if file has thin ar signature
#           1 if number of arguments is incorrect
#           2 no signature
#
def has_thin_archive_signature (_p1) :
    global AR

    if (str(Expand.hash()) != "1" ):
        return(1)
    if subprocess.call([str(AR.val),str(_p1),"--thin-magic"],shell=True):
        return(0)
    return(2)

#
# Check if file is an archive we can work with.
# 1 argument is needed - file path
# Returns - 0 if file is valid archive
#           1 if file is invalid archive
#
def is_valid_archive (_p1) :
    global AR
    global DEV_NULL

    if (str(Expand.hash()) != "1" ):
        return(1)
    # We use our own messages so throw original output away.
    _rc0 = subprocess.call(str(AR.val) + " " + str(_p1) + " " + "--valid",shell=True,stderr=subprocess.STDOUT,stdout=file(str(DEV_NULL.val),'wb'))
    

#
# Counts object files in archive.
# 1 argument is needed - file path
# Returns - 1 if error occurred
#
def archive_object_count (_p1) :
    global AR

    if (str(Expand.hash()) != "1" ):
        return(1)
    _rc0 = subprocess.call([str(AR.val),str(_p1),"--object-count"],shell=True)

#
# Print content of archive.
# 1 argument is needed - file path
# Returns - 1 if number of arguments is incorrect
#
def archive_list_content (_p1) :
    global AR

    if (str(Expand.hash()) != "1" ):
        return(1)
    _rc0 = subprocess.call([str(AR.val),str(_p1),"--list","--no-numbers"],shell=True)

#
# Print numbered content of archive.
# 1 argument is needed - file path
# Returns - 1 if number of arguments is incorrect
#
def archive_list_numbered_content (_p1) :
    global AR

    if (str(Expand.hash()) != "1" ):
        return(1)
    print("Index\tName")
    _rc0 = subprocess.call([str(AR.val),str(_p1),"--list"],shell=True)

#
# Print numbered content of archive in JSON format.
# 1 argument is needed - file path
# Returns - 1 if number of arguments is incorrect
#
def archive_list_numbered_content_json (_p1) :
    global AR

    if (str(Expand.hash()) != "1" ):
        return(1)
    _rc0 = subprocess.call([str(AR.val),str(_p1),"--list","--json"],shell=True)

#
# Get a single file from archive by name.
# 3 arguments are needed - path to the archive
#                        - name of the file
#                        - output path
# Returns - 1 if number of arguments is incorrect
#         - 2 if error occurred
#
def archive_get_by_name (_p1,_p2,_p3) :
    global AR
    global DEV_NULL

    if (str(Expand.hash()) != "3" ):
        return(1)
    if (not subprocess.call(str(AR.val) + " " + str(_p1) + " " + "--name" + " " + str(_p2) + " " + "--output" + " " + str(_p3),shell=True,stderr=subprocess.STDOUT,stdout=file(str(DEV_NULL.val),'wb')) ):
        return(2)

#
# Get a single file from archive by index.
# 3 arguments are needed - path to the archive
#                        - index of the file
#                        - output path
# Returns - 1 if number of arguments is incorrect
#         - 2 if error occurred
#
def archive_get_by_index (_p1,_p2,_p3) :
    global AR
    global DEV_NULL

    if (str(Expand.hash()) != "3" ):
        return(1)
    if (not subprocess.call(str(AR.val) + " " + str(_p1) + " " + "--index" + " " + str(_p2) + " " + "--output" + " " + str(_p3),shell=True,stderr=subprocess.STDOUT,stdout=file(str(DEV_NULL.val),'wb')) ):
        return(2)

#
# Check if file is Mach-O universal binary with archives.
# 1 argument is needed - file path
# Returns - 0 if file is archive
#           1 if file is not archive
#
def is_macho_archive (_p1) :
    global EXTRACT
    global DEV_NULL

    if (str(Expand.hash()) != "1" ):
        return(1)
    _rc0 = subprocess.call(str(EXTRACT.val) + " " + "--check-archive" + " " + str(_p1),shell=True,stderr=subprocess.STDOUT,stdout=file(str(DEV_NULL.val),'wb'))
    

#
# Check string is a valid decimal number.
# 1 argument is needed - string to check.
# Returns - 0 if string is a valid decimal number.
#           1 otherwise
#
def is_decimal_number (_p1) :
    global re

    if (str(Expand.hash()) != "1" ):
        return(1)
    re=Bash2Py("^[0-9]+$")
    if (re.search(str(re.val),str(_p1)) ):
        return(0)
    else:
        return(1)

#
# Check string is a valid hexadecimal number.
# 1 argument is needed - string to check.
# Returns - 0 if string is a valid hexadecimal number.
#           1 otherwise
#
def is_hexadecimal_number (_p1) :
    global re

    if (str(Expand.hash()) != "1" ):
        return(1)
    re=Bash2Py("^0x[0-9a-fA-F]+$")
    if (re.search(str(re.val),str(_p1)) ):
        return(0)
    else:
        return(1)

#
# Check string is a valid number (decimal or hexadecimal).
# 1 argument is needed - string to check.
# Returns - 0 if string is a valid number.
#           1 otherwise
#
def is_number (_p1) :
    if (str(Expand.hash()) != "1" ):
        return(1)
    if (is_decimal_number(_p1) ):
        return(0)
    if (is_hexadecimal_number(_p1) ):
        return(0)
    return(1)

#
# Check string is a valid decimal range.
# 1 argument is needed - string to check.
# Returns - 0 if string is a valid decimal range.
#           1 otherwise
#
def is_decimal_range (_p1) :
    global re

    if (str(Expand.hash()) != "1" ):
        return(1)
    re=Bash2Py("^[0-9]+-[0-9]+$")
    if (re.search(str(re.val),str(_p1)) ):
        return(0)
    else:
        return(1)

#
# Check string is a valid hexadecimal range
# 1 argument is needed - string to check.
# Returns - 0 if string is a valid hexadecimal range
#           1 otherwise
#
def is_hexadecimal_range (_p1) :
    global re

    if (str(Expand.hash()) != "1" ):
        return(1)
    re=Bash2Py("^0x[0-9a-fA-F]+-0x[0-9a-fA-F]+$")
    if (re.search(str(re.val),str(_p1)) ):
        return(0)
    else:
        return(1)

#
# Check string is a valid range (decimal or hexadecimal).
# 1 argument is needed - string to check.
# Returns - 0 if string is a valid range
#           1 otherwise
#
def is_range (_p1) :
    if (str(Expand.hash()) != "1" ):
        return(1)
    if (is_decimal_range(_p1) ):
        return(0)
    if (is_hexadecimal_range(_p1) ):
        return(0)
    return(1)

