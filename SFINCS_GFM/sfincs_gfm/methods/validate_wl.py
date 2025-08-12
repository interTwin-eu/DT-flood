from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from hydromt_sfincs import SfincsModel

from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import FileDirPath, ListOfPath, OutputDirPath

class Input(Parameters):

    sfincs_inp: FileDirPath

    wl_data: ListOfPath

class Output(Parameters):

    validation_plot: Path

class Params(Parameters):

    output_dir: OutputDirPath

    plot_name: str = "sfincs_wl_validation.png"

    wl_offset: float = 0.0

class ValidateWL(Method):

    name: str = "validate_sfincs_wl"

    def __init__(
            self,
            sfincs_inp: FileDirPath,
            wl_data: ListOfPath,
            output_dir: Path,
            **kwargs
    ):
        self.params: Params = Params(
            output_dir=output_dir,
            **kwargs
        )
        self.input: Input = Input(
            sfincs_inp=sfincs_inp,
            wl_data=wl_data
        )
        validation_plot = self.params.output_dir/self.params.plot_name
        self.output: Output = Output(
            validation_plot=validation_plot
        )
    
    def _run(self):

        sf_root = self.input.sfincs_inp.parent
        sf = SfincsModel(root=sf_root, mode='r+')
        sf.read()
        sf.read_results()

        wl_list = self.input.wl_data
        wl_offset = self.params.wl_offset
        wl_df = []

        df = pd.DataFrame(index=sf.results["point_zs"].time.values)
        if len(sf.results['point_zs'].stations)>0:
            for ii in np.arange(len(sf.results["point_zs"].stations)):
                df[ii] = sf.results["point_zs"].isel(stations=ii).values

        for ii, fn in enumerate(wl_list):
            wl_df.append(pd.read_csv(fn, header=0, delimiter=";"))
            wl_df[ii]["timestamp"] = pd.to_datetime(wl_df[ii]["timestamp"])
            wl_df[ii] = wl_df[ii].set_index("timestamp")
            if ii>=1:
                wl_df[0] = wl_df[0].join(wl_df[ii],rsuffix=str(ii))
        
        obs_df = (wl_df[0] + wl_offset)/100
        obs_df = obs_df.rename(columns={"value": "Althagen", "value1": "Barhoeft", "value2": "Barth"})
        obs_df = obs_df[obs_df.index.day>16]

        r2 = {}
        lab = []
        for ii,station in enumerate(obs_df.columns):
            x=obs_df[station]
            y=np.interp(obs_df.index,df.index,df[ii])

            coeffs = np.polyfit(x,y,1)
            p = np.poly1d(coeffs)

            y_hat = p(x)
            y_mean = np.mean(y)
            ss_tot = np.sum((y-y_mean)**2)
            ss_res = np.sum((y-y_hat)**2)
            r_squared = 1 - (ss_res/ss_tot)
            r2[station] = np.round(r_squared, decimals=2)
            lab.append(f"{station} R-squared: {r2[station]}")

        fig,ax = plt.subplots()
        df.plot(ax=ax, y=[0,1,2])
        clr=[]
        for n, li in enumerate(ax.get_lines()):
            clr.append(li.get_color())
        obs_df.plot(ax=ax, style="--", cmap=ListedColormap(clr))
        plt.grid()
        plt.legend(lab)
        ax.set_ylabel("Waterlevel [m above NHN]")
        ax.set_xlim(left=obs_df.index[0], right=df.index[-1])

        plt.close()
        plt.savefig(self.output.validation_plot)
