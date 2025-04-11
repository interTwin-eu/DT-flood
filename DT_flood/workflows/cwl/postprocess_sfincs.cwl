cwlVersion: v1.2
class: CommandLineTool

requirements:
    InitialWorkDirRequirement:
        listing:
            - $(inputs.input_folder)
            - $(inputs.static_folder)

baseCommand: ["python"]

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    input_folder:
        type: Directory
        inputBinding:
            prefix: "--input"
    static_folder:
        type: Directory
        inputBinding:
            prefix: "--static"
    scenario:
        type: string
        inputBinding:
            prefix: "--scenario"
    sfincs_dir:
        type: Directory
        inputBinding:
            prefix: "--sfincsdir"

outputs:
    floodmap:
        type: File
        outputBinding:
            glob: "FloodMap_$(inputs.scenario).tif"
    waterlevel_map:
        type: File
        outputBinding:
            glob: "max_water_level_map.nc"