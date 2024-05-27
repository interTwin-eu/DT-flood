cwlVersion: v1.2
class: CommandLineTool

# baseCommand: []
arguments: ["$(inputs.wflow_folder.path)/wflow_sbm.toml"]

requirements:
    InlineJavascriptRequirement: {}
    InitialWorkDirRequirement:
        listing:
            - entry: $(inputs.wflow_folder)
              writable: true

hints:
    DockerRequirement:
        dockerPull: deltares/wflow

inputs:
    wflow_folder:
        type: Directory


outputs:
    wflow_folder:
        type: Directory
        outputBinding:
            glob: "$(inputs.wflow_folder.basename)"