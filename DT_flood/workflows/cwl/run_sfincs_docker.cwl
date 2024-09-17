cwlVersion: v1.2
class: CommandLineTool

requirements:
    InitialWorkDirRequirement:
        listing:
            - entry: $(inputs.sfincs_files)
              writable: true

hints:
    DockerRequirement:
        dockerPull: deltares/sfincs-cpu:sfincs-v2.0.5

inputs:
    sfincs_files:
        type:
            type: array
            items:
                - Directory
                - File

# stdout: sfincs.log

outputs:
    sfincs_files_out:
        type:
            type: array
            items:
                - Directory
                - File
        outputBinding:
            glob: "*"
    # sfincs_log:
    #     type: stdout