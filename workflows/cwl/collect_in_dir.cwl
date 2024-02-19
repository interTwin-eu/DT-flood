cwlVersion: v1.2
class: ExpressionTool

requirements:
    InlineJavascriptRequirement: {}

inputs:
    files:
        type:
            type: array
            items:
                - Directory
                - File
    dir_name:
        type: string

outputs:
    dir:
        type: Directory



expression: |
    ${return {"dir": {"class": "Directory", "listing": inputs.files, "basename": inputs.dir_name}};}