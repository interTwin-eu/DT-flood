#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: python
arguments: [$(inputs.oscar_script),"--endpoint",$(inputs.endpoint), "--user",$(inputs.user), "--password",$(inputs.password), "--service",$(inputs.service), "--filename", $(inputs.filename),"--service_directory",$(inputs.oscar_service),"--output",$(inputs.output)]


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
    type: Directory?