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
    output_folder:
        type: Directory
    scenario:
        type: string
        inputBinding:
            prefix: "--scenario"
    fiat_dir:
        type: Directory
        inputBinding:
            prefix: "--fiatdir"

outputs:
    fiat_out_dir:
        type: Directory
        outputBinding:
            glob: "$(inputs.output_folder.basename)/scenarios/$(inputs.scenario)"
