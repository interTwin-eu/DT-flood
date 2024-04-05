cwlVersion: v1.2
class: Workflow

requirements:
    StepInputExpressionRequirement: {}
    InlineJavascriptRequirement: {}


inputs:
    fa_database: Directory
    scenario: string
    sfincs_update_script: File
    arrange_script: File

outputs:
    fa_database_out:
        type: Directory
        outputSource: arrange_folder/fa_database_out


steps:
    setup_sfincs:
        in:
            fa_database: fa_database
            scenario: scenario
            pyscript: sfincs_update_script
        out:
            [fa_database_out]
        run:
            ./update_sfincs.cwl
    fetch_sfincs_dir:
        in:
            fa_database: setup_sfincs/fa_database_out
            scenario: scenario
        out:
            [sfincs_dir]
        run:
            class: CommandLineTool
            baseCommand: ["echo","Fetching SFINCS Directory"]
            requirements:
                InlineJavascriptRequirement: {}
                InitialWorkDirRequirement:
                    listing:
                        - $(inputs.fa_database)
            inputs:
                fa_database:
                    type: Directory
                scenario:
                    type: string
            outputs:
                sfincs_dir:
                    type: Directory
                    outputBinding:
                        glob: $(inputs.fa_database.basename+"/output/Scenarios/"+inputs.scenario+"/Flooding/simulations/overland")
    run_sfincs:
        in:
            sfincs_files:
                source: fetch_sfincs_dir/sfincs_dir
                valueFrom: $(self.listing)
        out:
            [sfincs_files_out]
        run:
            ./run_sfincs_docker.cwl
    fetch_sfincs_files:
        in:
            files: run_sfincs/sfincs_files_out
            dir_name:
                default: "overland"
        out:
            [dir]
        run:
            ./collect_in_dir.cwl
    arrange_folder:
        in:
            pyscript: arrange_script
            in_folder: fetch_sfincs_files/dir
            fa_database: fa_database
            scenario: scenario
        out:
            [fa_database_out]
        run:
            class: CommandLineTool
            baseCommand: ["python"]
            requirements:
                InitialWorkDirRequirement:
                    listing:
                        - $(inputs.pyscript)
                        - $(inputs.in_folder)
                        - $(inputs.fa_database)
            inputs:
                pyscript:
                    type: File
                    inputBinding:
                        position: 1
                in_folder:
                    type: Directory
                    inputBinding:
                        position: 2
                fa_database:
                    type: Directory
                    inputBinding:
                        position: 3
                scenario:
                    type: string
                    inputBinding:
                        position: 4
            outputs:
                fa_database_out:
                    type: Directory
                    outputBinding:
                        glob: "$(inputs.fa_database.basename)"