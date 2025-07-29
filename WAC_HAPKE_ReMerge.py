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

input_files = [
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350N0450.tiff"),  # 45 E  (right of prime meridian)
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350N1350.tiff"),  # 135 E
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350N2250.tiff"),  # 225 E
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350N3150.tiff"),  # 315 E (left of prime meridian)
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350S0450.tiff"),  # 45 E  (right of prime meridian)
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350S1350.tiff"),  # 135 E
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350S2250.tiff"),  # 225 E
    path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_E350S3150.tiff")   # 315 E (left of prime meridian)
    ]  
output_file = path.join(inputDir, "Moon","Global","RGB","WAC_HAPKE_3BAND_Merged.tiff")


# Read a known-good moon projection file:
other_moon_ds : gdal.Dataset = gdal.Open(path.join(inputDir, "Moon","Global","Lunar_LRO_LROC-WAC_Mosaic_global_100m_June2013.tif"), gdal.GA_ReadOnly)

proj_knowngood = other_moon_ds.GetProjection()


# -----------------------------------------------------------------------------
# 1. Read input metadata
# -----------------------------------------------------------------------------
infos = []
for fn in input_files:
    ds = gdal.Open(fn, gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"Cannot open {fn}")
    gt = ds.GetGeoTransform()
    px = gt[1]
    py = gt[5]
    xsize = ds.RasterXSize
    ysize = ds.RasterYSize

    minx = gt[0]
    maxy = gt[3]
    maxx = minx + xsize * px
    miny = maxy + ysize * py

    this_info = {
        "fn": fn, "ds": ds, "gt": gt,
        "px": px, "py": py,
        "minx": minx, "maxx": maxx,
        "miny": miny, "maxy": maxy,
        "xsize": xsize, "ysize": ysize
    }

    infos.append(this_info)
    print(f"info: {this_info}")

    # print(f"maxx: {maxx}, minx: {minx}")
    # print(f"maxy: {maxy}, miny: {miny}")

# print(f"infos: {json.dumps(infos, indent=4)}") # didnt work

# sanity‐check all inputs share the same pixel size & projection
px0 = infos[0]["px"]
py0 = infos[0]["py"]
proj0 = infos[0]["ds"].GetProjection()
for info in infos[1:]:
    if not math.isclose(info["px"], px0) or not math.isclose(info["py"], py0):
        raise RuntimeError("Pixel size mismatch among inputs")
    if info["ds"].GetProjection() != proj0:
        raise RuntimeError("Projection mismatch among inputs")

# -----------------------------------------------------------------------------
# 2. Determine full‐world extent, extending to the poles ±90°
# -----------------------------------------------------------------------------
minx_all = min(info["minx"] for info in infos)
maxx_all = max(info["maxx"] for info in infos)

# ─── Re‑center longitudes to [–½world … +½world] ───
world_width = maxx_all - minx_all
minx_all    = -0.5 * world_width
maxx_all    =  0.5 * world_width

miny_all = min(info["miny"] for info in infos)
maxy_all = max(info["maxy"] for info in infos)

# output raster dimensions
out_xsize = int((maxx_all - minx_all) / px0 + 0.5)
out_ysize = int((maxy_all - miny_all) / abs(py0) + 0.5)
out_ysize_exp = int(math.floor(out_ysize * 90.0/70.0))-2 # Expand to cover poles
print(f"maxx_all: {maxx_all}, minx_all: {minx_all}")
print(f"maxy_all: {maxy_all}, miny_all: {miny_all}")
print(f"px0: {px0}, py0: {py0}")
print(f"Data extents size: {out_xsize} x {out_ysize} pixels")
print(f"Output raster size: {out_xsize} x {out_ysize_exp} pixels")

# -----------------------------------------------------------------------------
# 3. Create the output and initialize pole regions to zero/nodata
# -----------------------------------------------------------------------------
driver : gdal.Driver = gdal.GetDriverByName("GTiff")
in_ds : gdal.Dataset = infos[0]["ds"] 
band_count = in_ds.RasterCount
data_type  = in_ds.GetRasterBand(1).DataType

out_ds : gdal.Dataset = driver.Create(output_file, out_xsize, out_ysize_exp, band_count, data_type)
if out_ds is None:
    raise RuntimeError(f"Cannot create {output_file}")

# assign geotransform & projection
geotrans_max_y = maxy_all + (out_ysize_exp - out_ysize) * abs(py0) / 2.0
out_gt = (minx_all, px0, 0, geotrans_max_y, 0, py0)
out_ds.SetGeoTransform(out_gt)
# out_ds.SetProjection(proj0) # use the same projection as the inputs

# with open(path.join(projDir, "moon_cyl.prj"), "r") as prj_file:
#     wkt_txt = prj_file.read()
# out_ds.SetProjection(wkt_txt) #replace with our own projection file

out_ds.SetProjection(proj_knowngood)  # use the known-good projection

# set nodata=0 and fill entire raster with zeros (so poles remain zero)
for b in range(1, band_count+1):
    band = out_ds.GetRasterBand(b)
    band.SetNoDataValue(0)
    band.Fill(0)

# -----------------------------------------------------------------------------
# 4. Blit each input tile into its correct offset
# -----------------------------------------------------------------------------
north_pole_offset = (out_ysize_exp - out_ysize) // 2

# for info in infos:
#     # column offset
#     xoff = int((info["minx"] - minx_all) / px0 + 0.5)

half_world = world_width * 0.5
for info in infos:
    # wrap tiles that start > +½world back into negative side
    orig_minx = info["minx"]
    if orig_minx > half_world:
        tile_minx = orig_minx - world_width
    else:
        tile_minx = orig_minx

    # column offset relative to new minx_all
    xoff = int((tile_minx - minx_all) / px0 + 0.5)

    if(xoff >= out_xsize):
        xoff -= out_xsize

    # xoff = int(tile_minx / px0)
    # row offset from the new 90°N top
    yoff = north_pole_offset + int((maxy_all - info["maxy"]) / abs(py0) + 0.5)

    for b in range(1, band_count+1):
        arr = info["ds"].GetRasterBand(b).ReadAsArray()
        print(f"Blitting {info['fn']} band {b} at xoff={xoff}, yoff={yoff}, arr.shape={arr.shape}")
        out_ds.GetRasterBand(b).WriteArray(arr, xoff, yoff)

    # close input
    info["ds"] = None

# -----------------------------------------------------------------------------
# 5. Flush to disk
# -----------------------------------------------------------------------------
out_ds.FlushCache()
out_ds = None

print(f"Wrote full‐pole mosaic: {output_file}")