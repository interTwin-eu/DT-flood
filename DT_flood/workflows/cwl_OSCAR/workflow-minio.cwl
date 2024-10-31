#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: Workflow

requirements:
  InlineJavascriptRequirement: {}

inputs:
  file:
    type: Directory?
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
  out:
    type: File?
    outputSource: wait/example_out
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
    out: [example_out]