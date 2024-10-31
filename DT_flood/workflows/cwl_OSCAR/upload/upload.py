from minio import Minio
import argparse
import tarfile
import os.path


parser = argparse.ArgumentParser()

parser.add_argument("--bucket")
parser.add_argument("--filename")
parser.add_argument("--endpoint")
parser.add_argument("--accesskey")
parser.add_argument("--secretkey")

args = parser.parse_args()
variables = vars(args)
#print(variables)

bucket=variables['bucket']
filename=variables['filename']
endpoint=variables['endpoint']
accesskey=variables['accesskey']
secretkey=variables['secretkey']

#print (bucket.split("/")[0],)
#print('/'.join(sys.argv[1].split("/")[1:]))
#print(filename.split("/")[-1])
#print(filename)

# Create client with access and secret key.
with tarfile.open(filename+".tar", "w:gz") as tar:
        tar.add(filename, arcname=os.path.basename(filename))
client = Minio(str(endpoint), accesskey, secretkey)

result = client.fput_object(
    bucket.split("/")[0], '/'.join(bucket.split("/")[1:])+"/"+filename.split("/")[-1], filename+".tar",
)