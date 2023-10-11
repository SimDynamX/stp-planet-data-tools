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
# import progressbar as pb

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


def progress_callback(complete, message, data: QProgressBar):
    percent = int(complete * 100)  # round to integer percent
    data.setValue(percent)  # update the progressbar
    return 1


def Gnomonic_Warp(
    inputFiles: list,
    radius: float,
    prjFileRoot: str,
    prjFileSide: str,
    progBar: QProgressBar,
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
        inputFile_relative = path.relpath(inputFile, inputDir)
        inpath.append(path.join(inputDir, inputFile_relative))
    
    outpath = path.join(outputDir, path.relpath(inputFiles[0], inputDir))
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

    # progBar.start()
    gdal.Warp(outpath, inpath, options=warpoptions)
    # progBar.finish()


def Gnomonic_Warp_Global(
    inputFiles: list,
    radius: float,
    prjFileRoot: str,
    progBar: QProgressBar,
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

        # # Widget for radius
        # self.radius_input = QDoubleSpinBox()
        # self.radius_input.setRange(0, 10000)  # Example range
        # layout.addWidget(QLabel("Radius:"))
        # layout.addWidget(self.radius_input)

        self.planet_data = {
            'Ceres':{
                'proj': 'ceres_gnom',
                'radius': 473000.0
            },
            'Earth':{
                'proj': 'earth_gnom',
                'radius': 6.378137e6
            },
            'Enceladus':{
                'proj': 'enceladus_gnom',
                'radius': 252100.0
            },
            'Europa':{
                'proj': 'europa_gnom',
                'radius': 1560800.0
            },
            'Ganymede':{
                'proj': 'ganymede_gnom',
                'radius': 2634100.0
            },
            'Io':{
                'proj': 'io_gnom',
                'radius': 1821600.0
            },
            'Mars':{
                'proj': 'mars_gnom',
                'radius': 3396190.0
            },
            'Mercury':{
                'proj': 'mercury_gnom',
                'radius': 2493700.0
            },
            'Moon':{
                'proj': 'moon_gnom',
                'radius': 1737400.0
            },
            'Phobos':{
                'proj': 'phobos_gnom',
                'radius': 13000.0
            },
            'Pluto':{
                'proj': 'pluto_gnom',
                'radius': 1188300.0
            },
            'Titan':{
                'proj': 'titan_gnom',
                'radius': 2575150.0
            },
            'Triton':{
                'proj': 'triton_gnom',
                'radius': 1353400.0
            },
            'Venus':{
                'proj': 'venus_gnom',
                'radius': 6.0518e6
            },
            'Vesta':{
                'proj': 'vesta_gnom',
                'radius': 289000.0
            },
            }
        # Widgets for string inputs
        self.prjFileRoot_combo = QComboBox()
        self.prjFileRoot_combo.addItems(self.planet_data.keys())
        layout.addWidget(QLabel("Planet:"))
        layout.addWidget(self.prjFileRoot_combo)

        self.prjFileSide_combo = QComboBox()
        self.prjFileSide_combo.addItems(["Eq_0", "Eq_90","Eq_180","Eq_270","NPole","SPole","Global"])
        layout.addWidget(QLabel("Side:"))
        layout.addWidget(self.prjFileSide_combo)

        # Progress Bar
        self.progBar = QProgressBar()
        self.progBar.setRange(0, 100)
        self.progBar.setValue(0)
        layout.addWidget(self.progBar)

        # Other parameters with default values (as example)
        self.mpp_input = QDoubleSpinBox()
        self.mpp_input.setRange(0, 1000)  # Example range
        layout.addWidget(QLabel("Meters per Pixel:"))
        layout.addWidget(self.mpp_input)

    
        # self.forceFullSideExtents_chk = QCheckBox("Force Full Side Extents")
        # layout.addWidget(self.forceFullSideExtents_chk)


        # # Additional checkboxes for function selection
        # self.run_gnomonic_warp_checkbox = QCheckBox("Run Gnomonic_Warp")
        # self.run_gnomonic_warp_global_checkbox = QCheckBox("Run Gnomonic_Warp_Global")

        # # By default, run Gnomonic_Warp is selected
        # self.run_gnomonic_warp_checkbox.setChecked(True)

        # layout.addWidget(self.run_gnomonic_warp_checkbox)
        # layout.addWidget(self.run_gnomonic_warp_global_checkbox)

        # # Connect the stateChanged signal for mutual exclusion
        # self.run_gnomonic_warp_checkbox.stateChanged.connect(self.toggle_global_checkbox)
        # self.run_gnomonic_warp_global_checkbox.stateChanged.connect(self.toggle_warp_checkbox)
        

        # Submit button
        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.submit)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def toggle_global_checkbox(self):
        if self.run_gnomonic_warp_checkbox.isChecked():
            self.run_gnomonic_warp_global_checkbox.setChecked(False)

    def toggle_warp_checkbox(self):
        if self.run_gnomonic_warp_global_checkbox.isChecked():
            self.run_gnomonic_warp_checkbox.setChecked(False)

    def add_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_name:
            self.file_list.addItem(file_name)

    def submit(self):
        inputFiles = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        planet_choice = self.prjFileRoot_combo.currentText()

        radius = self.planet_data[planet_choice]['radius']
        prjFileRoot = self.planet_data[planet_choice]['proj']
        prjFileSide = self.prjFileSide_combo.currentText()
        progBar = self.progBar
        meters_per_pixel = self.mpp_input.value()
        # forceFullSideExtents = self.forceFullSideExtents_chk.isChecked()
        if self.prjFileSide_combo == "Global":
            Gnomonic_Warp_Global(inputFiles,radius,prjFileRoot,progBar,
            meters_per_pixel)#,input_nodata_val=None#,nodata_val=0)
        else:
            Gnomonic_Warp(
                inputFiles, radius, prjFileRoot, prjFileSide, progBar, 
                meters_per_pixel=meters_per_pixel, forceFullSideExtents=False
            )
            
           


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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppGUI()
    window.show()
    # sys.exit(app.exec_())
    # time.sleep(10)
    # exit()
    app.exec_()
    