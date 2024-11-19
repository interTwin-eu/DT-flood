cwlVersion: v1.2
class: CommandLineTool

requirements:
    InitialWorkDirRequirement:
        listing:
            - entry: $(inputs.sfincs_files)
              writable: true

hints:
    DockerRequirement:
        dockerPull: deltares/sfincs-cpu:sfincs-v2.1.1-Dollerup-Release

inputs:
    sfincs_files:
        type:
            type: array
            items:
                - Directory
                - File


outputs:
    sfincs_files_out:
        type:
            type: array
            items:
                - Directory
                - File
        outputBinding:
            glob: "*"