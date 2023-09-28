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

#######################################
### GLOBALS ###########################

thisDir = os.path.dirname(os.path.abspath(__file__))
inputDir = os.path.join(thisDir, "input")
outputDir = os.path.join(thisDir, "output")
productsDir = os.path.join(thisDir, "products")
projDir = os.path.join(thisDir, "proj")

#dataPaused = False

termUseColor = True

####################################
### MATH ###########################

def ppd_to_ppm(ppd, radius):
    return 2 * 3.1415962 * radius / (360 * ppd)

#######################################
### Actions ###########################

def playGreeting():
    global termUseColor

    if(termUseColor):
        print(sc.greetingString)
    else:
        print(sc.greetingStringNoColor)

    print("\nPlanetDataTools - Data_Preprocessor")
    print("---------------------")


def progress_callback(complete, message, data):
    percent = int(complete * 100)  # round to integer percent
    data.update(percent)  # update the progressbar
    return 1

def Gnomonic_Warp(inputFiles: list, radius: float, prjFileRoot: str, \
    prjFileSide: str, progBar: pb.ProgressBar, meters_per_pixel = 0.0, \
    forceFullSideExtents = False, input_nodata_val = None, nodata_val = 0, warpoptions = None):
    print("-------------------")
    print("-- Gnomonic_Warp --")
    print("\t inputFile:",inputFiles)
    print("\t radius:",radius)
    prjFile = prjFileRoot + "_" + prjFileSide + ".prj"
    print("\t prjFile:",prjFile)
    
    inpath = []

    for inputFile in inputFiles:
        inpath.append(path.join(inputDir,inputFile))
    outpath = path.join(outputDir,inputFiles[0])
    outpath_split = path.splitext(outpath)
    # outpath = outpath_split[0] + "_Gnom_" + prjFileSide + outpath_split[1]
    outpath = outpath_split[0] + "_Gnom_" + prjFileSide + ".tif"

    if(os.path.exists(outpath)):
        print("WARNING: there is already a file at "+outpath+"; skipped this warp.")
        return
    elif(not path.exists(path.split(outpath)[0])):
        print("Making new output directory \"" + path.split(outpath)[0] +"\"")
        os.makedirs(path.split(outpath)[0])
    
    radius_plus = radius * 33.0/32.0

    if(warpoptions == None):
        if(forceFullSideExtents):
            warpoptions = gdal.WarpOptions( \
                resampleAlg="bilinear", \
                dstSRS=path.join(projDir, prjFile),
                outputBounds=[-radius_plus, -radius_plus, radius_plus, radius_plus],
                xRes=meters_per_pixel,
                yRes=meters_per_pixel,
                srcNodata=input_nodata_val,
                dstNodata=nodata_val,
                format="GTiff",
                creationOptions = ['COMPRESS=LZW'],
                multithread=True,
                callback=progress_callback,
                callback_data=progBar \
                )
        else:
            warpoptions = gdal.WarpOptions( \
                resampleAlg="bilinear", \
                dstSRS=path.join(projDir, prjFile),
                xRes=meters_per_pixel,
                yRes=meters_per_pixel,
                srcNodata=input_nodata_val,
                dstNodata=nodata_val,
                format="GTiff",
                creationOptions = ['COMPRESS=LZW'],
                multithread=True,
                callback=progress_callback,
                callback_data=progBar \
                )

    
    progBar.start()
    gdal.Warp(outpath, inpath, options=warpoptions)
    progBar.finish()

