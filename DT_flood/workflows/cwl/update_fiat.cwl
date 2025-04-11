cwlVersion: v1.2
class: CommandLineTool

requirements:
    InitialWorkDirRequirement:
        listing:
            - $(inputs.input_folder)
            - $(inputs.static_folder)
            - $(inputs.output_folder)

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
    output_folder:
        type: Directory
        inputBinding:
            prefix: "--output"
    scenario:
        type: string
        inputBinding:
            prefix: "--scenario"
    floodmap:
        type: File
        inputBinding:
            prefix: "--floodmap"
    waterlevel_map:
        type: File
        inputBinding:
            prefix: "--waterlevelmap"

outputs:
    fiat_dir:
        type: Directory
        outputBinding:
            glob: "$(inputs.output_folder.basename)/scenarios/$(inputs.scenario)/Impacts/fiat_model"