cwlVersion: v1.2
class: CommandLineTool

requirements:
    InitialWorkDirRequirement:
        listing:
            - $(inputs.output_folder)

baseCommand: ["python"]

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    output_folder:
        type: Directory
        inputBinding:
            prefix: "--output"
    scenario:
        type: string
        inputBinding:
            prefix: "--scenario"
    wflow_warmup:
        type: Directory
        inputBinding:
            prefix: "--wflowwarmup"
    wflow_event:
        type: Directory
        inputBinding:
            prefix: "--wflowevent"
    sfincs_dir:
        type: Directory
        inputBinding:
            prefix: "--sfincsdir"
    fiat_dir:
        type: Directory
        inputBinding:
            prefix: "--fiatdir"
    ra2ce_dir:
        type: Directory
        inputBinding:
            prefix: "--ra2cedir"
    floodmap:
        type: File
        inputBinding:
            prefix: "--floodmap"
    waterlevels:
        type: File
        inputBinding:
            prefix: "--waterlevels"

outputs:
    fa_out_dir:
        type: Directory
        outputBinding:
            glob: "$(inputs.output_folder.basename)"

    