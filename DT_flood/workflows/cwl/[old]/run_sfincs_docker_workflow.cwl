cwlVersion: v1.2
class: Workflow

requirements:
    InlineJavascriptRequirement: {}
    StepInputExpressionRequirement: {}

inputs:
    sfincs_folder: Directory

outputs:
    sfincs_dir:
        type: Directory
        outputSource: collect_files/dir

steps:
    test_step:
        in:
            sfincs_files:
                source: sfincs_folder
                valueFrom: $(self.listing)
        out: [sfincs_files]
        run:
            ./run_sfincs_docker.cwl
    collect_files:
        in:
            files: test_step/sfincs_files
            dir_name:
                source: sfincs_folder
                valueFrom: $(self.basename)
        out:
            [dir]
        run:
            ./collect_in_dir.cwl


