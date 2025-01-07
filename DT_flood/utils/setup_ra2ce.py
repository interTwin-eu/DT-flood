from pathlib import Path

from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (NetworkConfigData, NetworkSection,OriginsDestinationsSection)
from ra2ce.network.network_wrappers.osm_network_wrapper.osm_network_wrapper import OsmNetworkWrapper
from ra2ce.network.exporters.geodataframe_network_exporter import GeoDataFrameNetworkExporter
from ra2ce.network.exporters.multi_graph_network_exporter import MultiGraphNetworkExporter
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData, AnalysisSectionLosses, ProjectSection
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum

from utils_ra2ce_docker import export_NetworkConfigData, export_AnalysisConfigData, tree


root_dir = Path("/home/mambauser/project/ra2ce/")

input_path = root_dir/"input"
output_path = root_dir/"output"
static_path = root_dir/"static"
map_path = root_dir/"static"/"network"/"map.geojson"

road_list = road_list = [
    RoadTypeEnum.MOTORWAY,
    RoadTypeEnum.MOTORWAY_LINK,
    RoadTypeEnum.TRUNK,
    RoadTypeEnum.TRUNK_LINK,
    RoadTypeEnum.PRIMARY,
    RoadTypeEnum.PRIMARY_LINK,
    RoadTypeEnum.SECONDARY,
    RoadTypeEnum.SECONDARY_LINK,
    RoadTypeEnum.TERTIARY,
    RoadTypeEnum.TERTIARY_LINK,
    RoadTypeEnum.BRIDGE,
    RoadTypeEnum.RESIDENTIAL,
    RoadTypeEnum.ROAD,
]

# Define which road to download from OSM

_network_section = NetworkSection(
    polygon=map_path,
    network_type=NetworkTypeEnum.DRIVE,
    road_types=road_list,
    save_gpkg=True,
    source=SourceEnum.PICKLE
)

od_section = OriginsDestinationsSection(
    origins="origins.gpkg",
    destinations="destinations.gpkg",
    origins_names="A",
    destinations_names="B",
    id_name_origin_destination="OBJECT ID",
    origin_count="POPULATION",
    category="category"
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
_graph, _gdf = OsmNetworkWrapper.get_network_from_geojson(_network_config_data)

od_loss_section = AnalysisSectionLosses(
    name="test multi link od analysis without hazard",
    analysis="multi_link_origin_closest_destination",
    weighing=WeighingEnum.LENGTH,
    calculate_route_without_disruption=False,
    save_csv=True,
    save_gpkg=True
)

od_analysis = AnalysisConfigData(
    root_path=root_dir,
    input_path=input_path,
    output_path=output_path,
    static_path=static_path,
    project=ProjectSection(name="ra2ce"),
    analyses=[od_loss_section]
)


# export graph
_exporter = MultiGraphNetworkExporter(basename='base_graph', export_types=['gpkg', 'pickle'])
_exporter.export(export_path=static_path/"output_graph", export_data=_graph)

_exporter = GeoDataFrameNetworkExporter(basename='base_network', export_types=['gpkg', 'pickle'])
_exporter.export(export_path=static_path/"output_graph", export_data=_gdf)

export_NetworkConfigData(_network_config_data)
export_AnalysisConfigData(od_analysis)

tree(root_dir)

