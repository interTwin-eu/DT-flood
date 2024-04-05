cwlVersion: v1.2
class: CommandLineTool

requirements:
    InlineJavascriptRequirement: {}
    InitialWorkDirRequirement:
        listing:    
            - entry: $(inputs.fa_database)
              writable: true

hints:
    DockerRequirement:
        dockerPull: deltares/wflow:v0.7.3

baseCommand: ["/app/build/create_binaries/wflow_bundle/bin/wflow_cli"]
arguments: ["$(inputs.fa_database.path)/output/Scenarios/$(inputs.scenario)/Flooding/simulations/wflow_$(inputs.mode)/wflow_sbm.toml"]

inputs:
    fa_database:
        type: Directory
    scenario:
        type: string
    mode:
        type: string



outputs:
    fa_database:
        type: Directory
        outputBinding:
            glob: "$(inputs.fa_database.basename)"