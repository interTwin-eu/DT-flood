import requests
import json
import os
import uuid
import tarfile

from minio import Minio
from oscar_python import Client

def generate_token(refresh_token):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": "token_portal",
         "scope": "openid email profile voperson_id voperson_external_affiliation entitlements eduperson_entitlement"
    }
    response = requests.post(
        "https://aai-demo.egi.eu/auth/realms/egi/protocol/openid-connect/token",
        data=data
    )
    token = response.json()["access_token"]
    return token

def check_oscar_connection(endpoint, token):

    options_basic_auth = {
        "cluster_id": "cluster-id",
        "endpoint": endpoint,
        "oidc_token": token,
        "ssl": "True"
    }

    client = Client(options=options_basic_auth)
    try:
        info = client.get_cluster_info()
        print(info)
    except Exception as err:
        print(err)
        print("OSCAR cluster not Found")
        exit(1)
    return client

def check_service(client, service_path):
    # TODO: make sure service vs service+service_dir is correct. Only want to use single input for both service name and service dir
    service = service_path.stem
    service_directory = service_path.parent
    try:
        service_info = client.get_service(service)
        minio_info = json.loads(service_info.text)["storage_providers"]["minio"]["default"]
        input_info = json.loads(service_info.text)["input"][0]
        output_info = json.loads(service_info.text)["output"][0]

        if service_info.status_code == 200:
            print(f"OSCAR Service {service} already exists")
            return minio_info, input_info, output_info
        
    except Exception as err:
        print(f"OSCAR service {service} not Found")
        print(err)
        oscar_service_directory = service_directory + "/" + service
        with open(oscar_service_directory+".yaml", "r") as file:
            data = file.read()
            data = data.replace(
                service+"_script.sh", oscar_service_directory+"_script.sh"
            )
        with open(oscar_service_directory+"_tmp.yaml", "w") as file:
            file.write(data)

        try:
            print(open(oscar_service_directory+"_tmp.yaml").read())
            creation = client.create_service(oscar_service_directory+"_tmp.yaml")
            print(creation)
        except Exception as err:
            print(err)
        os.remove(oscar_service_directory+"_tmp.yaml")
        service_info = client.get_service(service)
        minio_info = json.loads(service_info.text)["storage_providers"]["minio"]["default"]
        input_info = json.loads(service_info.text)["input"][0]
        output_info = json.loads(service_info.text)["output"][0]
        print(f"OSCAR Service {service} created")
        return minio_info, input_info, output_info
    
def connect_minio(minio_info):
    client = Minio(
        minio_info["endpoint"].split("//")[1],
        minio_info["access_key"],
        minio_info["secret_key"]
    )
    return client

def upload_file_minio(client, input_info, input_file):
    print("Uploading file to bucket")
    random = uuid.uuid4().hex + "_" + input_file.split("/")[-1]
    result = client.fput_object(
        input_info["path"].split("/")[0],
        "/".join(input_info["path"].split("/")[1:])+"/"+random,
        input_file
    )
    print(result)
    return random.split("_")[0]

def wait_output_and_download(client, output_info, output_loc, execution_id):
    print("Waiting output")
    with client.listen_bucket_notification(
        output_info["path"].split("/")[0],
        prefix="/".join(output_info["path"].split("/")[1:]),
        events=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
    ) as events:
        for event in events:
            outputfile = event["Records"][0]["s3"]["object"]["key"]
            print(outputfile)
            if execution_id in outputfile:
                break

    print("Downloading File")
    client.fget_object(
        output_info["path"].split("/")[0],
        outputfile,
        output_loc+"/"+outputfile.split("/")[-1]
    )
    return output_loc+"/"+outputfile.split("/")[-1]

def compress(filename):
    print("Compressing input")
    files = os.listdir(filename)
    tar_file = tarfile.open(filename + ".tar", "w")
    for x in files:
        tar_file.add(name=filename+"/"+x, arcname=x)
    tar_file.close()
    return filename+".tar"

def decompress(output_file, output_loc):
    print(f"Decompressing output file {output_file}")
    with tarfile.open(output_file, "r") as tar:
        for member in tar.getmembers():
            tar.extract(member, path=output_loc)
