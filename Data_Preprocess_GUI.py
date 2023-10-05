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

# This is at a relative directory, and doesn't include any non-standard Python modules
import Tools.PlatformPython.Imports as sc
import Tools.PlatformPython.RelPaths as rp
import os

EXPECTED_REL_PATH_TO_ANCHOR = "Tools/."
# pip install gdal>=2.2.2 --global-option=build_ext --global-option="-IC:/OSGeo4W64/include/" --global-option="-LC:/OSGeo4W64/lib/"
# extra_commands = ["install gdal>=2.2.2 --global-option=build_ext --global-option=\"-IC:/OSGeo4W64/include/\" --global-option=\"-LC:/OSGeo4W64/lib/\""]
# Do this instead for gdal: https://www.youtube.com/watch?v=8iCWUp7WaTk
# https://www.lfd.uci.edu/~gohlke/pythonlibs/
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

from osgeo import gdal

from shutil import copyfile
from colorama import Fore, Back, Style
import progressbar as pb

from PySide2.QtWidgets import (QApplication, QVBoxLayout, QWidget, QPushButton, 
                               QFileDialog, QListWidget, QDoubleSpinBox, QLineEdit, 
                               QCheckBox, QProgressBar, QLabel, QComboBox)

#######################################
### GLOBALS ###########################

thisDir = os.path.dirname(os.path.abspath(__file__))
inputDir = os.path.join(thisDir, "input")
outputDir = os.path.join(thisDir, "output")
productsDir = os.path.join(thisDir, "products")
projDir = os.path.join(thisDir, "proj")

# dataPaused = False

termUseColor = True

####################################
### MATH ###########################


def ppd_to_ppm(ppd, radius):
    return 2 * 3.1415962 * radius / (360 * ppd)


#######################################
### Actions ###########################


def playGreeting():
    global termUseColor

    if termUseColor:
        print(sc.greetingString)
    else:
        print(sc.greetingStringNoColor)

    print("\nPlanetDataTools - Data_Preprocessor")
    print("---------------------")


def progress_callback(complete, message, data):
    percent = int(complete * 100)  # round to integer percent
    data.update(percent)  # update the progressbar
    return 1


def Gnomonic_Warp(
    inputFiles: list,
    radius: float,
    prjFileRoot: str,
    prjFileSide: str,
    progBar: pb.ProgressBar,
    meters_per_pixel=0.0,
    forceFullSideExtents=False,
    input_nodata_val=None,
    nodata_val=0,
    warpoptions=None,
):
    print("-------------------")
    print("-- Gnomonic_Warp --")
    print("\t inputFile:", inputFiles)
    print("\t radius:", radius)
    prjFile = prjFileRoot + "_" + prjFileSide + ".prj"
    print("\t prjFile:", prjFile)

    inpath = []

    for inputFile in inputFiles:
        inpath.append(path.join(inputDir, inputFile))
    outpath = path.join(outputDir, inputFiles[0])
    outpath_split = path.splitext(outpath)
    # outpath = outpath_split[0] + "_Gnom_" + prjFileSide + outpath_split[1]
    outpath = outpath_split[0] + "_Gnom_" + prjFileSide + ".tif"

    if os.path.exists(outpath):
        print("WARNING: there is already a file at " + outpath + "; skipped this warp.")
        return
    elif not path.exists(path.split(outpath)[0]):
        print('Making new output directory "' + path.split(outpath)[0] + '"')
        os.makedirs(path.split(outpath)[0])

    radius_plus = radius * 33.0 / 32.0

    if warpoptions == None:
        if forceFullSideExtents:
            warpoptions = gdal.WarpOptions(
                resampleAlg="bilinear",
                dstSRS=path.join(projDir, prjFile),
                outputBounds=[-radius_plus, -radius_plus, radius_plus, radius_plus],
                xRes=meters_per_pixel,
                yRes=meters_per_pixel,
                srcNodata=input_nodata_val,
                dstNodata=nodata_val,
                format="GTiff",
                creationOptions=["COMPRESS=LZW"],
                multithread=True,
                callback=progress_callback,
                callback_data=progBar,
            )
        else:
            warpoptions = gdal.WarpOptions(
                resampleAlg="bilinear",
                dstSRS=path.join(projDir, prjFile),
                xRes=meters_per_pixel,
                yRes=meters_per_pixel,
                srcNodata=input_nodata_val,
                dstNodata=nodata_val,
                format="GTiff",
                creationOptions=["COMPRESS=LZW"],
                multithread=True,
                callback=progress_callback,
                callback_data=progBar,
            )

    progBar.start()
    gdal.Warp(outpath, inpath, options=warpoptions)
    progBar.finish()


