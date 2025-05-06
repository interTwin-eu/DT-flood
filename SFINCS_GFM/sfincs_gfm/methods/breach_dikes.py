from pathlib import Path
import geopandas as gpd

from hydromt_sfincs import SfincsModel

from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import OutputDirPath, FileDirPath

from sfincs_gfm.methods.utils import copy_sfincs_model

class Input(Parameters):

    sfincs_inp: FileDirPath

    dike_locs: Path

    breach_locs = Path

class Output(Parameters):

    sfincs_out_inp: FileDirPath

class Params(Parameters):

    overtopping: bool = False

    output_dir: OutputDirPath

    copy_model: bool = False

class BreachDikes(Method):

    name: str = "breach_dikes"

    def __init__(
            self,
            sfincs_inp: FileDirPath,
            dike_locs: Path,
            breach_locs: Path,
            output_dir: Path,
            overtopping: bool = False,
            **params
    ):
        
        self.params: Params = Params(
            overtopping=overtopping,
            output_dir=output_dir,
            **params
        )
        self.input: Input = Input(
            sfincs_inp=sfincs_inp,
            dike_locs=dike_locs,
            breach_locs=breach_locs,
        )

        if self.params.copy_model and not self.params.output_dir:
            raise ValueError("Unknown dest. folder for copy operation.")


        sinfcs_out_inp = self.params.output_dir / "sfincs.inp"
        if not self.params.copy_model and not self.params.output_dir.is_relative_to(
            self.input.sfincs_inp.parent
        ):
            raise ValueError("Output directory must be relative to the input directory when not copying the model.")
        self.output: Output = Output(
            sfincs_out_inp=sinfcs_out_inp
        )
    
    def _run(self):

        root = self.input.sfincs_inp.parent
        out_root = self.output.sfincs_out_inp.parent
        copy_model = self.params.copy_model
        
        if copy_model:
            copy_sfincs_model(src=root, dest=out_root)

        sf = SfincsModel(root=root, mode="r", write_gis=False)

        dikes = sf.data_catalog.get_geodataframe(
            self.input.dike_locs, crs=sf.crs, geom=sf.region
        )
        breaches = gpd.read_file(self.input.breach_locs).to_crs(sf.crs)

        s = gpd.GeoSeries(dikes.geometry)
        breach_idx = s.sindex.nearest(breaches.geometry)

        if self.params.overtopping:
            dikes_breached = dikes.copy()
            dikes_breached["z"].loc[breach_idx[1]] = 0.8
            dikes_breached["par1"] = 0.6
        else:
            dikes_breached = dikes.drop(index=breach_idx[1])
            dikes_breached["par1"] = 0.6

        sf.setup_structures(structures=dikes_breached, stype="weir", merge=False)

        sf.set_root(out_root, mode="w+")
        sf.write()
        



            

