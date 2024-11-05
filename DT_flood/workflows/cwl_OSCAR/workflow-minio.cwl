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
    type: string
  password:
    type: string
  service:
    type: string
  filename:
    type: File
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
  oscar:
    run: oscar_all/oscar.cwl
    in:
      oscar_script: oscar_script
      endpoint: endpoint
      user: user
      password: password
      service: service
      filename: filename
      oscar_service: oscar_service
      output: output
    out: [fa_database_out]