def Gnomonic_Warp_Global(
    inputFiles: list,
    radius: float,
    prjFileRoot: str,
    progBar: pb.ProgressBar,
    meters_per_pixel=0.0,
    input_nodata_val=None,
    nodata_val=0,
):
    print("--------------------------")
    print("-- Gnomonic_Warp_Global --")

    Gnomonic_Warp(
        inputFiles,
        radius,
        prjFileRoot,
        "Eq_0",
        progBar,
        meters_per_pixel,
        True,
        input_nodata_val,
        nodata_val,
    )
    Gnomonic_Warp(
        inputFiles,
        radius,
        prjFileRoot,
        "Eq_90",
        progBar,
        meters_per_pixel,
        True,
        input_nodata_val,
        nodata_val,
    )
    Gnomonic_Warp(
        inputFiles,
        radius,
        prjFileRoot,
        "Eq_180",
        progBar,
        meters_per_pixel,
        True,
        input_nodata_val,
        nodata_val,
    )
    Gnomonic_Warp(
        inputFiles,
        radius,
        prjFileRoot,
        "Eq_270",
        progBar,
        meters_per_pixel,
        True,
        input_nodata_val,
        nodata_val,
    )
    Gnomonic_Warp(
        inputFiles,
        radius,
        prjFileRoot,
        "NPole",
        progBar,
        meters_per_pixel,
        True,
        input_nodata_val,
        nodata_val,
    )
    Gnomonic_Warp(
        inputFiles,
        radius,
        prjFileRoot,
        "SPole",
        progBar,
        meters_per_pixel,
        True,
        input_nodata_val,
        nodata_val,
    )


#######################################
### MAIN ##############################
class AppGUI(QWidget):
    def __init__(self):
        super().__init__()

        # Layout
        layout = QVBoxLayout()

        # Widgets for inputFiles
        self.file_list = QListWidget()
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file)
        layout.addWidget(QLabel("Input Files:"))
        layout.addWidget(self.file_list)
        layout.addWidget(add_file_btn)

        # Widget for radius
        self.radius_input = QDoubleSpinBox()
        self.radius_input.setRange(0, 10000)  # Example range
        layout.addWidget(QLabel("Radius:"))
        layout.addWidget(self.radius_input)

        dic = {'earth':'earth_gnom', 'moon':'moon_gnom', 'mars':'mars_gnom'}
        # Widgets for string inputs
        self.prjFileRoot_combo = QComboBox()
        self.prjFileRoot_combo.addItems(["Option1_Root", "Option2_Root", "Option3_Root"])
        layout.addWidget(QLabel("Planet:"))
        layout.addWidget(self.prjFileRoot_combo)

        self.prjFileSide_combo = QComboBox()
        self.prjFileSide_combo.addItems(["Eq_0", "Eq_90","Eq_180","Eq_270","NPole","SPole"])
        layout.addWidget(QLabel("Side:"))
        layout.addWidget(self.prjFileSide_combo)

        # Progress Bar
        self.progBar = QProgressBar()
        layout.addWidget(self.progBar)

        # Other parameters with default values (as example)
        self.mpp_input = QDoubleSpinBox()
        self.mpp_input.setRange(0, 1000)  # Example range
        layout.addWidget(QLabel("Meters per Pixel:"))
        layout.addWidget(self.mpp_input)

        self.forceFullSideExtents_chk = QCheckBox("Force Full Side Extents")
        layout.addWidget(self.forceFullSideExtents_chk)

        # Add more widgets as necessary...

        # Submit button
        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.submit)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def add_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_name:
            self.file_list.addItem(file_name)

    def submit(self):
        inputFiles = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        radius = self.radius_input.value()
        prjFileRoot = self.prjFileRoot_input.text()
        prjFileSide = self.prjFileSide_input.text()
        progBar = self.progBar
        meters_per_pixel = self.mpp_input.value()
        forceFullSideExtents = self.forceFullSideExtents_chk.isChecked()
        # Add more parameters as needed

        Gnomonic_Warp(
            inputFiles, radius, prjFileRoot, prjFileSide, progBar, 
            meters_per_pixel=meters_per_pixel, forceFullSideExtents=forceFullSideExtents
        )
        # Add more arguments as needed...


# Use a larger multiplier here to avoid RAM issues with loading/storing the huge datasets
# large_datasets_mpp_mult = 1
large_datasets_mpp_mult = 4

DOWNSAMPLE_2X = 2
DOWNSAMPLE_4X = 4

# Nodata value is usually 0, but it's different for some things:
int16_nodata = -32768  # Datasets are usually consistent about this
uint16_nodata = 0
int32_nodata = -2147483648
float_nodata = -1e32
double_nodata = -1e32

