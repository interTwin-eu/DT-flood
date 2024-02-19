cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

requirements:
    InlineJavascriptRequirement: {}
    InitialWorkDirRequirement:
        listing:    
            - $(inputs.pyscript)
            - entry: $(inputs.fa_database)
              writable: true

# hints:
#     DockerRequirement:
#         dockerPull: deltares/wflow

# arguments: ["$(inputs.fa_database.path)/output/Scenarios/$(inputs.scenario)/Flooding/simulations/wflow_$(inputs.mode)/wflow_sbm.toml"]

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
    mode:
        type: string
        inputBinding:
            position: 4



outputs:
    fa_database:
        type: Directory
        outputBinding:
            glob: "$(inputs.fa_database.basename)"