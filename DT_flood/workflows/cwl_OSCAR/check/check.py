from minio import Minio
import argparse
from oscar_python.client import Client


parser = argparse.ArgumentParser()

parser.add_argument("--endpoint")
parser.add_argument("--filename")
parser.add_argument("--user")
parser.add_argument("--password")
parser.add_argument("--service")

args = parser.parse_args()
variables = vars(args)
#print(variables)

endpoint=variables['endpoint']
filename=variables['filename']
user=variables['user']
password=variables['password']
service=variables['service']


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
    service = client.get_service(service)
    if service.status_code == 200:
        print("Service already exits")
except Exception as err:
    print("Service not Found")
    creation = client.create_service("../wflow.yaml")
    print("Service Created")
    exit(2)

