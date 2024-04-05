            class: CommandLineTool
            baseCommand: ["echo"]
            requirements:
                InlineJavascriptRequirement: {}
                InitialWorkDirRequirement:
                    listing:
                        - $(inputs.in_folder)
            inputs:
                in_folder:
                    type: Directory
                fa_database:
                    type: Directory
                scenario:
                    type: string
                # new_location:
                #     type: string
            outputs:
                out_folder:
                    type: Directory
                    outputBinding:
                        glob: "."
                        outputEval: |
                            ${
                                self[0].basename = inputs.fa_database.basename+"/output/Scenarios/"+inputs.scenario+"/Flooding/simulations/"+inputs.in_folder.basename
                                return self
                            }



            class: ExpressionTool
            requirements:
                InlineJavascriptRequirement: {}
                InitialWorkDirRequirement:
                    listing:
                        - $(inputs.fa_database)
                        - $(inputs.in_folder)

            inputs:
                fa_database:
                    type: Directory
                in_folder:
                    type: Directory
                scenario:
                    type: string
            outputs:
                fa_database:
                    type: Directory[]
            expression: |
                ${
                    // dir1 = inputs.fa_database;
                    // dir2 = inputs.in_folder;
                    // dir2.basename = dir1.basename+"/output/Scenarios/"+inputs.scenario+"/Flooding/simulations/"+inputs.in_folder.basename;
                    return {"fa_database": [
                        {"class": "Directory", "listing": inputs.fa_database.listing, "basename": inputs.fa_database.basename},
                        {"class": "Directory", "listing": inputs.in_folder.listing, "basename": inputs.fa_database.basename+"/output/Scenarios/"+inputs.scenario+"/Flooding/simulations/"+inputs.in_folder.basename}
                    ]};
                }