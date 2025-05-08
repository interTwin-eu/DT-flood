cwlVersion: v1.2
class: CommandLineTool

requirements:
    InitialWorkDirRequirement:
        listing:
            - $(inputs.fiat_dir)
    EnvVarRequirement:
        envDef:
            GDAL_DATA: /home/wotromp/miniforge3/envs/DT-flood/share/gdal
            PROJ_LIB: /home/wotromp/miniforge3/envs/DT-flood/share/proj

baseCommand: ["sh"]

inputs:
    script:
        type: File
        inputBinding:
            position: -1
    fiat_dir:
        type: Directory

outputs:
    fiat_out_dir:
        type: Directory
        outputBinding:
            glob: "./$(inputs.fiat_dir.basename)/"
