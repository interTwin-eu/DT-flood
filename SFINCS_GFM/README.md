# Digital Twin for Post-flood Analysis

This repo contains the code to integrate the satellite-based [Global Flood Monitor](https://github.com/interTwin-eu/dask-flood-mapper) and the physics-based model [SFINCS](https://github.com/Deltares/SFINCS) into a single analysis workflow. The various pieces will setup and run the SFINCS model for the designated event, run the GFM for the designated time and area, and do the cross-comparison.

The directory `examples/baltic` contains example notebooks how to setup the SFINCS model and how to configure the workflow. The workflow and its individual steps are created using [HydroFlows](https://github.com/Deltares-research/HydroFlows). How to add or adapt steps to the workflow we refer to the [HydroFlows documentation](https://deltares-research.github.io/HydroFlows/). A user can run the workflow locally in sequential order (ideal for small number of workflow steps), or export it to either the [SnakeMake](https://snakemake.readthedocs.io/en/stable/) or [CWL](https://www.commonwl.org/) workflow engines for more advanced execution strategies.

## Installation

The workflow uses a different environment from the one in the DT-flood repo. To install this environment, do the following after cloning the DT-flood repo.
```bash
cd DT-flood/SFINCS_GFM
mamba env create -f environment.yml
```