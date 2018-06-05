#! /usr/bin/env python
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

#
# A wrapper for fileinfo that:
#
#  - uses also external YARA patterns,
#  - is able to analyze archives (.a/.lib files).
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
# When analyzing an archive, use the archive decompilation script `--list` instead of
# `fileinfo` because fileinfo is currently unable to analyze archives.
#
# First, we have to find path to the input file. We take the first parameter
# that does not start with a dash. This is a simplification and may not work in
# all cases. A proper solution would need to parse fileinfo parameters, which
# would be complex.
for Make("arg").val in Expand.at():
    if (str(arg.val:0:1) != "-" ):
        Make("IN").setValue(arg.val)
        if (not subprocess.call(["has_archive_signature",str(IN.val)],shell=True) ):
            # The input file is not an archive.
            break
        # The input file is an archive, so use the archive decompilation script
        # instead of fileinfo.
        Make("ARCHIVE_DECOMPILER_SH_PARAMS").setValue("("+str(IN.val)+" --list)")
        # When a JSON output was requested (any of the parameters is
        # -j/--json), forward it to the archive decompilation script.
        for Make("arg").val in Expand.at():
            if (if not str(arg.val) == "-j":
                str(arg.val) == "--json" ):
                Make("ARCHIVE_DECOMPILER_SH_PARAMS").setValue("(--json)")
        subprocess.call([str(ARCHIVE_DECOMPILER_SH.val),str(ARCHIVE_DECOMPILER_SH_PARAMS.val[@] ])],shell=True)
        exit(_rc0)
# We are not analyzing an archive, so proceed to fileinfo.
FILEINFO_PARAMS=Bash2Py("()")
for Make("par").val in Array(FILEINFO_EXTERNAL_YARA_PRIMARY_CRYPTO_DATABASES.val[@] ]):
    Make("FILEINFO_PARAMS").setValue("(--crypto "+str(par.val)+")")
for Make("var").val in Expand.at():
    if (str(var.val) == "--use-external-patterns" ):
        for Make("par").val in Array(FILEINFO_EXTERNAL_YARA_EXTRA_CRYPTO_DATABASES.val[@] ]):
            Make("FILEINFO_PARAMS").setValue("(--crypto "+str(par.val)+")")
    else:
        Make("FILEINFO_PARAMS").setValue("("+str(var.val)+")")
_rc0 = subprocess.call([str(FILEINFO.val),str(FILEINFO_PARAMS.val[@] ])],shell=True)
