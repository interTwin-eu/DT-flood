from pathlib import Path
from datetime import datetime

from hydromt_sfincs import SfincsModel
from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import OutputDirPath, FileDirPath

from sfincs_gfm.methods.utils import copy_sfincs_model, parse_local_wl_data, fetch_local_wind_data

class Input(Parameters):

    sfincs_inp: FileDirPath

    wl_file: Path

class Output(Parameters):
    
    sfincs_out_inp: FileDirPath

class Params(Parameters):

    wind_url: str

    wl_offset: float = 0.0

    start_time: datetime

    end_time: datetime

    output_dir: OutputDirPath

    copy_model: bool = False

class SetForcing(Method):

    name: str = "set_forcing"

    def __init__(
            self,
            sfincs_inp: FileDirPath,
            wl_file: Path,
            wind_url: Path,
            start_time: datetime,
            end_time: datetime,
            output_dir: Path,
            **params
    ):
        
        self.params: Params = Params(
            wind_url=wind_url,
            start_time=start_time,
            end_time=end_time,
            output_dir=output_dir,
            **params
        )
        self.input: Input = Input(
            sfincs_inp=sfincs_inp,
            wl_file=wl_file,
        )

        if self.params.copy_model and not self.params.output_dir:
            raise ValueError("Unknown dest. folder for copy operation.")
        
        sfincs_out_inp = self.params.output_dir / "sfincs.inp"
        if not self.params.copy_model and not self.params.output_dir.is_relative_to(
            self.input.sfincs_inp.parent
        ):
            raise ValueError("Output directory must be relative to the input directory when not copying the model.")
        self.output: Output = Output(
            sfincs_out_inp=sfincs_out_inp
        )

    def _run(self):

        root = self.input.sfincs_inp.parent
        out_root = self.output.sfincs_out_inp.parent
        copy_model = self.params.copy_model

        fmt = "%Y%m%d %H%M%S"
        
        if copy_model:
            copy_sfincs_model(src=root, dest=out_root)

        bzspd = parse_local_wl_data(self.input.wl_file)
        wnd = fetch_local_wind_data(self.params.wind_url)

        sf = SfincsModel(root=root, mode="r", write_gis=False)

        sf.config.update(
            {
                "tref": self.params.start_time.strftime(fmt),
                "tstart": self.params.start_time.strftime(fmt),
                "tstop": self.params.end_time.strftime(fmt)
            }
        )

        sf.setup_waterlevel_forcing(timeseries=bzspd, merge=False)
        sf.setup_wind_forcing(timeseries=wnd)

        sf.set_root(out_root, mode="w+")
        sf.write_config()
        sf.write_forcing()

