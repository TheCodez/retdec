#! /usr/bin/env python3
import shutil
import sys
import os
import subprocess

import retdec_utils as utils

##
## Prints help to stream $1.
##
def print_help (_p1) :
    print("Create Yara rules file from static libraries.",file=file(str(_p1),'wb'))
    print("Usage: " + __file__ + " [OPTIONS] -o OUTPUT INPUT_1 [... INPUT_N]\n",file=file(str(_p1),'wb'))
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


def die_with_error_and_cleanup(message):
    """Exit with error message $1 and clean up temporary files.
    """
    global NO_CLEANUP

    # Cleanup.
    if not NO_CLEANUP:
        temporary_files_cleanup()

    utils.print_error_and_die(message  +  '.')



def temporary_files_cleanup():
    """Removes temporary files.
    """
    global DIR_PATH

    for n in os.listdir(DIR_PATH):
        p = os.path.join(DIR_PATH, n)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.unlink(p)


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
        if str(MIN_PURE) != '':
            die_with_error_and_cleanup("duplicate option: --min-pure")
        Make("MIN_PURE").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-i' or str(sys.argv[1]) == '--ignore-nops'):
        if str(IGNORE_NOP) != '':
            die_with_error_and_cleanup("duplicate option: --ignore-nops")
        Make("IGNORE_NOP").setValue("--ignore-nops")
        Make("IGNORE_OPCODE").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    elif ( str(sys.argv[1]) == '-o' or str(sys.argv[1]) == '--output'):
        if str(OUT_PATH) != '':
            die_with_error_and_cleanup("duplicate option: --output")
        Make("OUT_PATH").setValue(sys.argv[2])
        subprocess.call(["shift","2"],shell=True)
    else:
        if  not (os.path.isfile(str(sys.argv[1]))):
            die_with_error_and_cleanup("input '" + str(sys.argv[1]) + "' is not a valid file nor argument")
        Make("INPUT_LIBS").setValue("(" + str(sys.argv[1]) + ")")
        subprocess.call(["shift"],shell=True)

# Check inputs.
if Expand.hash():
    die_with_error_and_cleanup("no input files")

# Output directory - compulsory argument.
if OUT_PATH == '':
    die_with_error_and_cleanup("option -o|--output is compulsory")
else:
    FILE_PATH = OUT_PATH
    DIR = os.popen("dirname \"" + os.popen("get_realpath \"" + str(FILE_PATH) + "\"").read().rstrip("\n") + "\"").read().rstrip("\n")
    DIR_PATH = os.popen("mktemp -d \"" + str(DIR) + "/XXXXXXXXX\"").read().rstrip("\n")

# Set default in argparser
# Set default --min-pure information argument.
if not (MIN_PURE != ''):
    MIN_PURE = 16

# Create .pat files for every library.
for LIB_PATH in Array(INPUT_LIBS[@] ]):
    # Check for invalid archives.
    if (not subprocess.call(["is_valid_archive",str(LIB_PATH)],shell=True) ):
        print("ignoring file '" + str(LIB_PATH) + "' - not valid archive")
        continue
    # Get library name for .pat file.
    LIB_NAME_TMP = os.popen("basename \"" + str(LIB_PATH) + "\"").read().rstrip("\n")
    LIB_NAME = LIB_NAME_TMP%%.*
    # Create sub-directory for object files.
    OBJECT_DIRECTORY = str(DIR_PATH) + "/" + str(LIB_NAME) + "-objects"
    OBJECT_DIRECTORIES = "(" + str(OBJECT_DIRECTORY) + ")"
    os.mkdir(OBJECT_DIRECTORY)
    # Extract all files to temporary folder.
    subprocess.call([str(AR),str(LIB_PATH),"--extract","--output",str(OBJECT_DIRECTORY)],shell=True)
    # List all extracted objects.
    IFS_OLD = IFS
    IFS = "\n"
    OBJECTS = "(" + os.popen("find \"" + str(OBJECT_DIRECTORY) + "\" -type f").read().rstrip("\n") + ")"
    IFS = IFS_OLD
    # Extract patterns from library.
    PATTERN_FILE = str(DIR_PATH) + "/" + str(LIB_NAME) + ".pat"
    PATTERN_FILES = "(" + str(PATTERN_FILE) + ")"
    subprocess.call([str(BIN2PAT),"-o",str(PATTERN_FILE),str(OBJECTS[@] ])],shell=True)
    if _rc0 != 0:
        die_with_error_and_cleanup("utility bin2pat failed when processing '" + str(LIB_PATH) + "'")
    # Remove extracted objects continuously.
    if not str(NO_CLEANUP) != '':
        subprocess.call(["rm","-r",str(OBJECT_DIRECTORY)],shell=True)

# Skip second step - only .pat files will be created.
if str(BIN2PAT_ONLY) != '':
    if not str(NO_CLEANUP) != '':
        subprocess.call(["rm","-f",str(OBJECT_DIRECTORIES[@] ])],shell=True)
    sys.exit(0)

# Create final .yara file from .pat files.
if str(DO_LOGFILE) != '':
    subprocess.call([str(PAT2YARA),str(PATTERN_FILES[@] ]),"--min-pure",str(MIN_PURE),"-o",str(FILE_PATH),"-l",str(FILE_PATH) + ".log",str(IGNORE_NOP),str(IGNORE_OPCODE)],shell=True)
    if _rc0 != 0:
        die_with_error_and_cleanup("utility pat2yara failed")
else:
    subprocess.call([str(PAT2YARA),str(PATTERN_FILES[@] ]),"--min-pure",str(MIN_PURE),"-o",str(FILE_PATH),str(IGNORE_NOP),str(IGNORE_OPCODE)],shell=True)
    if _rc0 != 0:
        die_with_error_and_cleanup("utility pat2yara failed")

# Do cleanup.
if not str(NO_CLEANUP) != '':
    temporary_files_cleanup()
