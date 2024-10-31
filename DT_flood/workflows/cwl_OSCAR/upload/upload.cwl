#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: python
arguments: [$(inputs.uploadScript),"--bucket",$(inputs.bucket),"--filename", $(inputs.file), "--endpoint",$(inputs.minioEndpoint),"--accesskey",$(inputs.minioAccesskey),"--secretkey",$(inputs.minioSecretkey)]
inputs:
  file:
    type: Directory?
  uploadScript:
    type: File?
  bucket:
    type: string
  minioEndpoint:
    type: string
  minioAccesskey:
    type: string
  minioSecretkey:
    type: string
outputs:
  example_out:
    type: stdout
stdout: output.txt
