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
    pop_data:
        type: string?
        inputBinding:
            prefix: "--popdata"
    dest_points:
        type: string?
        inputBinding:
            prefix: "--destpoints"
outputs:
    ra2ce_dir:
        type: Directory
        outputBinding:
            glob: "ra2ce"
