cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

requirements:
    InlineJavascriptRequirement: {}
    InitialWorkDirRequirement:
        listing:
            - $(inputs.pyscript)
            - $(inputs.fa_database)

inputs:
    pyscript:
        type: File
        inputBinding:
            position: 1
    fa_database:
        type: Directory
        inputBinding:
            position: 2
    scenario:
        type: string
        inputBinding:
            position: 3
    # data_catalog:
    #     type: File
    #     inputBinding:
    #         position: 4
    mode:
        type: string
        inputBinding:
            position: 4

outputs:
    fa_database_out:
        type: Directory
        outputBinding:
            glob: "$(inputs.fa_database.basename)"