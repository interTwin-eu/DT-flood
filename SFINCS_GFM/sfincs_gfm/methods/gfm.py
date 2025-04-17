from pathlib import Path
from datetime import datetime 

import geopandas as gpd
from dask.distributed import Client
from dask_flood_mapper import flood

from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import OutputDirPath

class Input(Parameters):

    region: Path

class Output(Parameters):

    floodcube: Path

class Params(Parameters):

    starttime: datetime
    endtime: datetime
    output_dir: OutputDirPath

class GFM(Method):

    name: str = "gfm"

    def __init__(
            self,
            region: Path,
            starttime: datetime,
            endtime: datetime,
            output_dir: str,
            **params
    ):
        
        self.params: Params = Params(
            starttime=starttime,
            endtime=endtime,
            output_dir=output_dir,
            **params
        )
        self.input: Input = Input(
            region=region
        )

        floodcube = Path(self.params.output_dir) / "floodcube.nc"
        self.output: Output = Output(
            floodcube=floodcube
        )

    def _run(self):
        """
        Run the GFM method.
        """

        client = Client(processes=False, threads_per_worker=2, n_workers=1, memory_limit="5GB")

        start = self.params.starttime.strftime("%Y-%m-%d")
        end = self.params.endtime.strftime("%Y-%m-%d")

        time_range = f"{start}/{end}"
        region = gpd.read_file(self.input.region).to_crs("EPSG:4326")
        bbox = region.total_bounds

        fd = flood.decision(bbox=bbox, datetime=time_range).compute()

        fd.to_netcdf(self.output.floodcube)