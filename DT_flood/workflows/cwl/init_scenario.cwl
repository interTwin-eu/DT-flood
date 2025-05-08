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


outputs:
    output_folder:
        type: Directory
        outputBinding:
            glob: "./output/"
