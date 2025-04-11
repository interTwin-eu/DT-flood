cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    endpoint:
        type: string
        inputBinding:
            prefix: "--endpoint"
    user:
        type: string?
        inputBinding:
            prefix: "--user"
    password:
        type: string?
        inputBinding:
            prefix: "--password"
    token:
        type: string?
        inputBinding:
            prefix: "--token"
    refreshtoken:
        type: string?
        inputBinding:
            prefix: "--refreshtoken"
    service:
        type: string
        inputBinding:
            prefix: "--service"
    filename:
        type: Directory
        inputBinding:
            prefix: "--filename"
    service_directory:
        type: Directory
        inputBinding:
            prefix: "--service_directory"
    output:
        type: string
        inputBinding:
            prefix: "--output"

outputs:
    oscar_out:
        type: Directory
        outputBinding:
            glob: "./output/"