#!/usr/bin/env python

import argparse
import base64
import json
import logging
import os
import subprocess
from typing import Dict, Optional, cast
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret(secret_name: str) -> Dict[str, Dict[str, str]]:
    region_name = os.environ.get("AWS_DEFAULT_REGION")
    try:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as ce:
        logger.info("Secret with SecretId '%s' could not be retrieved from SecretsManager", secret_name)
        print(f"Secret with SecretId {secret_name} could not be retrieved from SecretsManager - {ce}")
        exit(1)
    except FileNotFoundError:
        logger.info("Make sure AWW credentials are set")
        print("Make sure credentials  AWW credentials are set")
        exit(1)
    else:
        return cast(Dict[str, Dict[str, str]], json.loads(get_secret_value_response.get("SecretString", "{}")))


def get_auth(username: Optional[str] = None, password: Optional[str] = None, ssl_token: Optional[str] = None) -> str:
    if ssl_token:
        logger.info("ssl_token found and being used in url")
        return ssl_token

    if (username and not password) or (not username and password):
        logger.error("For NPM mirror auth support, both username and password must be provided")
        raise RuntimeError("For NPM mirror auth support, both username and password must be provided")
    else:
        logger.info("Both username and password found, encoding for use in url")
        return base64.b64encode((f"{username}:{password}").encode("ascii")).decode("ascii")


def main(url: str) -> None:
    secret_name = os.environ.get("SEEDFARMER_NPM_MIRROR_SECRET", "NO_SECRET")
    # Backwards Compatibility
    if secret_name == "NO_SECRET":
        secret_name = os.environ.get("AWS_CODESEEDER_NPM_MIRROR_SECRET", "NO_SECRET")
    elif secret_name == "NO_SECRET":
        secret_name = os.environ.get("AWS_CODESEEDER_MIRROR_SECRET", "NO_SECRET")

    if secret_name != "NO_SECRET":
        secret_name_key = secret_name.split("::")[0] if "::" in secret_name else secret_name
        key = secret_name.split("::")[1] if "::" in secret_name else "npm"
        creds = get_secret(secret_name=secret_name_key)
        if key in creds.keys():
            username = creds[key].get("username") if creds[key].get("username") else None
            password = creds[key].get("password") if creds[key].get("password") else None
            ssl_token = creds[key].get("ssl_token") if creds[key].get("ssl_token") else None
            try:
                auth = get_auth(username, password, ssl_token)
            except RuntimeError:
                logger.error(f"The auth token could not be generated - check the secret {secret_name}")
                exit(1)
            registry_url = urlparse(url).netloc
            npm_key = f"//{registry_url}/:_auth"
            process = subprocess.Popen(
                ["npm", "config", "set", npm_key, auth],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process.communicate()
            print(f"Setting npm config WITH auth:  {url}")
    else:
        logger.info("'NPM_MIRROR_SECRET' is not set")
        print("'NPM_MIRROR_SECRET' is not set")
        print(f"Setting npm config WITHOUT auth:  {url}")
    subprocess.call(["npm", "config", "set", "registry", url])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URL to evaluate")
    parser.add_argument("url", type=str, help="The url to set in npm'")
    args = parser.parse_args()
    main(args.url)
