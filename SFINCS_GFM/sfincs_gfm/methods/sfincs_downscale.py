from pathlib import Path
import geopandas as gpd

from hydromt_sfincs import SfincsModel
import hydromt_sfincs.utils as sf_utils

from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import OutputDirPath, FileDirPath

class Input(Parameters):

    sfincs_inp: FileDirPath

    landmask: Path

    dem: Path

class Params(Parameters):

    output_dir: OutputDirPath

    floodmap_name: str = "max_waterlevel.tif"

class Output(Parameters):

    floodmap: Path

class SfincsDownscale(Method):

    name: str = "sfincs_downscale"

    def __init__(
            self, 
            sfincs_inp: FileDirPath,
            landmask: Path,
            dem: Path,
            output_dir: Path,
            **kwargs
    ):
        
        self.params: Params = Params(
            output_dir=output_dir,
            **kwargs
        )
        self.input: Input = Input(
            sfincs_inp=sfincs_inp,
            landmask=landmask,
            dem=dem
        )
        floodmap_fn = self.params.output_dir / self.params.floodmap_name
        self.output: Output = Output(
            floodmap=floodmap_fn
        )

    def _run(self):

        sf_root = self.input.sfincs_inp.parent
        sf = SfincsModel(root=sf_root, mode='r+')
        sf.read()
        sf.read_results()

        landmask = gpd.read_file(self.input.landmask)
        dem = sf.data_catalog.get_rasterdataset(self.input.dem)

        zsmax = sf.results["zsmax"].max(dim="timemax")
        zsmax.attrs["units"] = "m"

        sf_utils.downscale_floodmap(
            zsmax=zsmax,
            dep=dem,
            hmin=0.01,
            floodmap_fn=self.output.floodmap,
            gdf_mask=landmask
        )




