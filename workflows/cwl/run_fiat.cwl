cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

requirements:
    InlineJavascriptRequirement: {}
    EnvVarRequirement:
        envDef:
            GDAL_DATA: /home/wotromp/mambaforge/envs/DT-flood/share/gdal
            PROJ_LIB: /home/wotromp/mambaforge/envs/DT-flood/share/proj
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

outputs:
    fa_database:
        type: Directory
        outputBinding:
            glob: "$(inputs.fa_database.basename)"