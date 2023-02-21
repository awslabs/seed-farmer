import json
import os

p = os.getenv("AWS_CODESEEDER_NAME")
p_fetch = p.replace("-","_").upper()

d = os.getenv(f"{p_fetch}_DEPLOYMENT_NAME")
m = os.getenv(f"{p_fetch}_MODULE_NAME")
cdk_output = open("cdk-exports.json")
data = json.load(cdk_output)[f"{p}-{d}-{m}"]["metadata"]

with open(f"{p_fetch}_MODULE_METADATA", 'w') as f:
    f.write(data)
