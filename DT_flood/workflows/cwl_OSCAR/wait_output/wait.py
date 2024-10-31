from minio import Minio
import argparse

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


# Create client with access and secret key.
client = Minio(str(endpoint), accesskey, secretkey)

with client.listen_bucket_notification(
    bucket.split("/")[0],
    prefix='/'.join(bucket.split("/")[1:]),
    events=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"],
) as events:
    for event in events:
        print(event["Records"][0]["s3"]["object"]["key"])
        break
        #if(resultfile in event["Records"][0]["s3"]["object"]["key"]):
        #    info=event
        #    break