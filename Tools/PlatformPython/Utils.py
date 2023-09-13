# Various reused stuff for Platform python scripting

#All these modules here are part of Python already
# from __future__ import absolute_import
# import subprocess
# import importlib
import Tools.PlatformPython.Base as sc

import sys
import os
import subprocess
from typing import List

# Simplifications for easy setup


def easy_AutoVenv(THIS_SCRIPT_NAME: str, EXPECTED_REL_PATH_TO_ANCHOR: str, extra_pip_commands: List[str] = []):
    REL_ANCHOR = EXPECTED_REL_PATH_TO_ANCHOR #shorter variable name
    if(not sc.executingAtProperRelPath(REL_ANCHOR)):
        if(os.path.exists("./Tools")):                 #TODO is this still correct?
            sc.scprint("Found \"Tools\" directory; you might be running this script from /PlanetDataTools. That is fine.")
            os.chdir("./Tools")
            if(not sc.executingAtProperRelPath(REL_ANCHOR)):
                sc.scprint("Please run this script by using \"python "+THIS_SCRIPT_NAME+"\" from the PlanetDataTools/Tools/"+REL_ANCHOR+" directory!")
                input("Press enter to exit...")
                exit(1)
        else:
            sc.scprint("Please run this script by using \"python "+THIS_SCRIPT_NAME+"\" from the PlanetDataTools/Tools/"+REL_ANCHOR+" directory!")
            input("Press enter to exit...")
            exit(1)

    #Run this script in a venv if not already
    if(not sc.currently_in_venv()):
        sc.makeVenvIfNotAlready(os.path.join(REL_ANCHOR,"sc_tools_env"))
        sc.scprint("Now continuing in this venv.")
        # Run this script in a subprocess POpen and then close after POpen
        sc.runScriptInVenv(os.path.join(REL_ANCHOR,"sc_tools_env"), THIS_SCRIPT_NAME)
        sc.scprint("Subprocess ended.")
        exit(0)

    #######################################
    ### FROM NOW ON, WE ARE FOR SURE ######
    ### RUNNING IN THE RIGHT VENV    ######
    sc.scprint("Ensuring required packages are installed (from configfiles/devtools_pyreq.txt)")
    sc.installRequirements(os.path.join(REL_ANCHOR,"configfiles/pyreq_wheel_only.txt"))
    sc.installRequirements(os.path.join(REL_ANCHOR,"configfiles/devtools_pyreq.txt"))
    sc.scprint("Done ensuring required packages are installed.")
    sc.scprint("Running extra pip commands...")
    for command in extra_pip_commands:
        sc.scprint("Running: python -m pip " + command)
        # cmdlist = os.PathLike([sys.executable, "-m", "pip"])
        try:
            subprocess.check_call(sys.executable + " -m pip " + command)
        except:
            subprocess.check_call(sys.executable + " -m pip3 " + command)
    sc.scprint("------- End of easy_AutoVenv -------")

#######################################
### Common Functions ##################

# https://stackoverflow.com/a/20804735/11502722
WIN_10 = (10, 0, 0)
WIN_8 = (6, 2, 0)
WIN_7 = (6, 1, 0)
WIN_SERVER_2008 = (6, 0, 1)
WIN_VISTA_SP1 = (6, 0, 1)
WIN_VISTA = (6, 0, 0)
WIN_SERVER_2003_SP2 = (5, 2, 2)
WIN_SERVER_2003_SP1 = (5, 2, 1)
WIN_SERVER_2003 = (5, 2, 0)
WIN_XP_SP3 = (5, 1, 3)
WIN_XP_SP2 = (5, 1, 2)
WIN_XP_SP1 = (5, 1, 1)
WIN_XP = (5, 1, 0)

#https://en.wikipedia.org/wiki/Windows_10_version_history
#older ones exist
WINBUILD_1703 = 15063
WINBUILD_1709 = 16299
WINBUILD_1803 = 17134
WINBUILD_1809 = 17763
WINBUILD_1903 = 18362
WINBUILD_1909 = 18363
WINBUILD_2004 = 19041

# Usage:
# if get_winver() >= WIN_XP_SP3:
#      ...
def get_winver():
    wv = sys.getwindowsversion()
    if hasattr(wv, 'service_pack_major'):  # python >= 2.7
        sp = wv.service_pack_major or 0
    else:
        import re
        r = re.search("\s\d$", wv.service_pack)
        sp = int(r.group(0)) if r else 0
    return (wv.major, wv.minor, sp)

def get_winbuild() -> int:
    wv = sys.getwindowsversion()
    return wv.build

# This python script running in Windows
def is_running_in_windows() -> bool:
    return os.name == 'nt'

# This python script running in Linux / some other posix-based os
# (This includes WSL)
def is_running_in_posix() -> bool:
    return os.name == 'posix'