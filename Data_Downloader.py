# -*- coding: utf-8 -*-

# SpaceCRAFT Platform Dev Configuration Tool

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
sc.easy_AutoVenv(__file__, EXPECTED_REL_PATH_TO_ANCHOR)

#######################################
### IMPORTS ###########################

import os
from os import path
# from sys import platform
# import sys
# import signal
# import psutil
# import json
# import glob
# import zipfile
# import time
# import functools
import urllib.request
import certifi
import ssl
import threading
import math
from pathlib import Path

# from shutil import copyfile
from colorama import Fore, Back, Style
# import progressbar as pb
from alive_progress import alive_bar

#######################################
### GLOBALS ###########################

thisDir = os.path.dirname(os.path.abspath(__file__))
inputDir = os.path.join(thisDir, "input")
outputDir = os.path.join(thisDir, "output")
productsDir = os.path.join(thisDir, "products")
projDir = os.path.join(thisDir, "proj")

termUseColor = True

#######################################
### Actions ###########################

def playGreeting():
    global termUseColor

    if(termUseColor):
        print(sc.greetingString)
    else:
        print(sc.greetingStringNoColor)

    print("\nPlanetDataTools - Data_Downloader")
    print("---------------------")

#https://stackoverflow.com/a/17511341/11502722
def ceildiv(a, b):
    return -(-a // b)

#https://github.com/rsalmei/alive-progress/issues/3
# (with my own modifications)
class AzureProgressCallback(object):
    def __init__(self, local_dir, filename):
        self._filename = path.join(local_dir, filename)
        self._lock = threading.Lock()
        # for progressbar (pb)
        self._pb = None
        self._pbupdate = None

    # def __call__(self, current, total):
    def __call__(self, count, blockSize, totalSize):
        """update the progress bar"""
        with self._lock:
            if self._pb is None:
                # This is a hacky way to make sure the progressbar doesn't get freaked out by overflow
                # Divide by 1e6 to get something that resembles tens of kilobytes
                ceil_totalSize = ceildiv(totalSize, blockSize) * math.ceil(blockSize/1e6)
                self._pb = alive_bar(ceil_totalSize, title=self._filename)
                self._pbupdate = self._pb.__enter__()  # start display thread
                # progress bar is now running (until we call __exit__ on it)
            else:
                # self._pbupdate(incr=math.ceil(blockSize/1e6))
                self._pbupdate(math.ceil(blockSize/1e6))

    def __del__(self):
        with self._lock:
            # dispose of the progressbar
            self._pb.__exit__(None, None, None)

# COPY PASTED FROM C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.9_3.9.2032.0_x64__qbz5n2kfra8p0\Lib\urllib\request.py
import contextlib
import tempfile
from urllib.parse import _splittype

class URLError(OSError):
    # URLError is a sub-type of OSError, but it doesn't share any of
    # the implementation.  need to override __init__ and __str__.
    # It sets self.args for compatibility with other OSError
    # subclasses, but args doesn't have the typical format with errno in
    # slot 0 and strerror in slot 1.  This may be better than nothing.
    def __init__(self, reason, filename=None):
        self.args = reason,
        self.reason = reason
        if filename is not None:
            self.filename = filename

    def __str__(self):
        return '<urlopen error %s>' % self.reason

class ContentTooShortError(URLError):
    """Exception raised when downloaded size does not match content-length."""
    def __init__(self, message, content):
        URLError.__init__(self, message)
        self.content = content


_url_tempfiles = []
def sc_urlretrieve(url, filename=None, reporthook=None, data=None):
    """
    Retrieve a URL into a temporary location on disk.

    Requires a URL argument. If a filename is passed, it is used as
    the temporary file location. The reporthook argument should be
    a callable that accepts a block number, a read size, and the
    total file size of the URL target. The data argument should be
    valid URL encoded data.

    If a filename is passed and the URL points to a local resource,
    the result is a copy from local file to new file.

    Returns a tuple containing the path to the newly created
    data file as well as the resulting HTTPMessage object.
    """
    url_type, path = _splittype(url)

    #https://stackoverflow.com/a/65860355  ?
    #https://stackoverflow.com/a/52117844
    #https://stackoverflow.com/a/44316583
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    with contextlib.closing(urllib.request.urlopen(url, data, context=ssl_context)) as fp:
                                            # My change here! ^^^^^^^^^^^^^^^^^^^^^^ 
        headers = fp.info()

        # Just return the local path and the "headers" for file://
        # URLs. No sense in performing a copy unless requested.
        if url_type == "file" and not filename:
            return os.path.normpath(path), headers

        # Handle temporary file setup.
        if filename:
            tfp = open(filename, 'wb')
        else:
            tfp = tempfile.NamedTemporaryFile(delete=False)
            filename = tfp.name
            _url_tempfiles.append(filename)

        with tfp:
            result = filename, headers
            bs = 1024*8
            size = -1
            read = 0
            blocknum = 0
            if "content-length" in headers:
                size = int(headers["Content-Length"])

            if reporthook:
                reporthook(blocknum, bs, size)

            while True:
                block = fp.read(bs)
                if not block:
                    break
                read += len(block)
                tfp.write(block)
                blocknum += 1
                if reporthook:
                    reporthook(blocknum, bs, size)

    if size >= 0 and read < size:
        raise ContentTooShortError(
            "retrieval incomplete: got only %i out of %i bytes"
            % (read, size), result)

    return result
# END COPY PASTED SEGMENT

def DownloadIfNotExists(local_dir: str, url: str):
    #https://stackoverflow.com/questions/22676/how-to-download-a-file-over-http
    
    file_name = url.split('/')[-1]
    local_path = path.join(inputDir, local_dir, file_name)
    if not path.exists(local_path):
        #ensure the path to the local path exists
        Path(path.join(inputDir, local_dir)).mkdir(parents=True, exist_ok=True)
        local_filename, headers = sc_urlretrieve(url, local_path, AzureProgressCallback(local_dir, file_name))
    else:
        print(file_name, "-- already exists; skipping.")

#######################################
### MAIN ##############################

if __name__ == "__main__":
    playGreeting()

    print("These numbers are roughly in tens of Kilobytes.")

    DownloadIfNotExists(path.join("Moon","Global"),"http://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif")
    DownloadIfNotExists(path.join("Moon","Global"),"https://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LROC-WAC_Mosaic_global_100m_June2013.tif")
    DownloadIfNotExists(path.join("Moon","Local","Apollo17"),"https://planetarymaps.usgs.gov/mosaic/Apollo17/APOLLO17_DTM_150CM.TIFF")#TODO BREAKING might need to rename extension
    DownloadIfNotExists(path.join("Moon","Local","Apollo17"),"https://planetarymaps.usgs.gov/mosaic/Apollo17/APOLLO17_ORTHOMOSAIC_50CM.TIFF")#TODO BREAKING might need to rename extension
    DownloadIfNotExists(path.join("Moon","Local","Apollo15"),"https://astropedia.astrogeology.usgs.gov/download/Moon/LMMP/Apollo15/LRO_NAC_DEM_Apollo_15_26N004E_150cmp.tif")
    DownloadIfNotExists(path.join("Moon","Local","Apollo15"),"https://astropedia.astrogeology.usgs.gov/downloadBig/Moon/LMMP/Apollo15/derived/Moon_LRO_NAC_Mosaic_26N004E_50cmp.tif")
    DownloadIfNotExists(path.join("Moon","Local","SouthPole"),"https://astropedia.astrogeology.usgs.gov/download/Moon/LRO/LOLA/ancillary/LRO_LOLA_DEM_SPolar875_10m.tif")
    DownloadIfNotExists(path.join("Moon","Local","SouthPole"),"https://astropedia.astrogeology.usgs.gov/downloadBig/Moon/LRO/LOLA/ancillary/LRO_LOLA_DEM_SPole75_30m.tif")
    DownloadIfNotExists(path.join("Moon","Local","SouthPole"),"https://astropedia.astrogeology.usgs.gov/download/Moon/LRO/MOON_LRO_NAC_DEM_89S210E_4mp.tif")
    #TODO add links for these (Kevin Cannon website):
    # # Moon South Pole Overlay Data
    # Gnomonic_Warp(path.join("Moon","Local","SouthPole","SP_IceFavorabilityIndex.tif"), \
    #     1737400.0, "moon_gnom", "SPole", pbar, 591)
    # Gnomonic_Warp(path.join("Moon","Local","SouthPole","SP_TerrainType.tif"), \
    #     1737400.0, "moon_gnom", "SPole", pbar, 591)

    # Mars
    DownloadIfNotExists(path.join("Mars","Global"),"https://planetarymaps.usgs.gov/mosaic/Mars_Viking_ClrMosaic_global_925m.tif")
    DownloadIfNotExists(path.join("Mars","Global"),"https://planetarymaps.usgs.gov/mosaic/Mars/HRSC_MOLA_Blend/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif")
    # This one is "artisticly" colored, which doesn't look good in 3D and is not accurate.
    # Disabled for now.
    #DownloadIfNotExists(path.join("Mars","Global"),"https://planetarymaps.usgs.gov/mosaic/Mars_Viking_MDIM21_ClrMosaic_global_232m.tif")
    DownloadIfNotExists(path.join("Mars","Local","Jezero"),"https://planetarymaps.usgs.gov/mosaic/mars2020_landing_site_dtm/J03_045994_1986_J03_046060_1986_20m_DTM.tif")
    DownloadIfNotExists(path.join("Mars","Local","Jezero"),"https://planetarymaps.usgs.gov/mosaic/mars2020_landing_site_dtm/J03_045994_1986_XN_18N282W_6m_ORTHO.tif")
    DownloadIfNotExists(path.join("Mars","Local","Jezero"),"https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first.tif")
    DownloadIfNotExists(path.join("Mars","Local","Jezero"),"https://www.uahirise.org/PDS/DTM/ESP/ORB_045900_045999/ESP_045994_1985_ESP_046060_1985/DTEEC_045994_1985_046060_1985_U01.IMG")
    DownloadIfNotExists(path.join("Mars","Local","Gale"),"http://planetarymaps.usgs.gov/mosaic/Mars/MSL/MSL_Gale_DEM_Mosaic_1m_v3.tif") #3.6GB
    # DownloadIfNotExists(path.join("Mars","Local","Gale"),"http://planetarymaps.usgs.gov/mosaic/Mars/MSL/MSL_Gale_Orthophoto_Mosaic_25cm_v3.tif") #23GB!!!
    #https://astrogeology.usgs.gov/search/map/Mars/MarsReconnaissanceOrbiter/CTX/dundas_flood_lavas_topo/DEM_18m_N_Kasei_Valles_distal_flow
    DownloadIfNotExists(path.join("Mars","Local","LavaFlows"),"https://planetarymaps.usgs.gov/mosaic/dundas_flood_lavas_topo/DEM_18m_N_Kasei_Valles_distal_flow.tif")
    DownloadIfNotExists(path.join("Mars","Local","LavaFlows"),"https://planetarymaps.usgs.gov/mosaic/dundas_flood_lavas_topo/DEM_18m_Lethe_Vallis.tif")
    DownloadIfNotExists(path.join("Mars","Local","LavaFlows"),"https://planetarymaps.usgs.gov/mosaic/dundas_flood_lavas_topo/DEM_18m_NW_Kasei_Constriction.tif")
    DownloadIfNotExists(path.join("Mars","Local","LavaFlows"),"https://planetarymaps.usgs.gov/mosaic/dundas_flood_lavas_topo/DEM_18m_Cerberus_Palus_wrinkle_ridge.tif")
    DownloadIfNotExists(path.join("Mars","Local","LavaFlows"),"https://planetarymaps.usgs.gov/mosaic/dundas_flood_lavas_topo/DEM_18m_North_Kasei_Valles_cataract.tif")
    #https://astrogeology.usgs.gov/search/map/Mars/Mars2020/landing_site/F21_043907_1652_F21_043841_1654_20m_DTM
    DownloadIfNotExists(path.join("Mars","Local","Misc"),"https://planetarymaps.usgs.gov/mosaic/mars2020_landing_site_dtm/F21_043907_1652_F21_043841_1654_20m_DTM.tif")
    DownloadIfNotExists(path.join("Mars","Local","Misc"),"https://planetarymaps.usgs.gov/mosaic/mars2020_landing_site_dtm/D21_035237_2021_F01_036358_2020_20m_DTM.tif")
    DownloadIfNotExists(path.join("Mars","Local","Misc"),"https://planetarymaps.usgs.gov/mosaic/mars2020_landing_site_dtm/B18_016575_1978_B17_016219_1978_20m_DTM.tif")
    DownloadIfNotExists(path.join("Mars","Local","Misc"),"https://planetarymaps.usgs.gov/mosaic/mars2020_landing_site_dtm/P14_006633_2018_P17_007556_2012_20m_DTM_destripe.tif")
    # https://astrogeology.usgs.gov/search/map/Mars/InSight/landing_site/F02_036695_1843_D02_028045_1831_20m_DTM_destripe
    DownloadIfNotExists(path.join("Mars","Local","InSight"),"https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/F02_036761_1828_F04_037262_1841_20m_DTM_destripe.tif")
    DownloadIfNotExists(path.join("Mars","Local","InSight"),"https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/F02_036695_1843_D02_028045_1831_20m_DTM_destripe.tif")
    DownloadIfNotExists(path.join("Mars","Local","InSight"),"https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/D18_034427_1842_D17_033939_1843_20m_DTM.tif")
    DownloadIfNotExists(path.join("Mars","Local","InSight"),"https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/D18_034150_1838_D17_033728_1838_20m_DTM_destripe.tif")
    DownloadIfNotExists(path.join("Mars","Local","InSight"),"https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/D18_034071_1842_D18_034216_1845_20m_DTM.tif")
    DownloadIfNotExists(path.join("Mars","Local","InSight"),"https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/D06_029601_1846_F05_037684_1857_20m_DTM_destripe.tif")
    DownloadIfNotExists(path.join("Mars","Local","InSight"),"https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/D19_034783_1864_D20_034928_1864_20m_DTM_destripe.tif")

    # Mars Moons
    DownloadIfNotExists(path.join("Mars","Phobos","Global"),"https://planetarymaps.usgs.gov/mosaic/Phobos_Viking_Mosaic_40ppd_DLRcontrol.tif")
    DownloadIfNotExists(path.join("Mars","Phobos","Global"),"https://planetarymaps.usgs.gov/mosaic/Phobos_ME_HRSC_DEM_Global_2ppd.tif")
    
    # Mercury
    DownloadIfNotExists(path.join("Mercury","Global"),"http://planetarymaps.usgs.gov/mosaic/Mercury_Messenger_USGS_DEM_Global_665m_v2.tif")
    #Low-incidence imagery (less shadows) https://astrogeology.usgs.gov/search/map/Mercury/Messenger/Global/Mercury_MESSENGER_MDIS_Basemap_LOI_Mosaic_Global_166m
    DownloadIfNotExists(path.join("Mercury","Global"),"https://planetarymaps.usgs.gov/mosaic/Mercury_MESSENGER_MDIS_Basemap_LOI_Mosaic_Global_166m.tif") # double // after mosaic
    #https://astrogeology.usgs.gov/search/map/Mercury/Messenger/MDIS/Mercury_Volatile_Loss/Mercury_Volatile_Loss
    DownloadIfNotExists(path.join("Mercury","Local", "Volatile_Loss"),"https://astropedia.astrogeology.usgs.gov/download/Mercury/Messenger/MDIS/Mercury_Volatile_Loss/Mercury_Volatile_Loss.zip")
    #https://astrogeology.usgs.gov/search/map/Mercury/Topography/Fassett_MDIS_Stereo/Fassett_MESSENGER_MDIS_DEMs

    # Venus
    DownloadIfNotExists(path.join("Venus","Global","Topography"),"https://planetarymaps.usgs.gov/mosaic/Venus_Magellan_Topography_Global_4641m_v02.tif")
    # DownloadIfNotExists(path.join("Venus","Global"),"https://planetarymaps.usgs.gov/mosaic/Venus_Magellan_C3-MDIR_Colorized_Global_Mosaic_4641m.tif") # Artist Colorized
    DownloadIfNotExists(path.join("Venus","Global"),"https://planetarymaps.usgs.gov/mosaic/Venus_Magellan_C3-MDIR_Global_Mosaic_2025m.tif")

    # Ceres
    # https://astrogeology.usgs.gov/search/map/Ceres/Dawn/DLR/FramingCamera/Ceres_Dawn_FC_HAMO_DTM_DLR_Global_60ppd_Oct2016
    DownloadIfNotExists(path.join("Ceres","Global"),"https://planetarymaps.usgs.gov/mosaic/Ceres_Dawn_FC_HAMO_DTM_DLR_Global_60ppd_Oct2016.tif")

    # Vesta
    DownloadIfNotExists(path.join("Vesta","Global"),"https://planetarymaps.usgs.gov/mosaic/Vesta_Dawn_HAMO_DTM_DLR_Global_48ppd.tif")

    # Jupiter Moons
    # Io
    DownloadIfNotExists(path.join("Jupiter","Io","Global"),"https://planetarymaps.usgs.gov/mosaic/Io_GalileoSSI-Voyager_Global_Mosaic_ClrMerge_1km.tif")
    DownloadIfNotExists(path.join("Jupiter","Io","Local"),"https://planetarymaps.usgs.gov/mosaic/Io/TvashtarPaterae_DEM/TvashtarPaterae_DEM_900m.tif")
    # Europa
    DownloadIfNotExists(path.join("Jupiter","Europa","Global"),"https://planetarymaps.usgs.gov/mosaic/Europa_Voyager_GalileoSSI_global_mosaic_500m.tif")
    # Ganymede
    DownloadIfNotExists(path.join("Jupiter","Ganymede","Global"),"https://planetarymaps.usgs.gov/mosaic/Ganymede_Voyager_GalileoSSI_Global_ClrMosaic_1435m.tif")

    # Saturn Moons
    # Enceladus https://astrogeology.usgs.gov/search?pmi-target=enceladus
    DownloadIfNotExists(path.join("Saturn","Enceladus","Global"),"https://planetarymaps.usgs.gov/mosaic/Enceladus/enceladus_cassini_iss_shapemodel_bland_2019/enceladus_2019pm_radius.tif")
    DownloadIfNotExists(path.join("Saturn","Enceladus","Global"),"https://astrogeology.usgs.gov/search/map/Enceladus/enceladus_cassini_iss_shapemodel_bland_2019/enceladus_2019pm_topography") #TODO radius vs altitude ellipsoid stuff
    DownloadIfNotExists(path.join("Saturn","Enceladus","Global"),"https://astropedia.astrogeology.usgs.gov/download/Enceladus/enceladus_cassini_iss_shapemodel_bland_2019/ancillary/enceladus_2019pm_nps_radius.tif")
    DownloadIfNotExists(path.join("Saturn","Enceladus","Global"),"https://astropedia.astrogeology.usgs.gov/download/Enceladus/enceladus_cassini_iss_shapemodel_bland_2019/ancillary/enceladus_2019pm_sps_radius.tif")
    DownloadIfNotExists(path.join("Saturn","Enceladus","Global"),"https://planetarymaps.usgs.gov/mosaic/Enceladus/Cassini/Enceladus_Cassini_ISS_Global_Mosaic_100m_HPF.tif") #TODO high pass filter vs not?
    # DownloadIfNotExists(path.join("Saturn","Enceladus","Global"),"https://planetarymaps.usgs.gov/mosaic/Enceladus_Cassini_mosaic_global_110m.tif")
    #Titan https://astrogeology.usgs.gov/search?pmi-target=titan
    DownloadIfNotExists(path.join("Saturn","Titan","Global"),"https://astropedia.astrogeology.usgs.gov/download/Titan/Cassini/GTDR/gtdr-data.zip")
    DownloadIfNotExists(path.join("Saturn","Titan","Global"),"https://planetarymaps.usgs.gov/mosaic/Titan_ISS_Globe_65Sto45N_450M_AvgMos.tif") #1.5GB
    DownloadIfNotExists(path.join("Saturn","Titan","Global"),"https://planetarymaps.usgs.gov/mosaic/Titan_ISS_P19658_Mosaic_Global_4km.tif")
    #Dione https://astrogeology.usgs.gov/search?pmi-target=dione
    #Iapetus https://astrogeology.usgs.gov/search?pmi-target=iapetus

    # Neptune Moons
    # Triton
    DownloadIfNotExists(path.join("Neptune","Triton","Global"),"https://planetarymaps.usgs.gov/mosaic/Triton_Voyager2_ClrMosaic_GlobalFill_600m.tif")

    # Pluto
    DownloadIfNotExists(path.join("Pluto","Global"),"https://planetarymaps.usgs.gov/mosaic/Pluto_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif")
    DownloadIfNotExists(path.join("Pluto","Global"),"https://planetarymaps.usgs.gov/mosaic/Pluto_NewHorizons_Global_DEM_300m_Jul2017_16bit.tif") # double // after mosaic
    

    # Earth
    # https://earthobservatory.nasa.gov/features/NightLights
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_A1_geo_gray.tif")
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_B1_geo_gray.tif")
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_C1_geo_gray.tif")
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_D1_geo_gray.tif")
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_A2_geo_gray.tif")
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_B2_geo_gray.tif")
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_C2_geo_gray.tif")
    DownloadIfNotExists(path.join("Earth","Global","BlackMarble"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144897/BlackMarble_2016_D2_geo_gray.tif")
    #https://visibleearth.nasa.gov/images/73934/topography
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_A1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_B1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_C1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_D1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_A2_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_B2_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_C2_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Topography"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73934/gebco_08_rev_elev_D2_grey_geo.tif")
    #https://visibleearth.nasa.gov/images/74167/october-blue-marble-next-generation
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.A1.png")
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.B1.png")
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.C1.png")
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.D1.png")
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.A2.png")
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.B2.png")
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.C2.png")
    DownloadIfNotExists(path.join("Earth","Global","BlueMarbleOctober"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/74000/74167/world.200410.3x21600x21600.D2.png")
    #https://visibleearth.nasa.gov/images/73963/bathymetry
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_A1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_B1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_C1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_D1_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_A2_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_B2_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_C2_grey_geo.tif")
    DownloadIfNotExists(path.join("Earth","Global","Bathymetry"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73963/gebco_08_rev_bath_D2_grey_geo.tif")
    #https://visibleearth.nasa.gov/images/57747/blue-marble-clouds
    DownloadIfNotExists(path.join("Earth","Global","Clouds"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud.W.2001210.21600x21600.png")
    DownloadIfNotExists(path.join("Earth","Global","Clouds"),"https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud.E.2001210.21600x21600.png")
    
    # Grand Canyon
    #https://pubs.usgs.gov/ds/121/grand/grand.html
    DownloadIfNotExists(path.join("Earth","Local","Grand Canyon"),"https://pubs.usgs.gov/ds/121/grand/geophys/gc_dem.zip")
    import zipfile
    with zipfile.ZipFile(path.join(inputDir, "Earth","Local","Grand Canyon", "gc_dem.zip"), 'r') as zip_ref:
        zip_ref.extractall(path.join(inputDir, "Earth","Local","Grand Canyon"))

    # Hawaii
    #https://earthworks.stanford.edu/catalog/stanford-mr768cn1027
    DownloadIfNotExists(path.join("Earth","Local","Hawaii"),"https://stacks.stanford.edu/file/druid:mr768cn1027/data.zip")
    with zipfile.ZipFile(path.join(inputDir, "Earth","Local","Hawaii", "data.zip"), 'r') as zip_ref:
        zip_ref.extractall(path.join(inputDir, "Earth","Local","Hawaii"))
    #TODO fix filepath

    # California
    #https://purl.stanford.edu/nh236hj3673
    DownloadIfNotExists(path.join("Earth","Local","San Francisco Bay Area"),"https://stacks.stanford.edu/file/druid:nh236hj3673/data.zip")
    #TODO fix filepath
    with zipfile.ZipFile(path.join(inputDir, "Earth","Local","San Francisco Bay Area", "data.zip"), 'r') as zip_ref:
        zip_ref.extractall(path.join(inputDir, "Earth","Local","San Francisco Bay Area"))

    #Caucasus Mountains
    #https://sustainable-caucasus.unepgrid.ch/download/26
    #DownloadIfNotExists(path.join("Earth","Local","Caucasus"),"https://sustainable-caucasus.unepgrid.ch/download/26")
    #TODO fix or find another?
    #TODO unzip

    # Himalayas - Everest
    # https://nsidc.org/data/hma_dem8m_mos/versions/1#anchor-1
    # https://n5eil01u.ecs.nsidc.org/HMA/HMA_DEM8m_MOS.001/2002.01.28/
    # This doesn't work; requires authentication. Connor will re-host this.
    #DownloadIfNotExists(path.join("Earth","Local","Himalayas"), "https://n5eil01u.ecs.nsidc.org/HMA/HMA_DEM8m_MOS.001/2002.01.28/HMA_DEM8m_MOS_20170716_tile-677.tif")