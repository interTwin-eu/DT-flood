#!/bin/bash
mamba env create -f environment.yml -n de372_demo
source $HOME/miniforge3/bin/activate de372_demo
python3 -m pip --no-cache-dir install dfm_tools earthkit jupyter solara ipyleaflet mapbox-earcut localtileserver html2image
pip install -e .