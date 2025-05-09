"""RA2CE utility function for inside container."""

import configparser
from typing import Dict

from ra2ce.analysis.analysis_config_data.analysis_config_data import (  # type: ignore
    AnalysisConfigData,  # type: ignore
)
from ra2ce.network.network_config_data.network_config_data import (  # type: ignore
    NetworkConfigData,  # type: ignore
)


def tree(directory):
    """Display directory tree."""
    print(f"+ {directory}")
    for path in sorted(directory.rglob("*")):
        depth = len(path.relative_to(directory).parts)
        spacer = "  " * depth
        print(f"{spacer}+ {path.name}")


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
