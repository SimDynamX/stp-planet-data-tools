# Copyright 2026 SimDynamX LLC

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

from osgeo import gdal, osr
from os import path
import numpy as np


thisDir = os.path.dirname(os.path.abspath(__file__))
inputDir = os.path.join(thisDir, "input")
outputDir = os.path.join(thisDir, "output")
productsDir = os.path.join(thisDir, "products")
projDir = os.path.join(thisDir, "proj")

VESTA_RADIUS_M = 255000.0

input_path = path.join(
    inputDir, 
    "Vesta",
    "Global",
    "Vesta_Dawn_HAMO_DTM_DLR_Global_48ppd.tif",
)

base, ext = path.splitext(input_path)
output_path = f"{base}_Altitude{ext}"

src_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
if src_ds is None:
    raise RuntimeError(f"Failed to open input raster: {input_path}")

src_band = src_ds.GetRasterBand(1)
nodata = src_band.GetNoDataValue()

xsize = src_ds.RasterXSize
ysize = src_ds.RasterYSize

driver = gdal.GetDriverByName("GTiff")
dst_ds = driver.Create(
    output_path,
    xsize,
    ysize,
    1,
    gdal.GDT_Float32,
    options=[
        "TILED=YES",
        "COMPRESS=LZW",
        "BIGTIFF=IF_SAFER",
    ],
)
if dst_ds is None:
    raise RuntimeError(f"Failed to create output raster: {output_path}")

# Copy spatial reference / georeferencing unchanged
dst_ds.SetGeoTransform(src_ds.GetGeoTransform())
dst_ds.SetProjection(src_ds.GetProjection())

dst_band = dst_ds.GetRasterBand(1)
if nodata is not None:
    dst_band.SetNoDataValue(nodata)

# Process line-by-line to avoid loading the full raster into memory
for y in range(ysize):
    arr = src_band.ReadAsArray(0, y, xsize, 1).astype(np.float32)

    if nodata is None:
        alt = arr - VESTA_RADIUS_M
    else:
        alt = np.where(arr == nodata, nodata, arr - VESTA_RADIUS_M).astype(np.float32)

    dst_band.WriteArray(alt, 0, y)

dst_band.FlushCache()

# Optional: compute fresh statistics for the new altitude raster
dst_band.ComputeStatistics(False)

# Optional: explicitly preserve the SRS in normalized form using osr
srs = osr.SpatialReference()
srs.ImportFromWkt(src_ds.GetProjection())
dst_ds.SetProjection(srs.ExportToWkt())

dst_ds = None
src_ds = None

print(f"Wrote altitude DEM: {output_path}")
