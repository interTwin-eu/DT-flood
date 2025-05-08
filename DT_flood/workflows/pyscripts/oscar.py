"""Script for triggering OSCAR service."""

import argparse
import json
import os
import tarfile
import uuid

import requests
from minio import Minio
from oscar_python.client import Client

parser = argparse.ArgumentParser()

parser.add_argument("--endpoint")
parser.add_argument("--filename")
parser.add_argument("--user", nargs="?")
parser.add_argument("--password", nargs="?")
parser.add_argument("--token", nargs="?")
parser.add_argument("--refreshtoken", nargs="?")
parser.add_argument("--service")
parser.add_argument("--service_directory")
parser.add_argument("--output", required=True)

args = parser.parse_args()

endpoint = args.endpoint
filename = args.filename
service = args.service
service_directory = args.service_directory
output = args.output

if args.user and args.password:
    user = args.user
    password = args.password
    token = None
elif args.token:
    token = args.token
    user = None
    password = None
elif args.refreshtoken:
    user = None
    password = None
    refresh_token = args.refreshtoken
    print("Fetching access token using refresh token")
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": "token-portal",
        "scope": "openid email profile voperson_id voperson_external_affiliation entitlements eduperson_entitlement",
    }
    response = requests.post(
        "https://aai-demo.egi.eu/auth/realms/egi/protocol/openid-connect/token",
        data=data,
    )
    token = response.json()["access_token"]


def check_oscar_connection():
    """Check connection to OSCAR client."""
    # Check the service or create it
    print("Checking OSCAR connection status")
    if user and password:
        options_basic_auth = {
            "cluster_id": "cluster-id",
            "endpoint": endpoint,
            "user": user,
            "password": password,
            "ssl": "True",
        }
        print("Using credentials user/password")
    elif token:
        options_basic_auth = {
            "cluster_id": "cluster-id",
            "endpoint": endpoint,
            "oidc_token": token,
            "ssl": "True",
        }
        print("Using credentials token")
    else:
        print("Introduce the credentials user/password or token")
        exit(2)

    client = Client(options=options_basic_auth)
    try:
        info = client.get_cluster_info()
        print(info)
    except Exception as err:
        print(err)
        print("OSCAR cluster not Found")
        exit(1)
    return client


def check_service(client, service, service_directory):
    """Check OSCAR service existance."""
    print("Checking OSCAR service status")
    try:
        service_info = client.get_service(service)
        minio_info = json.load(client.get_cluster_config().text)["minio_provider"]
        input_info = json.loads(service_info.text)["input"][0]
        output_info = json.loads(service_info.text)["output"][0]
        if service_info.status_code == 200:
            print("OSCAR Service " + service + " already exists")
            return minio_info, input_info, output_info
    except Exception as err:
        print("OSCAR Service " + service + " not Found")
        print(err)
        oscar_service_directory = service_directory + "/" + service
        with open(oscar_service_directory + ".yaml", "r") as file:
            data = file.read()
            data = data.replace(
                service + "_script.sh", oscar_service_directory + "_script.sh"
            )
        with open(oscar_service_directory + "_tmp.yaml", "w") as file:
            file.write(data)
        try:
            # print content of the file oscar_service_directory + "_tmp.yaml"
            print(open(oscar_service_directory + "_tmp.yaml").read())
            creation = client.create_service(oscar_service_directory + "_tmp.yaml")
            print(creation)
        except Exception as err:
            print(err)
        os.remove(oscar_service_directory + "_tmp.yaml")
        service_info = client.get_service(service)
        minio_info = json.loads(client.get_cluster_config().text)["minio_provider"]
        input_info = json.loads(service_info.text)["input"][0]
        output_info = json.loads(service_info.text)["output"][0]
        print("OSCAR Service " + service + " created")
        return minio_info, input_info, output_info


def connect_minio(minio_info):
    """Connect to MinIO."""
    # Create client with access and secret key.
    print("Creating connection with MinIO")
    client = Minio(
        minio_info["endpoint"].split("//")[1],
        minio_info["access_key"],
        minio_info["secret_key"],
    )
    return client


def upload_file_minio(client, input_info, input_file):
    """Upload input files to MinIO."""
    # Upload the file into input bucket
    print("Uploading the file into input bucket")
    random = uuid.uuid4().hex + "_" + input_file.split("/")[-1]
    print(random)
    result = client.fput_object(
        input_info["path"].split("/")[0],
        "/".join(input_info["path"].split("/")[1:]) + "/" + random,
        input_file,
    )
    print(result)
    return random.split("_")[0]


def wait_output_and_download(client, output_info, execution_id):
    """Fetch outputs from MinIO."""
    # Wait the output
    print("Waiting the output")
    with client.listen_bucket_notification(
        output_info["path"].split("/")[0],
        prefix="/".join(output_info["path"].split("/")[1:]),
        events=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"],
    ) as events:
        for event in events:
            outputfile = event["Records"][0]["s3"]["object"]["key"]
            print(event["Records"][0]["s3"]["object"]["key"])
            if execution_id in outputfile:
                print(event["Records"][0]["s3"]["object"]["key"])
                break
    # Download the file
    print("Downloading the file")
    client.fget_object(
        output_info["path"].split("/")[0],
        outputfile,
        output + "/" + outputfile.split("/")[-1],
    )
    return output + "/" + outputfile.split("/")[-1]


def compress():
    """Compress input files."""
    print("Compressing input")
    files = os.listdir(filename)
    tar_file_ = tarfile.open(filename + ".tar", "w")
    for x in files:
        tar_file_.add(name=filename + "/" + x, arcname=x)
    tar_file_.close()
    return filename + ".tar"


def decompress(output_file):
    """Decompress output files."""
    print(f"Decompressing output {output_file}")
    with tarfile.open(output_file, "r") as tar:
        for member in tar.getmembers():
            tar.extract(member, path=output)


input_file = compress()
client = check_oscar_connection()
minio_info, input_info, output_info = check_service(client, service, service_directory)
minio_client = connect_minio(minio_info)
print(f"Minio info: {minio_info}")
print(f"Input info: {input_info}")
print(f"Input file: {input_file}")
execution_id = upload_file_minio(minio_client, input_info, input_file)
print(execution_id)
output_file = wait_output_and_download(minio_client, output_info, execution_id)
decompress(output_file)
