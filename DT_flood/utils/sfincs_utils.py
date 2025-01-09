import pandas as pd

from cht.misc.deltares_ini import IniStruct
from cht.sfincs.sfincs import FlowBoundaryPoint
from cht.tide.tide_predict import predict

from earthkit.data import from_source
from earthkit.regrid import interpolate


def read_flow_boundary_points(bnd_fn):
    flow_boundary_point = []

    # if not os.path.exists(bnd_fn):
    #     return
        
    # Read the bnd file
    df = pd.read_csv(bnd_fn, index_col=False, header=None,
        delim_whitespace=True, names=['x', 'y'])
        
    # Loop through points
    for ind in range(len(df.x.values)):
        name = str(ind + 1).zfill(4)
        point = FlowBoundaryPoint(df.x.values[ind],
                                    df.y.values[ind],
                                    name=name)
        flow_boundary_point.append(point)
    return flow_boundary_point


def read_astro_boundary_conditions(flow_boundary_point,bca_fn):

    # Read SFINCS bca file
    # if not os.path.exists(bca_fn):
    #     return

    d = IniStruct(filename=bca_fn)
    for ind, point in enumerate(flow_boundary_point):
        point.astro = d.section[ind].data
    return flow_boundary_point

def generate_bzs_from_bca(flow_boundary_point,
                        tref,
                        tstart,
                        tstop,
                        bzs_fn=None,
                        dt:int=600,
                        offset=0.0,
                        write_file=True):

        if bzs_fn is None:
            bzs_fn = "sfincs.bzs"

        try:
            times = pd.date_range(start=tstart,
                                end=tstop,
                                freq=f"{dt}S")
        except:
            print("Dates fall outside pandas date_range, year 2000 used instead")
            tref = tref.replace(year=2000)
            tstart = tstart.replace(year=2000)
            tstop = tstop.replace(year=2000)
            times = pd.date_range(start=tstart,
                                end=tstop,
                                freq=f"{dt}S")

        # Make boundary conditions based on bca file
        df = pd.DataFrame()

        for i, point in enumerate(flow_boundary_point):
            v = predict(point.astro, times) + offset
            ts = pd.Series(v, index=times)
            point.data = pd.Series(v, index=times)
            df = pd.concat([df, point.data], axis=1)   
        tmsec = pd.to_timedelta(df.index.values - tref, unit="s")
        df.index = tmsec.total_seconds()

        if write_file:            
            # Build a new DataFrame
            df.to_csv(bzs_fn,
                    index=True,
                    sep=" ",
                    header=False,
                    float_format="%0.3f")
        return df
            
def process_dt_climate(filepath, tstart, tend, bounds, res=.1):
    # bounds are list/array in order [minx, miny, maxx, maxy]

    start = int(tstart.strftime("%Y%m%d"))
    end = int(tend.strftime("%Y%m%d"))

    print("Loading data")
    data = from_source("file", filepath).sel(dataDate=slice(start,end))
    print(f"Interpolating data to grid with resolution {res} deg")
    data = interpolate(data, out_grid={"grid": [res,res]}, method='linear')
    ds = data.to_xarray(xarray_open_dataset_kwargs={'chunks': {"time": 1}}).squeeze()

    ds = ds.assign_coords(
        {"longitude": ((ds.longitude+180)%360)-180}
    )
    ds.sortby("longitude")
    ds.sortby("latitude")
    ds = ds.rename(
        {
            "longitude": "x",
            "latitude": "y",
            "sp": "press_msl",
            "u10": "wind10_u",
            "v10": "wind10_v"
        }
    )
    ds.raster.set_crs(4326)

    ds = ds.sel(
        x=slice(bounds[0], bounds[2]),
        y=slice(bounds[1], bounds[3])
    )

    return ds