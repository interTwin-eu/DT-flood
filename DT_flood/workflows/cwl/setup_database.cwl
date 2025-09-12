cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    name:
        type: string
        inputBinding:
            prefix: "--name"
    sfincs_root:
        type: Directory
        inputBinding:
            prefix: "--sfincsroot"
    fiat_root:
        type: Directory
        inputBinding:
            prefix: "--fiatroot"
    wflow_root:
        type: Directory
        inputBinding:
            prefix: "--wflowroot"
    ra2ce_root:
        type: Directory
        inputBinding:
            prefix: "--ra2ceroot"


outputs:
    fa_database:
        type: Directory
        outputBinding:
            glob: "$(inputs.name)"
