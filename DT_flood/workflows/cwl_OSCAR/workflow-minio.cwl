#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: Workflow

requirements:
  InlineJavascriptRequirement: {}

inputs:
  file:
    type: File?
  uploadScript:
    type: File?
  waitScript:
    type: File?
  minioEndpoint:
    type: string
  minioAccesskey:
    type: string
  minioSecretkey:
    type: string
  bucketInput:
    type: string
  bucketOutput:
    type: string
outputs:
    fa_database_out:
        type: Directory
        
steps:

  upload:
    run: upload/upload.cwl
    in:
      file: file
      uploadScript: uploadScript
      bucket: bucketInput
      minioEndpoint: minioEndpoint
      minioAccesskey: minioAccesskey
      minioSecretkey: minioSecretkey
    out: [example_out]
  wait:
    run: wait_output/wait.cwl
    in:
      waitScript: waitScript
      bucket: bucketOutput
      minioEndpoint: minioEndpoint
      minioAccesskey: minioAccesskey
      minioSecretkey: minioSecretkey
      data: 
        source: upload/example_out
    # out: [fa_database_out]
    out: [std_out]