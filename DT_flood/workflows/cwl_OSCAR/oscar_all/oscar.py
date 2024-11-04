from minio import Minio
import argparse
from oscar_python.client import Client
import json
import os

parser = argparse.ArgumentParser()

parser.add_argument("--endpoint")
parser.add_argument("--filename")
parser.add_argument("--user")
parser.add_argument("--password")
parser.add_argument("--service")
parser.add_argument("--service_directory")

args = parser.parse_args()
variables = vars(args)
#print(variables)

endpoint=variables['endpoint']
filename=variables['filename']
user=variables['user']
password=variables['password']
service=variables['service']
service_directory=variables['service_directory']


# Check the service or create it
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
try:
    serviceinfo = client.get_service(service)
    minioinfo = json.loads(serviceinfo.text)["storage_providers"]["minio"]["default"]
    inputinfo = json.loads(serviceinfo.text)["input"][0]
    outputinfo = json.loads(serviceinfo.text)["output"][0]
    if serviceinfo.status_code == 200:
        print("Service already exits")
except Exception as err:
    print("Service not Found")
    with open(service_directory+"/wflow.yaml", 'r') as file: 
        data = file.read()
        data = data.replace("wflow_script.sh", service_directory+"/wflow_script.sh") 
        
    # Opening our text file in write only 
    # mode to write the replaced content 
    with open(service_directory+"/wflow_tmp.yaml", 'w') as file: 
        # Writing the replaced data in our 
        # text file 
        file.write(data) 

    creation = client.create_service(service_directory+"/wflow_tmp.yaml")
    os.remove(service_directory+"/wflow_tmp.yaml") 
    serviceinfo = client.get_service(service)
    minioinfo = json.loads(serviceinfo.text)["storage_providers"]["minio"]["default"]
    inputinfo = json.loads(serviceinfo.text)["input"][0]
    outputinfo = json.loads(serviceinfo.text)["output"][0]
    print("Service Created")

# Create client with access and secret key.
print("Creating connection with MinIO")
client = Minio(minioinfo["endpoint"].split("//")[1], minioinfo["access_key"] , minioinfo["secret_key"])


#Upload the file into input bucket
print("Uploading the file into input bucket")
result = client.fput_object(
    inputinfo["path"].split("/")[0],
    '/'.join(inputinfo["path"].split("/")[1:])+"/"+filename.split("/")[-1],
    filename,
)



#Wait the output 
print("Waiting the output ")
with client.listen_bucket_notification(
    outputinfo["path"].split("/")[0],
    prefix='/'.join(outputinfo["path"].split("/")[1:]),
    events=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"],
) as events:
    for event in events:
        outputfile=event["Records"][0]["s3"]["object"]["key"]
        print(event["Records"][0]["s3"]["object"]["key"])
        break

#Download the file
print("Downloading the file")
client.fget_object(outputinfo["path"].split("/")[0], 
                   outputfile,
                   filename+".nc")