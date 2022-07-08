import json,os
p=os.getenv("AWS_CODESEEDER_NAME")
d=os.getenv(f"{p.upper()}_DEPLOYMENT_NAME")
m=os.getenv(f"{p.upper()}_MODULE_NAME")
file=open('cdk-exports.json'); 
print(json.load(file)[f'{p}-{d}-{m}']['metadata'])