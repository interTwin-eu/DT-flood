#!/bin/bash
mamba env create -f environment.yml
source $HOME/miniforge3/bin/activate DT-flood
python3 -m pip --no-cache-dir install dfm_tools earthkit jupyter solara ipyleaflet mapbox-earcut localtileserver html2image minio oscar-python liboidcagent
pip install -e .