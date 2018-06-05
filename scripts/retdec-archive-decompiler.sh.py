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

def Str(value):
  if isinstance(value, list):
    return " ".join(value)
  if isinstance(value, basestring):
    return value
  return str(value)

class Expand(object):
  @staticmethod
  def at():
    if (len(sys.argv) < 2):
      return []
    return  sys.argv[1:]
  @staticmethod
  def star(in_quotes):
    if (in_quotes):
      if (len(sys.argv) < 2):
        return ""
      return " ".join(sys.argv[1:])
    return Expand.at()
  @staticmethod
  def hash():
    return  len(sys.argv)-1
  @staticmethod
  def dollar():
    return  os.getpid()

#
# Runs the decompilation script with the given arguments over all files in the
# given static library.
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
##
## Configuration.
##
TIMEOUT=Bash2Py(300)
# Timeout for the decompilation script.
##
## Prints help to stream $1.
##
def print_help (_p1) :
    print("Runs the decompilation script with the given optional arguments over all files",file=file(str(_p1),'wb'))
    print("in the given static library or prints list of files in plain text",file=file(str(_p1),'wb'))
    print("with --plain argument or in JSON format with --json argument. You",file=file(str(_p1),'wb'))
    print("can pass arguments for decompilation after double-dash '--' argument.",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))
    print("Usage:",file=file(str(_p1),'wb'))
    print("    "+__file__+" ARCHIVE [-- ARGS]",file=file(str(_p1),'wb'))
    print("    "+__file__+" ARCHIVE --plain|--json",file=file(str(_p1),'wb'))
    print(,file=file(str(_p1),'wb'))

##
## Prints error in either plain text or JSON format.
## One argument required: error message.
##
def print_error_plain_or_json (_p1) :
    global JSON_FORMAT
    global M

    if (str(JSON_FORMAT.val) != '' ):
        Make("M").setValue(os.popen("echo \""+str(_p1)+"\" | sed \"s,\\\\,\\\\\\\\,g\"").read().rstrip("\n"))
        Make("M").setValue(os.popen("echo \""+str(M.val)+"\" | sed \"s,\\",\\\\",g\"").read().rstrip("\n"))
        print("{")
        print("    \"error\" : \""+str(M.val)+"\"")
        print("}")
        exit(1)
    else:
        # Otherwise print in plain text.
        subprocess.call(["print_error_and_die",str(_p1)],shell=True)

##
## Cleans up all temporary files.
## No arguments accepted.
##
def cleanup () :
    global TMP_ARCHIVE

    subprocess.call(["rm","-f",str(TMP_ARCHIVE.val)],shell=True)

##
## Parse script arguments.
##
while (Expand.hash() > 0):
    
    if ( str(sys.argv[1]) == '-h' or str(sys.argv[1]) == '--help'):
        print_help("/dev/stdout")
        exit(0)
    elif ( str(sys.argv[1]) == '--list'):
        Make("LIST_MODE").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--plain'):
        if str(JSON_FORMAT.val) != '':
            subprocess.call(["print_error_and_die","Arguments --plain and --json are mutually exclusive."],shell=True)
        Make("LIST_MODE").setValue(1)
        Make("PLAIN_FORMAT").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--json'):
        if str(PLAIN_FORMAT.val) != '':
            subprocess.call(["print_error_and_die","Arguments --plain and --json are mutually exclusive."],shell=True)
        Make("LIST_MODE").setValue(1)
        Make("JSON_FORMAT").setValue(1)
        subprocess.call(["shift"],shell=True)
    elif ( str(sys.argv[1]) == '--'):
        # Skip -- and store arguments for decompilation.
        subprocess.call(["shift"],shell=True)
        Make("DECOMPILER_SH_ARGS").setValue(Expand.star(0))
        break
    else:
        if  not (os.path.isfile(str(sys.argv[1]))):
            subprocess.call(["print_error_and_die","Input '"+str(sys.argv[1])+"' is not a valid file."],shell=True)
        Make("LIBRARY_PATH").setValue(sys.argv[1])
        subprocess.call(["shift"],shell=True)
