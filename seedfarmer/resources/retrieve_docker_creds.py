#!/usr/bin/env python

import json
import logging
import os
import subprocess
from typing import Dict, cast

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret() -> Dict[str, Dict[str, str]]:
    secret_name = os.environ.get("AWS_CODESEEDER_DOCKER_SECRET", "NO_SECRET")
    region_name = os.environ.get("AWS_DEFAULT_REGION")

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError:
        logger.info("Secret with SecretId '%s' could not be retrieved from SecretsManager")
        return {}
    else:
        return cast(Dict[str, Dict[str, str]], json.loads(get_secret_value_response.get("SecretString", "{}")))


if __name__ == "__main__":
    credentials = get_secret()
    for registry, creds in credentials.items():
        username = creds["username"]
        password = creds["password"]
        subprocess.call(["docker", "login", "--username", username, "--password", password, registry])
