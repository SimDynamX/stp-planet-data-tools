# -*- coding: utf-8 -*-

# SpaceCRAFT Planet Data Preprocessor

# Assumptions/Disclaimers:
# - Can work with fresh install or any amount of "progress".

# TODO:
# - (none)

# TODO BREAKING:
# - (none)

#######################################
### SETUP / PREREQUISITES #############

#This is at a relative directory, and doesn't include any non-standard Python modules
import Tools.PlatformPython.Imports as sc
import Tools.PlatformPython.RelPaths as rp
import os

EXPECTED_REL_PATH_TO_ANCHOR = "Tools/."
#pip install gdal>=2.2.2 --global-option=build_ext --global-option="-IC:/OSGeo4W64/include/" --global-option="-LC:/OSGeo4W64/lib/"
# extra_commands = ["install gdal>=2.2.2 --global-option=build_ext --global-option=\"-IC:/OSGeo4W64/include/\" --global-option=\"-LC:/OSGeo4W64/lib/\""]

# Do this instead for gdal: 
# .\Tools\sc_tools_env\for_windows\Scripts\python.exe -m pip install .\GDAL_Wheels\GDAL-3.8.2-cp311-cp311-win_amd64.whl
# More details: https://www.youtube.com/watch?v=8iCWUp7WaTk
# https://github.com/cgohlke/geospatial-wheels/releases/download/v2024.1.1/GDAL-3.8.2-cp311-cp311-win_amd64.whl
# https://github.com/cgohlke/geospatial-wheels/releases (for newer releases)
# For Example: .\Tools\sc_tools_env\for_windows\Scripts\python.exe -m pip install .\GDAL_Wheels\GDAL-3.4.3-cp311-cp311-win_amd64.whl
sc.easy_AutoVenv(__file__, EXPECTED_REL_PATH_TO_ANCHOR)

#######################################
### IMPORTS ###########################

import os
from os import path
from sys import platform
import sys
import signal
# import psutil
import json
import glob
import zipfile
import time
import numpy as np
import math

import json

from osgeo import gdal, osr

gdal.UseExceptions()
# gdal.AllRegister()

from shutil import copyfile
from colorama import Fore, Back, Style
import progressbar as pb

#######################################
### GLOBALS ###########################

thisDir = os.path.dirname(os.path.abspath(__file__))
inputDir = os.path.join(thisDir, "input")
outputDir = os.path.join(thisDir, "output")
productsDir = os.path.join(thisDir, "products")
projDir = os.path.join(thisDir, "proj")

# -----------------------------------------------------------------------------
# User settings: list your eight input rasters here (in the order you like).
# They must all share the same projection and pixel size.
# -----------------------------------------------------------------------------

ds : gdal.Dataset = gdal.Open(path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_Merged.tiff"), gdal.GA_ReadOnly)
# ds : gdal.Dataset = gdal.Open(path.join(inputDir, "Moon","Global","Lunar_LRO_LROC-WAC_Mosaic_global_100m_June2013.tif"), gdal.GA_ReadOnly)
print(gdal.Info(ds, stats=True))