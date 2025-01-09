cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

requirements:
    InlineJavascriptRequirement: {}
    InitialWorkDirRequirement:
        listing:    
            - entry: $(inputs.pyscript)
            - entry: $(inputs.fa_database)
              writable: true

hints:
    DockerRequirement:
        dockerPull: containers.deltares.nl/ra2ce/ra2ce:latest

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