# Check arguments
if not str(LIBRARY_PATH.val) != '':
    print_error_plain_or_json("No input file.")
# Check for archives packed in Mach-O Universal Binaries.
if (subprocess.call(["is_macho_archive",str(LIBRARY_PATH.val)],shell=True) ):
    if (str(LIST_MODE.val) != '' ):
        if (str(JSON_FORMAT.val) != '' ):
            subprocess.call([str(EXTRACT.val),"--objects","--json",str(LIBRARY_PATH.val)],shell=True)
        else:
            # Otherwise print in plain text.
            subprocess.call([str(EXTRACT.val),"--objects",str(LIBRARY_PATH.val)],shell=True)
        # Not sure why failure is used there.
        exit(1)
    Make("TMP_ARCHIVE").setValue(str(LIBRARY_PATH.val)+".a")
    subprocess.call([str(EXTRACT.val),"--best","--out",str(TMP_ARCHIVE.val),str(LIBRARY_PATH.val)],shell=True)
    Make("LIBRARY_PATH").setValue(TMP_ARCHIVE.val)
# Check for thin archives.
if (subprocess.call(["has_thin_archive_signature",str(LIBRARY_PATH.val)],shell=True) ):
    print_error_plain_or_json("File is a thin archive and cannot be decompiled.")
# Check if file is archive
if (not subprocess.call(["is_valid_archive",str(LIBRARY_PATH.val)],shell=True) ):
    print_error_plain_or_json("File is not supported archive or is not readable.")
# Check number of files.
FILE_COUNT=Bash2Py(os.popen("archive_object_count \""+str(LIBRARY_PATH.val)+"\"").read().rstrip("\n"))
if (int(FILE_COUNT.val) <= 0 ):
    print_error_plain_or_json("No files found in archive.")
##
## List only mode.
##
if (str(LIST_MODE.val) != '' ):
    if (str(JSON_FORMAT.val) != '' ):
        subprocess.call(["archive_list_numbered_content_json",str(LIBRARY_PATH.val)],shell=True)
    else:
        # Otherwise print in plain text.
        subprocess.call(["archive_list_numbered_content",str(LIBRARY_PATH.val)],shell=True)
    cleanup()
    exit(0)
##
## Run the decompilation script over all the found files.
##
print("Running \`"+str(DECOMPILER_SH.val),end="")
if (str(DECOMPILER_SH_ARGS.val) != str() ):
    print(DECOMPILER_SH_ARGS.val,end="")
print("\` over "+str(FILE_COUNT.val)+" files with timeout "+str(TIMEOUT.val)+"s","(run \`kill "+str(Expand.dollar())+"\` to terminate this script)...",stderr=subprocess.STDOUT)
print(,stderr=subprocess.STDOUT)
Make("INDEX").setValue(0)
while (INDEX.val < FILE_COUNT.val):
    Make("FILE_INDEX").setValue((INDEX.val + 1))
    print("-ne",str(FILE_INDEX.val)+"/"+str(FILE_COUNT.val)+"\t\t")
    # We have to use indexes instead of names because archives can contain multiple files with same name.
    Make("LOG_FILE").setValue(str(LIBRARY_PATH.val)+".file_"+str(FILE_INDEX.val)+".log.verbose")
    # Do not escape!
    subprocess.call("gnutimeout" + " " + str(TIMEOUT.val) + " " + str(DECOMPILER_SH.val) + " " + "--ar-index="+str(INDEX.val) + " " + "-o" + " " + str(LIBRARY_PATH.val)+".file_"+str(FILE_INDEX.val)+".c" + " " + str(LIBRARY_PATH.val) + " " + str(DECOMPILER_SH_ARGS.val),shell=True,stdout=file(str(LOG_FILE.val),'wb'),stderr=subprocess.STDOUT)
    
    Make("RC").setValue(_rc0)
    # Print status.
    
    if ( str(RC.val) == '0'):
        print("[OK]")
    elif ( str(RC.val) == '124'):
        print("[TIMEOUT]")
    else:
        print("[FAIL]")
    Make("INDEX").postinc()
# Cleanup
cleanup()
# Success!
exit(0)
