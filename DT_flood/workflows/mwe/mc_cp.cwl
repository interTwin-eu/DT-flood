cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["mc", "cp"]

inputs:
    src:
        type: [ Directory, File]
        inputBinding:
            position: 1
    dest:
        type: string
        inputBinding:
            position: 2

outputs: []