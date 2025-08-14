from pathlib import Path
import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import OutputDirPath

class Input(Parameters):

    sfincs_map: Path

    gfm_map: Path

class Output(Parameters):

    comparison_plot: Path

    comparison_raster: Path

class Params(Parameters):

    output_dir: OutputDirPath

    plot_name: str = "comparison_plot.png"

    raster_name: str = "flood_match.tif"

class CompareSfincsGFM(Method):

    name: str = "compare_sfincs_gfm"

    def __init__(
            self,
            sfincs_map: Path,
            gfm_map: Path,
            output_dir: Path,
            **kwargs
    ):
        
        self.input: Input = Input(
            sfincs_map=sfincs_map,
            gfm_map=gfm_map
        )

        self.params: Params = Params(
            output_dir=output_dir,
            **kwargs
        )

        comparison_plot = self.params.output_dir/self.params.plot_name
        comparison_raster = self.params.output_dir/self.params.raster_name
        self.output: Output = Output(
            comparison_plot=comparison_plot,
            comparison_raster=comparison_raster
        )

    def _run(self):
        
        sf = rxr.open_rasterio(self.input.sfincs_map)
        gfm = rxr.open_rasterio(self.input.gfm_map)

        gfm.rio.write_crs("epsg:4326", inplace=True)
        gfm_match = gfm.rio.reproject_match(sf).sel(band=1)

        sf_flood = xr.where(sf.sel(band=1)>0.05, 0.5, 0)

        compare = sf_flood+gfm_match
        compare.rio.to_raster(self.output.comparison_raster)

        gfm_match = gfm_match.fillna(0)
        compare = sf_flood+gfm_match

        count_flooded_match = (compare == 1.5).sum().item()
        count_sf_only = (compare == 0.5).sum().item()
        count_gfm_only = (compare == 1.0).sum().item()
        count_no_flood_match = (compare == 0.0).sum().item()

        total_count = count_flooded_match + count_sf_only + count_gfm_only + count_no_flood_match

        fig, ax = plt.subplots(figsize=(3,3))

        r1 = Rectangle((0,0), 1, 1, edgecolor="black", facecolor="limegreen", fill=True, lw=0.5)
        _ = plt.text(0.5, 0.5, f"{np.round(count_no_flood_match/total_count*100, decimals=1)}",
                      size=16, ha="center", va="center")
        r2 = Rectangle((1,0), 1, 1, edgecolor="black", facecolor="coral", fill=True, lw=0.5)
        _ = plt.text(1.5, 0.5, f"{np.round(count_gfm_only/total_count*100, decimals=1)}",
                      size=16, ha="center", va="center")
        r3 = Rectangle((0,1), 1, 1, edgecolor="black", facecolor="coral", fill=True, lw=0.5)
        _ = plt.text(0.5, 1.5, f"{np.round(count_sf_only/total_count*100, decimals=1)}",
                      size=16, ha="center", va="center")
        r4 = Rectangle((1,1), 1, 1, edgecolor="black", facecolor="limegreen", fill=True, lw=0.5)
        _ = plt.text(1.5, 1.5, f"{np.round(count_flooded_match/total_count*100)}",
                      size=16, ha="center", va="center")

        ax.add_patch(r1)
        ax.add_patch(r2)
        ax.add_patch(r3)
        ax.add_patch(r4)

        ax.set_xlabel("Global Flood Monitor")
        ax.set_xticks([0.5, 1.5])
        ax.set_xticklabels(["Not Flooded", "Flooded"])

        ax.set_ylabel(["SFINCS"])
        ax.set_yticks([0.5, 1.5])
        ax.set_yticklabels(["Not Flooded", "Flooded"])
        ax.tick_params(axis="y", rotation=90)

        ax.set_xlim(left=0, right=2)
        ax.set_ylim(bottom=0, top=2)
        ax.axis("equal")
        ax.set_position([.15, .15, .8, .8])

        plt.savefig(self.output.comparison_plot)
        plt.close()