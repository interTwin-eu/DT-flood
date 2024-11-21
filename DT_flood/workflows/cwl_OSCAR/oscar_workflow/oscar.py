import argparse
import json
import os
from minio import Minio
from oscar_python.client import Client
import tarfile

parser = argparse.ArgumentParser()

parser.add_argument("--endpoint")
parser.add_argument("--filename")
parser.add_argument("--user")
parser.add_argument("--password")
parser.add_argument("--service")
parser.add_argument("--service_directory")
parser.add_argument("--output")

args = parser.parse_args()
variables = vars(args)
#print(variables)

endpoint = variables['endpoint']
filename = variables['filename']
user = variables['user']
password = variables['password']
service = variables['service']
service_directory = variables['service_directory']
output = variables['output']


def check_oscar_connection():
    # Check the service or create it
    print("Checking OSCAR connection status")
    options_basic_auth = {'cluster_id':'cluster-id',
                    'endpoint': endpoint,
                    'user':user,
                    'password':password,
                    'ssl':'True'}

    client = Client(options = options_basic_auth)
    try:
        info = client.get_cluster_info()
    except Exception as err:
        print("OSCAR cluster not Found")
        exit(1)
    return client


def check_service(client,service,service_directory):
    print("Checking OSCAR service status")
    try:
        service_info = client.get_service(service)
        minio_info = json.loads(service_info.text)["storage_providers"]["minio"]["default"]
        input_info = json.loads(service_info.text)["input"][0]
        output_info = json.loads(service_info.text)["output"][0]
        if service_info.status_code == 200:
            print("OSCAR Service " + service + " already exists")
            return minio_info, input_info, output_info
    except Exception as err:
        print("OSCAR Service " + service + " not Found")
        oscar_service_directory = service_directory + "/" + service
        with open(oscar_service_directory + ".yaml", 'r') as file: 
            data = file.read()
            data = data.replace(service + "_script.sh",
                                oscar_service_directory + "_script.sh") 
        with open(oscar_service_directory + "_tmp.yaml", 'w') as file: 
            file.write(data) 

        creation = client.create_service(oscar_service_directory + "_tmp.yaml")
        os.remove(oscar_service_directory + "_tmp.yaml") 
        service_info = client.get_service(service)
        minio_info = json.loads(service_info.text)["storage_providers"]["minio"]["default"]
        input_info = json.loads(service_info.text)["input"][0]
        output_info = json.loads(service_info.text)["output"][0]
        print("OSCAR Service " + service + " created")
        return minio_info, input_info, output_info


def connect_minio(minio_info):
    # Create client with access and secret key.
    print("Creating connection with MinIO")
    client = Minio(minio_info["endpoint"].split("//")[1],
                   minio_info["access_key"],
                   minio_info["secret_key"]
    )
    return client


def upload_file_minio(client, input_info, input_file):
    #Upload the file into input bucket
    print("Uploading the file into input bucket")
    result = client.fput_object(
        input_info["path"].split("/")[0],
        '/'.join(input_info["path"].split("/")[1:]) + "/" + input_file.split("/")[-1],
        input_file,
    )


def wait_output_and_download(client, output_info):
    #Wait the output 
    print("Waiting the output")
    with client.listen_bucket_notification(
        output_info["path"].split("/")[0],
        prefix='/'.join(output_info["path"].split("/")[1:]),
        events=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"],
    ) as events:
        for event in events:
            outputfile = event["Records"][0]["s3"]["object"]["key"]
            print(event["Records"][0]["s3"]["object"]["key"])
            break
    #Download the file
    print("Downloading the file")
    client.fget_object(output_info["path"].split("/")[0], 
                    outputfile,
                    output + "/" + outputfile.split("/")[-1]
    )
    return output + "/" + outputfile.split("/")[-1]


def compress():
    print("Compressing input")
    files = os.listdir(filename)
    tar_file_ = tarfile.open(filename + ".tar", "w")
    for x in files:
        tar_file_.add( name=filename + "/" +x, arcname=x)
    tar_file_.close()
    return filename + ".tar"



def decompress(output_file):
    print("Decompressing output")
    with tarfile.open(output_file, 'r') as tar:
        for member in tar.getmembers():
            tar.extract(member, path=output)

input_file = compress()
client = check_oscar_connection()
minio_info, input_info, output_info = check_service(client, service, service_directory)
minio_client = connect_minio(minio_info)
upload_file_minio(minio_client, input_info, input_file)
output_file = wait_output_and_download(minio_client, output_info)
decompress(output_file)
