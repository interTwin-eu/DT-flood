cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

requirements:
    InlineJavascriptRequirement: {}
    InitialWorkDirRequirement:
        listing:    
            - $(inputs.pyscript)
            - $(inputs.fa_database)
    EnvVarRequirement:
        envDef:
            GDAL_DATA: /home/wotromp/miniforge3/envs/DT-flood/share/gdal
            PROJ_LIB: /home/wotromp/miniforge3/envs/DT-flood/share/proj

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
    fa_database_out:
        type: Directory
        outputBinding:
            glob: "$(inputs.fa_database.basename)"