def Gnomonic_Warp_Global(inputFiles: list, radius: float, prjFileRoot: str, \
    progBar: pb.ProgressBar, meters_per_pixel = 0.0, input_nodata_val = None, nodata_val = 0):
    print("--------------------------")
    print("-- Gnomonic_Warp_Global --")

    Gnomonic_Warp(inputFiles, radius, prjFileRoot, "Eq_0", progBar, meters_per_pixel, True, input_nodata_val, nodata_val)
    Gnomonic_Warp(inputFiles, radius, prjFileRoot, "Eq_90", progBar, meters_per_pixel, True, input_nodata_val, nodata_val)
    Gnomonic_Warp(inputFiles, radius, prjFileRoot, "Eq_180", progBar, meters_per_pixel, True, input_nodata_val, nodata_val)
    Gnomonic_Warp(inputFiles, radius, prjFileRoot, "Eq_270", progBar, meters_per_pixel, True, input_nodata_val, nodata_val)
    Gnomonic_Warp(inputFiles, radius, prjFileRoot, "NPole", progBar, meters_per_pixel, True, input_nodata_val, nodata_val)
    Gnomonic_Warp(inputFiles, radius, prjFileRoot, "SPole", progBar, meters_per_pixel, True, input_nodata_val, nodata_val)


#######################################
### MAIN ##############################

# Use a larger multiplier here to avoid RAM issues with loading/storing the huge datasets 
# large_datasets_mpp_mult = 1
large_datasets_mpp_mult = 4

# Nodata value is usually 0, but it's different for some things:
int16_nodata = -32768 # Datasets are usually consistent about this
uint16_nodata = 0
int32_nodata = -2147483648
float_nodata = -1e32
double_nodata = -1e32

