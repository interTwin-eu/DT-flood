#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: Workflow

requirements:
  InlineJavascriptRequirement: {}

inputs:
  oscar_script:
    type: File
  endpoint:
    type: string
  user:
    type: string?
  password:
    type: string?
  token:
    type: string?
  service_wflow:
    type: string
  service_sfincs:
    type: string
  filename_wflow:
    type: Directory
  filename_sfincs:
    type: Directory
  oscar_service:
    type: Directory
  output:
    type: Directory

outputs:
  fa_database_out:
    type:
      type: array
      items: [File, Directory, string]
      
steps:
  wflow:
    run: oscar_workflow/oscar.cwl
    in:
      oscar_script: oscar_script
      endpoint: endpoint
      user: user
      password: password
      token: token
      service: service_wflow
      filename: filename_wflow
      oscar_service: oscar_service
      output: output
    out: [fa_database_out]
  sfincs:
    run: oscar_workflow/oscar.cwl  
    in:
      oscar_script: oscar_script
      endpoint: endpoint
      user: user
      password: password
      token: token
      service: service_sfincs
      filename: filename_sfincs
      oscar_service: oscar_service
      output: output
    out: [fa_database_out]