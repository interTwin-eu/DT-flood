#!/bin/bash
mamba env create -f environment.yml -n de372_demo
# mamba activate de372_demo
source $CONDA_PREFIX/bin/activate de372_demo
python3 -m pip install dfm_tools earthkit jupyter solara ipyleaflet mapbox-earcut localtileserver html2image
pip install -e .