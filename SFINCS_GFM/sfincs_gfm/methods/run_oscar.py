from pathlib import Path

from hydroflows.workflow.method_parameters import Parameters
from hydroflows.workflow.method import Method
from hydroflows._typing import OutputDirPath, FileDirPath

from sfincs_gfm.methods.utils_oscar import (
    compress,
    decompress,
    generate_token,
    check_oscar_connection,
    check_service,
    connect_minio,
    upload_file_minio,
    wait_output_and_download
)

class Input(Parameters):

    input_file: FileDirPath

class Output(Parameters):

    output_file: FileDirPath

class Params(Parameters):

    service: Path
    refreshtoken: str
    endpoint: str = ""
    output_loc: OutputDirPath = "output"

class RunOscarService(Method):

    name: str = "run_oscar_service"

    def __init__(
        self,
        input_file: Path,
        service: Path,
        refreshtoken: str,
        **params
    ):
        self.params: Params = Params(
            service=service,
            refreshtoken=refreshtoken,
            **params
        )
        self.input: Input = Input(
            input_file=input_file
        )

        output_file = self.params.output_loc / self.input.input_file.name
        self.output: Output = Output(
            output_file=output_file
        )

    def _run(self):

        input_dir = self.input.input_file.parent
        output_loc = self.params.output_loc
        endpoint = self.params.endpoint
        refreshtoken = self.params.refreshtoken
        service = self.params.service

        token = generate_token(refresh_token=refreshtoken)

        inputs = compress(input_dir)
        client = check_oscar_connection(endpoint=endpoint, token=token)
        minio_info, input_info, output_info = check_service(client=client, service_path=service)
        minio_client = connect_minio(minio_info=minio_info)
        print(f"Minio info: {minio_info}")
        print(f"Input info: {input_info}")
        print(f"Input file: {inputs}")
        execution_id = upload_file_minio(minio_client, input_info=input_info, input_file=inputs)
        outputs = wait_output_and_download(minio_client, output_info=output_info, execution_id=execution_id, output_loc=output_loc)
        decompress(output_file=outputs, output_loc=output_loc)
