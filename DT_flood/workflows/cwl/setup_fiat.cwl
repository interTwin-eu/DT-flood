cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    region_file:
        type: File
        inputBinding:
            prefix: "--regionfile"
    sfincs_root:
        type: Directory
        inputBinding:
            prefix: "--sfincsroot"
    agg_areas:
        type: string?
        inputBinding:
            prefix: "--aggareas"
outputs:
    fiat_dir:
        type: Directory
        outputBinding:
            glob: "fiat"
