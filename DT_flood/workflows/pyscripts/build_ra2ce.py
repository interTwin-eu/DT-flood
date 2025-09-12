"""Script to build ra2ce model, run inside docker."""

import configparser
from pathlib import Path
from typing import Dict

from ra2ce.analysis.analysis_config_data.analysis_config_data import (  # type: ignore
    AnalysisConfigData,
    AnalysisSectionLosses,
    ProjectSection,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import (  # type: ignore
    WeighingEnum,  # type: ignore
)
from ra2ce.network.exporters.geodataframe_network_exporter import (  # type: ignore
    GeoDataFrameNetworkExporter,
)
from ra2ce.network.exporters.multi_graph_network_exporter import (  # type: ignore
    MultiGraphNetworkExporter,
)
from ra2ce.network.network_config_data.enums.network_type_enum import (  # type: ignore
    NetworkTypeEnum,  # type: ignore
)
from ra2ce.network.network_config_data.enums.road_type_enum import (  # type: ignore
    RoadTypeEnum,  # type: ignore
)
from ra2ce.network.network_config_data.enums.source_enum import (  # type: ignore
    SourceEnum,  # type: ignore
)
from ra2ce.network.network_config_data.network_config_data import (  # type: ignore
    NetworkConfigData,
    NetworkSection,
    OriginsDestinationsSection,
)
from ra2ce.network.network_wrappers.osm_network_wrapper.osm_network_wrapper import (  # type: ignore
    OsmNetworkWrapper,
)

# from utils_ra2ce_docker import (  # type: ignore
#     export_AnalysisConfigData,
#     export_NetworkConfigData,
# )


def analysisConfigData_to_dict(acd: AnalysisConfigData) -> Dict:
    """Export analysis config data to dict.

    Parameters
    ----------
    acd : AnalysisConfigData
        RA2CE analysis config data

    Returns
    -------
    Dict
        analysis config data in dict form.
    """
    _dict = acd.__dict__
    _dict["project"] = acd.project.__dict__
    _dict["analyses"] = [analysis.__dict__ for analysis in acd.analyses]
    _dict["origins_destinations"] = acd.origins_destinations.__dict__
    _dict["network"] = acd.network.__dict__
    _dict["hazard_names"] = acd.hazard_names
    return _dict


def entries_to_str(dict_in: Dict) -> Dict:
    """Turn all dictionary values into strings.

    Lists will be parsed into a single string containing all list entries.
    Empty values will be parsed into "None" string.

    Parameters
    ----------
    dict_in : Dict
        Dictionary whose values will be converted.

    Returns
    -------
    Dict
        Output dictionary. Keys are the same as dict_in keys.
    """
    dict_out = {}
    for key, value in dict_in.items():
        if not isinstance(value, list):
            dict_out[key] = str(value)
        else:
            dict_out[key] = ",".join([str(item) for item in value])
        dict_out[key] = "None" if dict_out[key] == "" else dict_out[key]
    return dict_out


def export_NetworkConfigData(ncd: NetworkConfigData) -> None:
    """Export a NetworkConfigData instance to network.ini file.

    Parameters
    ----------
    ncd : NetworkConfigData
        NetworkConfigData to export.
    """
    config = configparser.ConfigParser()

    for key, value in ncd.to_dict().items():
        if not isinstance(value, dict):
            continue
        config[key] = entries_to_str(value)

    with open(ncd.static_path.parent / "network.ini", "w") as f:
        config.write(f)


def export_AnalysisConfigData(acd: AnalysisConfigData) -> None:
    """Export an AnalysisConfigData instance to analysis.ini file.

    Parameters
    ----------
    acd : AnalysisConfigData
        AnalysisConfigData to export.
    """
    config = configparser.ConfigParser()

    for key, value in analysisConfigData_to_dict(acd).items():
        if key == "analyses":
            for num, analysis in enumerate(value):
                config[f"analysis{num+1}"] = entries_to_str(analysis)
        elif not isinstance(value, dict):
            continue
        else:
            config[key] = entries_to_str(value)

    with open(acd.static_path.parent / "analysis.ini", "w") as f:
        config.write(f)


# root_dir = Path("/home/mambauser/project/ra2ce/")
root_dir = Path("data")

input_path = root_dir / "input"
output_path = root_dir / "output"
static_path = root_dir / "static"
map_path = root_dir / "static" / "network" / "map.geojson"

print(map_path)
print(map_path.exists())

road_list = road_list = [
    RoadTypeEnum.MOTORWAY,
    RoadTypeEnum.MOTORWAY_LINK,
    RoadTypeEnum.TRUNK,
    RoadTypeEnum.TRUNK_LINK,
    RoadTypeEnum.PRIMARY,
    RoadTypeEnum.PRIMARY_LINK,
    RoadTypeEnum.SECONDARY,
    RoadTypeEnum.SECONDARY_LINK,
    # RoadTypeEnum.TERTIARY,
    # RoadTypeEnum.TERTIARY_LINK,
    # RoadTypeEnum.BRIDGE,
    # RoadTypeEnum.RESIDENTIAL,
    # RoadTypeEnum.ROAD,
]

# Define which road to download from OSM

print("Define Network Config")
_network_section = NetworkSection(
    polygon=map_path,
    network_type=NetworkTypeEnum.DRIVE,
    road_types=road_list,
    save_gpkg=True,
    source=SourceEnum.PICKLE,
)

od_section = OriginsDestinationsSection(
    origins="origins.gpkg",
    destinations="destinations.gpkg",
    origins_names="A",
    destinations_names="B",
    id_name_origin_destination="OBJECT ID",
    origin_count="POPULATION",
    category="category",
)

# Pass specified sections as arguments for config
_network_config_data = NetworkConfigData(
    root_path=root_dir,
    output_path=output_path,
    static_path=static_path,
    network=_network_section,
    origins_destinations=od_section,
)

# Download network based on polygon and specified road types
print("Get OSM data")
_graph, _gdf = OsmNetworkWrapper.get_network_from_geojson(_network_config_data)

print("Define Analysis Config")
od_loss_section = AnalysisSectionLosses(
    name="test multi link od analysis without hazard",
    analysis="multi_link_origin_closest_destination",
    weighing=WeighingEnum.LENGTH,
    calculate_route_without_disruption=False,
    save_csv=True,
    save_gpkg=True,
)

od_analysis = AnalysisConfigData(
    root_path=root_dir,
    input_path=input_path,
    output_path=output_path,
    static_path=static_path,
    project=ProjectSection(name="ra2ce"),
    analyses=[od_loss_section],
)


# export graph
print("Export Configs")
_exporter = MultiGraphNetworkExporter(
    basename="base_graph", export_types=["gpkg", "pickle"]
)
_exporter.export(export_path=static_path / "output_graph", export_data=_graph)

_exporter = GeoDataFrameNetworkExporter(
    basename="base_network", export_types=["gpkg", "pickle"]
)
_exporter.export(export_path=static_path / "output_graph", export_data=_gdf)

export_NetworkConfigData(_network_config_data)
export_AnalysisConfigData(od_analysis)
