import json
import os

p = os.getenv("SEEDFARMER_PROJECT_NAME")
d = os.getenv("SEEDFARMER_DEPLOYMENT_NAME")
m = os.getenv("SEEDFARMER_MODULE_NAME")

cdk_output = open("cdk-exports.json")
data = json.load(cdk_output)[f"{p}-{d}-{m}"]["metadata"]

with open("SEEDFARMER_MODULE_METADATA", 'w') as f:
    f.write(data)
