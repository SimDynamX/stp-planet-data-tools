# Various reused stuff for Platform python scripting

#All these modules here are part of Python already
# from __future__ import absolute_import
# import subprocess
# import importlib
import Tools.PlatformPython.Base as sc

import sys
import os

#sc.EnsureModulesInstalled([""])

#######################################
### Common Functions ##################

# Relative to .RELPATHS_ANCHOR_FILE
Platform = ".."

# Relative to .RELPATHS_ANCHOR_FILE
Compute_Server = os.path.join(Platform,"Compute_Server")

# Relative to .RELPATHS_ANCHOR_FILE
Packages = os.path.join(Compute_Server, "packages")