# if __name__ == "__main__":
#     playGreeting()

#     print("GDAL Version:", gdal.VersionInfo())

#     pbar = pb.ProgressBar()

#     # Moon Global
#     Gnomonic_Warp_Global(
#         [path.join("Moon", "Global", "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif")],
#         1737400.0,
#         "moon_gnom",
#         pbar,
#         meters_per_pixel=118 * large_datasets_mpp_mult,
#     )
#     Gnomonic_Warp_Global(
#         [
#             path.join(
#                 "Moon", "Global", "Lunar_LRO_LROC-WAC_Mosaic_global_100m_June2013.tif"
#             )
#         ],
#         1737400.0,
#         "moon_gnom",
#         pbar,
#         meters_per_pixel=100 * large_datasets_mpp_mult,
#     )
#     # Moon Apollo Sites
#     Gnomonic_Warp(
#         [path.join("Moon", "Local", "Apollo17", "APOLLO17_DTM_150CM.TIFF")],
#         1737400.0,
#         "moon_gnom",
#         "Eq_0",
#         pbar,
#         meters_per_pixel=1.5,
#         nodata_val=float_nodata,
#     )
#     Gnomonic_Warp(
#         [path.join("Moon", "Local", "Apollo17", "APOLLO17_ORTHOMOSAIC_50CM.TIFF")],
#         1737400.0,
#         "moon_gnom",
#         "Eq_0",
#         pbar,
#         meters_per_pixel=0.5,
#     )
#     Gnomonic_Warp(
#         [
#             path.join(
#                 "Moon", "Local", "Apollo15", "LRO_NAC_DEM_Apollo_15_26N004E_150cmp.tif"
#             )
#         ],
#         1737400.0,
#         "moon_gnom",
#         "Eq_0",
#         pbar,
#         meters_per_pixel=1.5 * 2,
#         nodata_val=float_nodata,
#     )
#     #     #TODO this ^ needs its nodata value set to our standardized value
#     Gnomonic_Warp(
#         [
#             path.join(
#                 "Moon", "Local", "Apollo15", "Moon_LRO_NAC_Mosaic_26N004E_50cmp.tif"
#             )
#         ],
#         1737400.0,
#         "moon_gnom",
#         "Eq_0",
#         pbar,
#         meters_per_pixel=0.5 * 4,
#     )
#     # TODO this ^ is giving an error partway through:
#     # ERROR 1: LZWDecode:Not enough data at scanline 47450 (short 53477 bytes)
#     # ERROR 1: TIFFReadEncodedStrip() failed.
#     # ERROR 1: C:\Users\conno\Documents\GitHub\PlanetDataTools\input\Moon\Local\Apollo15\Moon_LRO_NAC_Mosaic_26N004E_50cmp.tif,
#     #    band 1: IReadBlock failed at X offset 0, Y offset 47450: TIFFReadEncodedStrip() failed.
#     # Moon South Pole Altimetry
#     Gnomonic_Warp(
#         [path.join("Moon", "Local", "SouthPole", "LRO_LOLA_DEM_SPolar875_10m.tif")],
#         1737400.0,
#         "moon_gnom",
#         "SPole",
#         pbar,
#         meters_per_pixel=10,
#         nodata_val=int16_nodata,
#     )
#     Gnomonic_Warp(
#         [path.join("Moon", "Local", "SouthPole", "LRO_LOLA_DEM_SPole75_30m.tif")],
#         1737400.0,
#         "moon_gnom",
#         "SPole",
#         pbar,
#         meters_per_pixel=30,
#         nodata_val=int16_nodata,
#     )
#     Gnomonic_Warp(
#         [path.join("Moon", "Local", "SouthPole", "MOON_LRO_NAC_DEM_89S210E_4mp.tif")],
#         1737400.0,
#         "moon_gnom",
#         "SPole",
#         pbar,
#         meters_per_pixel=4,
#         nodata_val=float_nodata,
#     )
#     # Moon South Pole Overlay Data
#     # Pending Data_Downloader links to these
#     # Gnomonic_Warp(path.join("Moon","Local","SouthPole","SP_IceFavorabilityIndex.tif"), \
#     #     1737400.0, "moon_gnom", "SPole", pbar, 591)
#     # Gnomonic_Warp(path.join("Moon","Local","SouthPole","SP_TerrainType.tif"), \
#     #     1737400.0, "moon_gnom", "SPole", pbar, 591)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppGUI()
    window.show()
    # sys.exit(app.exec_())
    # time.sleep(10)
    # exit()
    app.exec_()
    