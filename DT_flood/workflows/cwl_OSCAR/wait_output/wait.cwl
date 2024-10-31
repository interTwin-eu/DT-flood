#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: python
arguments: [$(inputs.waitScript),"--bucket",$(inputs.bucket), "--endpoint",$(inputs.minioEndpoint),"--accesskey",$(inputs.minioAccesskey),"--secretkey",$(inputs.minioSecretkey)]
inputs:
  waitScript:
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
    fa_database_out:
        type: Directory