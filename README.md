# SpaceTeamsPro Planet Data Tools
This repo contains tools for the reprojection of georeferenced celestial body data into 6-sided gnomonic, the projection that Space Teams Pro uses for its celestial body rendering.

The `proj` folder contains the WKT-format projection definitions we're using for 6-sided gnomonic for each of the celestial bodies.

`Data_Downloader.py` downloads the planet data from the source websites, and `Data_Preprocessor.py` does the reprojection.
