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

from osgeo import gdal
from os import path
import numpy as np
import progressbar as pb


def progress_callback(complete, message, data):
    percent = int(complete * 100)  # round to integer percent
    data.update(percent)  # update the progressbar
    return 1


# def GeodeticToGeocentric(meters_geodetic_arr: np.typing.NDArray, lat_array: np.typing.NDArray):
# 


thisDir = os.path.dirname(os.path.abspath(__file__))
inputDir = os.path.join(thisDir, "input")
outputDir = os.path.join(thisDir, "output")
productsDir = os.path.join(thisDir, "products")
projDir = os.path.join(thisDir, "proj")


# Input and output file paths
input_tifs = [path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_A1_grey_geo.tif"), \
              path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_B1_grey_geo.tif"),  \
              path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_C1_grey_geo.tif"),  \
              path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_D1_grey_geo.tif"),  \
              path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_A2_grey_geo.tif"),  \
              path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_B2_grey_geo.tif"),  \
              path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_C2_grey_geo.tif"),  \
              path.join("Earth", "Global", "Topography", "gebco_08_rev_elev_D2_grey_geo.tif")]

# Define the spherical target SRS (Example: Spherical Mercator or LongLat)
# +R defines the radius in meters (e.g., 6378137m)
sphere_srs = "+proj=longlat +R=6378137 +no_defs"
# sphere_srs = "+proj=longlat +R=6378137"

# TODO: validate these numbers?
min_elev: float = 0.0
max_elev: float = 6400.0
sea_level_offset: float = max_elev / 255.0

pbar = pb.ProgressBar()

# Run gdal.Warp to convert
for i in range(len(input_tifs)):
    input_tif = path.join(inputDir, input_tifs[i])

    if not path.exists(path.join(productsDir, "Earth", "Global", "Topography")):
        os.makedirs(path.join(productsDir, "Earth", "Global", "Topography"))
    
    outpath_elev = path.join(productsDir, input_tifs[i])
    outpath_elev_split = path.splitext(outpath_elev)
    outpath_elev = outpath_elev_split[0] + "_Elevation.tif"

    outpath_sphere = path.join(productsDir, input_tifs[i])
    outpath_sphere_split = path.splitext(outpath_sphere)
    outpath_sphere = outpath_sphere_split[0] + "_SphericalDatum.tif"

    # Input dataset as uint8 (0 - 255, 0 = no data)
    ds: gdal.Dataset = gdal.Open(input_tif)
    band: gdal.Band = ds.GetRasterBand(1)
    arr: np.typing.NDArray = band.ReadAsArray().astype(np.float32)

    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()

    # Create meshgrid of pixel coordinates
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))

    # Transform pixel coordinates to map coordinates
    # gt[0] = top-left x, gt[1] = pixel width, gt[2] = row rotation
    # gt[3] = top-left y, gt[4] = column rotation, gt[5] = pixel height
    lon_array = gt[0] + cols * gt[1] + rows * gt[2]
    lat_array = gt[3] + cols * gt[4] + rows * gt[5]

    # Scale 0-255 to min_elev-max_elev
    meters_geodetic_arr: np.typing.NDArray = min_elev + (arr / 255.0) * (max_elev - min_elev)
    # meters_geocentric_arr: np.typing.NDArray = GeodeticToGeocentric(meters_geodetic_arr, lat_array)

    # Save as new GeoTIFF (float32)
    driver: gdal.Driver = gdal.GetDriverByName('GTiff')
    out_ds: gdal.Dataset = driver.Create(outpath_elev, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Float32)
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(meters_geodetic_arr)
    out_ds.Close()

    print(f"Processing dataset ")

    pbar.start()
    gdal.Warp(outpath_sphere, outpath_elev, 
              options=gdal.WarpOptions(dstSRS=sphere_srs,
                                       format="GTiff",
                                       creationOptions = ['COMPRESS=LZW'],
                                       multithread=True,
                                       callback=progress_callback, 
                                       callback_data=pbar))
    # dstSRS_options=['FORMAT=WKT2_2018'])
    pbar.finish()

print("Conversion complete.")