if __name__ == "__main__":
    playGreeting()

    print("GDAL Version:", gdal.VersionInfo())

    pbar = pb.ProgressBar()

    # Moon Global
    Gnomonic_Warp_Global([path.join("Moon","Global","Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif")], \
        1737400.0, "moon_gnom", pbar, meters_per_pixel=118 * large_datasets_mpp_mult)
    Gnomonic_Warp_Global([path.join("Moon","Global","Lunar_LRO_LROC-WAC_Mosaic_global_100m_June2013.tif")], \
        1737400.0, "moon_gnom", pbar, meters_per_pixel=100 * large_datasets_mpp_mult)
    # Moon Apollo Sites
    Gnomonic_Warp([path.join("Moon","Local","Apollo17","APOLLO17_DTM_150CM.TIFF")], \
        1737400.0, "moon_gnom", "Eq_0", pbar, meters_per_pixel=1.5, nodata_val=float_nodata)
    Gnomonic_Warp([path.join("Moon","Local","Apollo17","APOLLO17_ORTHOMOSAIC_50CM.TIFF")], \
        1737400.0, "moon_gnom", "Eq_0", pbar, meters_per_pixel=0.5)
    Gnomonic_Warp([path.join("Moon","Local","Apollo15","LRO_NAC_DEM_Apollo_15_26N004E_150cmp.tif")], \
        1737400.0, "moon_gnom", "Eq_0", pbar, meters_per_pixel=1.5 * 2, nodata_val=float_nodata)
    #     #TODO this ^ needs its nodata value set to our standardized value
    Gnomonic_Warp([path.join("Moon","Local","Apollo15","Moon_LRO_NAC_Mosaic_26N004E_50cmp.tif")], \
        1737400.0, "moon_gnom", "Eq_0", pbar, meters_per_pixel=0.5 * 4) 
        #TODO this ^ is giving an error partway through:
        # ERROR 1: LZWDecode:Not enough data at scanline 47450 (short 53477 bytes)
        # ERROR 1: TIFFReadEncodedStrip() failed.
        # ERROR 1: C:\Users\conno\Documents\GitHub\PlanetDataTools\input\Moon\Local\Apollo15\Moon_LRO_NAC_Mosaic_26N004E_50cmp.tif,
        #    band 1: IReadBlock failed at X offset 0, Y offset 47450: TIFFReadEncodedStrip() failed.
    # Moon South Pole Altimetry
    Gnomonic_Warp([path.join("Moon","Local","SouthPole","LRO_LOLA_DEM_SPolar875_10m.tif")], \
        1737400.0, "moon_gnom", "SPole", pbar, meters_per_pixel=10, nodata_val=int16_nodata)
    Gnomonic_Warp([path.join("Moon","Local","SouthPole","LRO_LOLA_DEM_SPole75_30m.tif")], \
        1737400.0, "moon_gnom", "SPole", pbar, meters_per_pixel=30, nodata_val=int16_nodata)
    Gnomonic_Warp([path.join("Moon","Local","SouthPole","MOON_LRO_NAC_DEM_89S210E_4mp.tif")], \
        1737400.0, "moon_gnom", "SPole", pbar, meters_per_pixel=4, nodata_val=float_nodata)
    # Moon South Pole Overlay Data
    # Pending Data_Downloader links to these
    # Gnomonic_Warp(path.join("Moon","Local","SouthPole","SP_IceFavorabilityIndex.tif"), \
    #     1737400.0, "moon_gnom", "SPole", pbar, 591)
    # Gnomonic_Warp(path.join("Moon","Local","SouthPole","SP_TerrainType.tif"), \
    #     1737400.0, "moon_gnom", "SPole", pbar, 591)

    # Mars
    Gnomonic_Warp_Global([path.join("Mars","Global","Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif")], \
        3396190.0, "mars_gnom", pbar, meters_per_pixel=200 * large_datasets_mpp_mult)
    # This one is "artisticly" colored, which doesn't look good in 3D and is not accurate.
    # Disabled for now.
    #Gnomonic_Warp_Global(path.join("Mars","Global","Mars_Viking_MDIM21_ClrMosaic_global_232m.tif"), \
    #    3396190.0, "mars_gnom", pbar, meters_per_pixel=232 * large_datasets_mpp_mult)
    # This one is at least close to color-accurate.
    Gnomonic_Warp_Global([path.join("Mars","Global","Mars_Viking_ClrMosaic_global_925m.tif")], \
        3396190.0, "mars_gnom", pbar, meters_per_pixel=925)
        
    Gnomonic_Warp([path.join("Mars","Local","Jezero","J03_045994_1986_J03_046060_1986_20m_DTM.tif")], \
        3396190.0, "mars_gnom", "Eq_90", pbar, meters_per_pixel=20, nodata_val=float_nodata)
    Gnomonic_Warp([path.join("Mars","Local","Jezero","J03_045994_1986_XN_18N282W_6m_ORTHO.tif")], \
        3396190.0, "mars_gnom", "Eq_90", pbar, meters_per_pixel=6)
    Gnomonic_Warp([path.join("Mars","Local","Jezero","JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first.tif")], \
        3396190.0, "mars_gnom", "Eq_90", pbar, meters_per_pixel=0.25 * large_datasets_mpp_mult)
    Gnomonic_Warp([path.join("Mars","Local","Jezero","DTEEC_045994_1985_046060_1985_U01.IMG")], \
        3396190.0, "mars_gnom", "Eq_90", pbar, meters_per_pixel=1, nodata_val=float_nodata)
    
    #TODO Gale, InSight, LavaFlows, Misc datasets

    ########################
    ### WORK IN PROGRESS ###
    ########################

    # Ceres
    Gnomonic_Warp_Global([path.join("Ceres","Global","Ceres_Dawn_FC_HAMO_DTM_DLR_Global_60ppd_Oct2016.tif")], \
        487300.0, "ceres_gnom", pbar, meters_per_pixel=142)
    #TODO 
    '''
    ERROR 1: PROJ: proj_create_operations: Source and target ellipsoid do not belong to the same celestial body
    ERROR 6: Cannot find coordinate operations from 
    `PROJCRS["Equirectangular CERES",BASEGEOGCRS["GCS_CERES",DATUM["D_CERES",ELLIPSOID["CERES_localRadius",470000,0,LENGTHUNIT["metre",1,ID["EPSG",9001]]]],PRIMEM["Reference_Meridian",0,ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9122]]]],CONVERSION["Equidistant Cylindrical",METHOD["Equidistant Cylindrical",ID["EPSG",1028]],PARAMETER["Latitude of 1st standard parallel",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],PARAMETER["Longitude of natural origin",180,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting",east,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],AXIS["northing",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]' 
    to 
    `PROJCRS["Ceres_Gnomonic_Eq90",BASEGEOGCRS["Ceres 2000",DATUM["D_Ceres_2000",ELLIPSOID["Ceres_2000_IAU_IAG",487300,0,LENGTHUNIT["metre",1,ID["EPSG",9001]]]],PRIMEM["Greenwich",0,ANGLEUNIT["Decimal_Degree",0.0174532925199433]]],CONVERSION["unnamed",METHOD["Gnomonic"],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["Decimal_Degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",90,ANGLEUNIT["Decimal_Degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]'
    '''


    # Mercury
    Gnomonic_Warp_Global([path.join("Mercury","Global","Mercury_Messenger_USGS_DEM_Global_665m_v2.tif")], \
        2493700, "mercury_gnom", pbar, meters_per_pixel=665)
    Gnomonic_Warp_Global([path.join("Mercury","Global","Mercury_MESSENGER_MDIS_Basemap_LOI_Mosaic_Global_166m.tif")], \
        2493700, "mercury_gnom", pbar, meters_per_pixel=166)
    #TODO 
    '''
    ERROR 1: PROJ: proj_create_operations: Source and target ellipsoid do not belong to the same celestial body
    ERROR 6: Cannot find coordinate operations from 
    `PROJCRS["Equirectangular Mercury",BASEGEOGCRS["GCS_Mercury",DATUM["D_Mercury",ELLIPSOID["Mercury_localRadius",2439400,0,LENGTHUNIT["metre",1,ID["EPSG",9001]]]],PRIMEM["Reference_Meridian",0,ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9122]]]],CONVERSION["Equidistant Cylindrical",METHOD["Equidistant Cylindrical",ID["EPSG",1028]],PARAMETER["Latitude of 1st standard parallel",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],PARAMETER["Longitude of natural origin",180,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting",east,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],AXIS["northing",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]' 
    to 
    `PROJCRS["Mercury_Gnomonic_Eq90",BASEGEOGCRS["Mercury 2000",DATUM["D_Mercury_2000",ELLIPSOID["Mercury_2000_IAU_IAG",2493700,0,LENGTHUNIT["metre",1,ID["EPSG",9001]]]],PRIMEM["Greenwich",0,ANGLEUNIT["Decimal_Degree",0.0174532925199433]]],CONVERSION["unnamed",METHOD["Gnomonic"],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["Decimal_Degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",90,ANGLEUNIT["Decimal_Degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]'
    '''

    # Phobos
    Gnomonic_Warp_Global([path.join("Mars", "Phobos","Global","Phobos_Viking_Mosaic_40ppd_DLRcontrol.tif")], \
        13000, "phobos_gnom", pbar, meters_per_pixel= 5.67)
    Gnomonic_Warp_Global([path.join("Mars", "Phobos","Global","Phobos_ME_HRSC_DEM_Global_2ppd.tif")], \
        13000, "phobos_gnom", pbar, meters_per_pixel=113)
    #TODO
    '''
    ERROR 1: PROJ: proj_create_operations: Source and target ellipsoid do not belong to the same celestial body
    ERROR 6: Cannot find coordinate operations from 
    `PROJCRS["SimpleCylindrical Phobos",BASEGEOGCRS["GCS_Phobos",DATUM["D_Phobos",ELLIPSOID["Phobos",11100,0,LENGTHUNIT["metre",1,ID["EPSG",9001]]]],PRIMEM["Reference_Meridian",0,ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9122]]]],CONVERSION["Equidistant Cylindrical",METHOD["Equidistant Cylindrical",ID["EPSG",1028]],PARAMETER["Latitude of 1st standard parallel",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],PARAMETER["Longitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting",east,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],AXIS["northing",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]' 
    to 
    `PROJCRS["Phobos_Gnomonic_Eq90",BASEGEOGCRS["Phobos 2000",DATUM["D_Phobos_2000",ELLIPSOID["Phobos_2000_IAU_IAG",13000,0,LENGTHUNIT["metre",1,ID["EPSG",9001]]]],PRIMEM["Greenwich",0,ANGLEUNIT["Decimal_Degree",0.0174532925199433]]],CONVERSION["unnamed",METHOD["Gnomonic"],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["Decimal_Degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",90,ANGLEUNIT["Decimal_Degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]'
    '''

    # Vesta
    Gnomonic_Warp_Global([path.join("Vesta","Global","Vesta_Dawn_HAMO_DTM_DLR_Global_48ppd.tif")], \
        289000, "vesta_gnom", pbar, meters_per_pixel=105)
    

    # Io
    Gnomonic_Warp_Global([path.join("Jupiter", "Io","Global","Io_GalileoSSI-Voyager_Global_Mosaic_ClrMerge_1km.tif")], \
        1821600, "io_gnom", pbar, meters_per_pixel=1000)
    # no info on local


    # Europa
    Gnomonic_Warp_Global([path.join("Jupiter", "Europa","Global","Europa_Voyager_GalileoSSI_global_mosaic_500m.tif")], \
        1560800, "europa_gnom", pbar, meters_per_pixel=500)


    # Ganymede
    Gnomonic_Warp_Global([path.join("Jupiter", "Ganymede","Global","Ganymede_Voyager_GalileoSSI_Global_ClrMosaic_1435m.tif")], \
        2634100, "ganymede_gnom", pbar, meters_per_pixel=1435)


    # Enceladus
    Gnomonic_Warp_Global([path.join("Saturn", "Enceladus","Global","enceladus_2019pm_radius.tif")], \
        252100, "enceladus_gnom", pbar, meters_per_pixel=2200)
    Gnomonic_Warp_Global([path.join("Saturn", "Enceladus","Global","Enceladus_Cassini_ISS_Global_Mosaic_100m_HPF.tif")], \
        252100, "enceladus_gnom", pbar, meters_per_pixel=100)
    Gnomonic_Warp_Global([path.join("Saturn", "Enceladus","Global","enceladus_2019pm_nps_radius.tif")], \
        252100, "enceladus_gnom", pbar, meters_per_pixel=2200)
    Gnomonic_Warp_Global([path.join("Saturn", "Enceladus","Global","enceladus_2019pm_sps_radius.tif")], \
        252100, "enceladus_gnom", pbar, meters_per_pixel=2200)
    # under TODO
    # nps and sps are ancillary data and no context is given about mpp


    # Titan
    #Gnomonic_Warp_Global([path.join("Saturn", "Titan","Global","gtdr-data.zip")], \
    #    2575150, "titan_gnom", pbar, meters_per_pixel=1000)
    # no info on mpp
    Gnomonic_Warp_Global([path.join("Saturn", "Titan","Global","Titan_ISS_Globe_65Sto45N_450M_AvgMos.tif")], \
        2575150, "titan_gnom", pbar, meters_per_pixel=450)
    Gnomonic_Warp_Global([path.join("Saturn", "Titan","Global","Titan_ISS_P19658_Mosaic_Global_4km.tif")], \
        2575150, "titan_gnom", pbar, meters_per_pixel=4000)


    # Dione
    # add valid path


    # Iapetus
    # add valid path


    # Triton
    Gnomonic_Warp_Global([path.join("Neptune", "Triton","Global","Triton_Voyager2_ClrMosaic_GlobalFill_600m.tif")], \
        1353400, "triton_gnom", pbar, meters_per_pixel=600)


    # Pluto
    Gnomonic_Warp_Global([path.join("Pluto","Global","Pluto_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif")], \
        1188300, "pluto_gnom", pbar, meters_per_pixel=300)
    Gnomonic_Warp_Global([path.join("Pluto","Global","Pluto_NewHorizons_Global_DEM_300m_Jul2017_16bit.tif")], \
        1188300, "pluto_gnom", pbar, meters_per_pixel=300)

    ########################
    ### WORK IN PROGRESS ###
    ########################
        

    # Venus

    if(not path.exists(path.join(inputDir,"Venus","Global","Topography","2DSignal312_625_50tol_0.01.tif"))):
        if(path.exists(path.join(inputDir,"Venus","Global","Topography","2DSignal312_625_50tol_0.01.png"))):
            gdal.Translate(path.join(inputDir,"Venus","Global","Topography","2DSignal312_625_50tol_0.01.tif"),
                path.join(inputDir,"Venus","Global","Topography","2DSignal312_625_50tol_0.01.png"),
                options=gdal.TranslateOptions(resampleAlg="bilinear", \
                        outputBounds=[-180, 90, 180, -90],
                        outputSRS=path.join(projDir, "venus_cyl.prj"),
                        format="GTiff",
                        noData=0,
                        creationOptions = ['COMPRESS=LZW'])
                )    

    # Gnomonic_Warp_Global([path.join("Venus","Global","Topography","2DSignal312_625_50tol_0.01.tif")], \
    #     6.0518e6, "venus_gnom", pbar, meters_per_pixel=2*3.14159265*6.051e6/625.0, input_nodata_val=0, nodata_val=0)

    # if(not path.exists(path.join(inputDir,"Venus","Global","Topography","2DOriginal312_625_50.tif"))):
    #     gdal.Translate(path.join(inputDir,"Venus","Global","Topography","2DOriginal312_625_50.tif"),
    #         path.join(inputDir,"Venus","Global","Topography","2DOriginal312_625_50.png"),
    #         options=gdal.TranslateOptions(resampleAlg="bilinear", \
    #                 outputBounds=[-180, 90, 180, -90],
    #                 outputSRS=path.join(projDir, "venus_cyl.prj"),
    #                 format="GTiff",
    #                 noData=0,
    #                 creationOptions = ['COMPRESS=LZW'])
    #         )    

    # Gnomonic_Warp_Global([path.join("Venus","Global","Topography","2DOriginal312_625_50.tif")], \
    #     6.0518e6, "venus_gnom", pbar, meters_per_pixel=2*3.14159265*6.051e6/625.0, input_nodata_val=0, nodata_val=0)

    Gnomonic_Warp_Global([path.join("Venus","Global","Topography","Venus_Magellan_Topography_Global_4641m_v02.tif")], \
        6.0518e6, "venus_gnom", pbar, meters_per_pixel=4641, nodata_val=int16_nodata)

    # Gnomonic_Warp_Global([path.join("Venus","Global","Venus_Magellan_C3-MDIR_Colorized_Global_Mosaic_4641m.tif")], \
    #     6.0518e6, "venus_gnom", pbar, meters_per_pixel=4641) # Artist Colorized
    
    Gnomonic_Warp_Global([path.join("Venus","Global","Venus_Magellan_C3-MDIR_Global_Mosaic_2025m.tif")], \
        6.0518e6, "venus_gnom", pbar, meters_per_pixel=2025)

    # Earth
    
    ##https://visibleearth.nasa.gov/images/57747/blue-marble-clouds
    #DownloadIfNotExists(path.join("Earth","Global","Clouds"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud.W.2001210.21600x21600.png")

    # Use a larger multiplier here to avoid RAM issues with loading/storing the huge datasets
    blue_marble_mpp_mult = 1
    # blue_marble_mpp_mult = 2

    #21600x21600 pixels
    blue_marble_mpp_22k = 463.77
    #10800x10800 pixels
    blue_marble_mpp_11k = 927.55

    # https://earthobservatory.nasa.gov/features/NightLights
    Gnomonic_Warp_Global([path.join("Earth","Global","BlackMarble","BlackMarble_2016_A1_geo_gray.tif"), \
        path.join("Earth","Global","BlackMarble","BlackMarble_2016_B1_geo_gray.tif"),  \
        path.join("Earth","Global","BlackMarble","BlackMarble_2016_C1_geo_gray.tif"),  \
        path.join("Earth","Global","BlackMarble","BlackMarble_2016_D1_geo_gray.tif"),  \
        path.join("Earth","Global","BlackMarble","BlackMarble_2016_A2_geo_gray.tif"),  \
        path.join("Earth","Global","BlackMarble","BlackMarble_2016_B2_geo_gray.tif"),  \
        path.join("Earth","Global","BlackMarble","BlackMarble_2016_C2_geo_gray.tif"),  \
        path.join("Earth","Global","BlackMarble","BlackMarble_2016_D2_geo_gray.tif")], \
        6.378137e6, "earth_gnom", pbar, meters_per_pixel=blue_marble_mpp_22k * blue_marble_mpp_mult)

    #https://visibleearth.nasa.gov/images/73934/topography
    #scaled 0 to +6400 meters
    Gnomonic_Warp_Global([path.join("Earth","Global","Topography","gebco_08_rev_elev_A1_grey_geo.tif"), \
        path.join("Earth","Global","Topography","gebco_08_rev_elev_B1_grey_geo.tif"),  \
        path.join("Earth","Global","Topography","gebco_08_rev_elev_C1_grey_geo.tif"),  \
        path.join("Earth","Global","Topography","gebco_08_rev_elev_D1_grey_geo.tif"),  \
        path.join("Earth","Global","Topography","gebco_08_rev_elev_A2_grey_geo.tif"),  \
        path.join("Earth","Global","Topography","gebco_08_rev_elev_B2_grey_geo.tif"),  \
        path.join("Earth","Global","Topography","gebco_08_rev_elev_C2_grey_geo.tif"),  \
        path.join("Earth","Global","Topography","gebco_08_rev_elev_D2_grey_geo.tif")],  \
        6.378137e6, "earth_gnom", pbar, meters_per_pixel=blue_marble_mpp_11k * blue_marble_mpp_mult)

    #https://visibleearth.nasa.gov/images/73963/bathymetry
    #scaled -8000 to 0 meters
    Gnomonic_Warp_Global([path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_A1_grey_geo.tif"), \
        path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_B1_grey_geo.tif"),  \
        path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_C1_grey_geo.tif"),  \
        path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_D1_grey_geo.tif"),  \
        path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_A2_grey_geo.tif"),  \
        path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_B2_grey_geo.tif"),  \
        path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_C2_grey_geo.tif"),  \
        path.join("Earth","Global","Bathymetry","gebco_08_rev_bath_D2_grey_geo.tif")],  \
        6.378137e6, "earth_gnom", pbar, meters_per_pixel=blue_marble_mpp_11k * blue_marble_mpp_mult)

    # Georeference Blue Marble vis color PNGs then get gnomonic warps of them
    #TODO clouds

    #https://gis.stackexchange.com/a/334024/144120
    print("Wait for georeferencing of blue marble datasets...")
    print("A1")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A1.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A1.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A1.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[-180, 90, -90, 0],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )
    print("B1")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B1.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B1.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B1.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[-90, 90, 0, 0],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )
    print("C1")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C1.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C1.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C1.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[0, 90, 90, 0],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )
    print("D1")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D1.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D1.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D1.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[90, 90, 180, 0],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )
    print("A2")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A2.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A2.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A2.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[-180, 0, -90, -90],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )
    print("B2")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B2.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B2.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B2.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[-90, 0, 0, -90],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )    
    print("C2")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C2.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C2.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C2.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[0, 0, 90, -90],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )    
    print("D2")
    if(not path.exists(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D2.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D2.tif"),
            path.join(inputDir,"Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D2.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[90, 0, 180, -90],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )    


    Gnomonic_Warp_Global([path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A1.tif"), \
        path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B1.tif"),  \
        path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C1.tif"),  \
        path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D1.tif"),  \
        path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.A2.tif"),  \
        path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.B2.tif"),  \
        path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.C2.tif"),  \
        path.join("Earth","Global","BlueMarbleOctober","world.200410.3x21600x21600.D2.tif")],  \
        6.378137e6, "earth_gnom", pbar, meters_per_pixel=blue_marble_mpp_22k * blue_marble_mpp_mult)


    
    print("Wait for georeferencing of blue marble cloud datasets...")
    print("West")
    if(not path.exists(path.join(inputDir,"Earth","Global","Clouds","cloud.W.2001210.21600x21600.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","Clouds","cloud.W.2001210.21600x21600.tif"),
            path.join(inputDir,"Earth","Global","Clouds","cloud.W.2001210.21600x21600.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[-180, 90, 0, -90],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )

    print("East")
    if(not path.exists(path.join(inputDir,"Earth","Global","Clouds","cloud.E.2001210.21600x21600.tif"))):
        gdal.Translate(path.join(inputDir,"Earth","Global","Clouds","cloud.E.2001210.21600x21600.tif"),
            path.join(inputDir,"Earth","Global","Clouds","cloud.E.2001210.21600x21600.png"),
            options=gdal.TranslateOptions(resampleAlg="bilinear", \
                    outputBounds=[0, 90, 180, -90],
                    outputSRS="WGS84",
                    format="GTiff",
                    creationOptions = ['COMPRESS=LZW'])
            )

    Gnomonic_Warp_Global([path.join("Earth","Global","Clouds","cloud.W.2001210.21600x21600.tif"), \
        path.join("Earth","Global","Clouds","cloud.E.2001210.21600x21600.tif")],  \
        6.378137e6, "earth_gnom", pbar, meters_per_pixel=blue_marble_mpp_11k * blue_marble_mpp_mult)


    Gnomonic_Warp([path.join("Earth","Local","Grand Canyon","gc_dem.tif")], \
        6.378137e6, "earth_gnom", "Eq_270", pbar, meters_per_pixel=30, input_nodata_val=0, nodata_val=uint16_nodata)

    Gnomonic_Warp([path.join("Earth","Local","Hawaii","elevhii0100a.tif")], \
        6.378137e6, "earth_gnom", "Eq_180", pbar, meters_per_pixel=100, nodata_val=int16_nodata)
        
    Gnomonic_Warp([path.join("Earth","Local","San Francisco Bay Area", "dem30m", "w001001.adf")], \
        6.378137e6, "earth_gnom", "Eq_270", pbar, meters_per_pixel=30, nodata_val=int16_nodata)
    
    if False:
        #677 is Everest; others are surroundings
        for i in range(642,647):
            Gnomonic_Warp([path.join("Earth","Local","Himalayas", f"HMA_DEM8m_MOS_20170716_tile-{i}.tif")], \
                6.378137e6, "earth_gnom", "Eq_90", pbar, meters_per_pixel=8, nodata_val=float_nodata)
        for i in range(675,680):
            Gnomonic_Warp([path.join("Earth","Local","Himalayas", f"HMA_DEM8m_MOS_20170716_tile-{i}.tif")], \
                6.378137e6, "earth_gnom", "Eq_90", pbar, meters_per_pixel=8, nodata_val=float_nodata)
        for i in range(708,713):
            Gnomonic_Warp([path.join("Earth","Local","Himalayas", f"HMA_DEM8m_MOS_20170716_tile-{i}.tif")], \
                6.378137e6, "earth_gnom", "Eq_90", pbar, meters_per_pixel=8, nodata_val=float_nodata)

    if True:
        #677 is Everest; others are surroundings
        Gnomonic_Warp([path.join("Earth","Local","Himalayas", f"HMA_DEM8m_MOS_20170716_tile-677.tif")], \
            6.378137e6, "earth_gnom", "Eq_90", pbar, meters_per_pixel=8, nodata_val=float_nodata)
            
    if False:
        Gnomonic_Warp([path.join("Earth","Local","Caucasus", "dem_200_000.tif")], \
            6.378137e6, "earth_gnom", "NPole", pbar, meters_per_pixel=50, nodata_val=float_nodata)