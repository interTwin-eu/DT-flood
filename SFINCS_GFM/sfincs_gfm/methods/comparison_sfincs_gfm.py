from pathlib import Path

from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import OutputDirPath, FileDirPath

class Input(Parameters):

    sfincs_inp: FileDirPath

    gfm_map: Path

class Output(Parameters):

    comparison_plot: Path

class Params(Parameters):

    output_dir: OutputDirPath

    plot_name: str = "comparison_plot.png"

class CompareSfincsGFM(Method):

    name: str = "compare_sfincs_gfm"

    def __init__(
            self,
            sfincs_inp: Path,
            gfm_map: Path,
            output_dir: Path,
    ):
        
        self.input: Input = Input(
            sfincs_inp=sfincs_inp,
            gfm_map=gfm_map
        )

        self.params: Params = Params(
            output_dir=output_dir
        )

        comparison_plot = self.params.output_dir/self.params.plot_name
        self.output: Output = Output(
            comparison_plot=comparison_plot
        )

    def _run(self):
        pass

