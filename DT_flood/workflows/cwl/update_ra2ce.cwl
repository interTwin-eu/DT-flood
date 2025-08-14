cwlVersion: v1.2
class: CommandLineTool

requirements:
    InitialWorkDirRequirement:
        listing:
            - entry: $(inputs.pyscript)
            - entry: $(inputs.input_folder)
            - entry: $(inputs.static_folder)
            - entry: $(inputs.utils_script_docker)


baseCommand: ["python"]

hints:
    DockerRequirement:
        dockerPull: containers.deltares.nl/gfs/ra2ce:v1_0_0

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    input_folder:
        type: Directory
        inputBinding:
            prefix: "--input"
    static_folder:
        type: Directory
        inputBinding:
            prefix: "--static"
    output_folder:
        type: Directory
    scenario:
        type: string
        inputBinding:
            prefix: "--scenario"
    floodmap:
        type: File
        inputBinding:
            prefix: "--floodmap"
    utils_script_docker:
        type: File

outputs:
    ra2ce_dir:
        type: Directory
        outputBinding:
            glob: "$(inputs.output_folder.basename)/scenarios/$(inputs.scenario)/Impacts/ra2ce"
