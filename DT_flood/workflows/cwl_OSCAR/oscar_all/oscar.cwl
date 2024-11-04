#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: python
arguments: [$(inputs.oscarScript),"--endpoint",$(inputs.endpoint), "--user",$(inputs.user), "--password",$(inputs.password), "--service",$(inputs.service), "--filename", $(inputs.filename),"--service_directory",$(inputs.oscarService)]

inputs:
  oscarScript:
    type: File?
  endpoint:
    type: string
  user:
    type: string
  password:
    type: string
  service:
    type: string
  filename:
    type: File?
  oscarService:
    type: Directory?
outputs:
    fa_database_out:
        type: Directory