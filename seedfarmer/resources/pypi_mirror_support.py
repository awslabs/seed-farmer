#!/usr/bin/env python

import argparse
import json
import logging
import os
import subprocess
from typing import Dict, Optional, Tuple, cast

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret(secret_name: str) -> Dict[str, Dict[str, str]]:
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


def create_url(url: str, username: Optional[str] = None, password: Optional[str] = None) -> Tuple[str, str]:
    if url.startswith("http://"):
        logger.info("URL is unsecured, no passwords will be set and url used as-is")
        return url, url
    if url.startswith("https://"):
        if username is not None and password is not None:
            s = url.split("https://")
            secured_url = f"https://{username}:{password}@{s[1]}"
            obfusctated_url = f"https://XXXX:XXXX@{s[1]}"
            return secured_url, obfusctated_url
        else:
            logger.info("Username and / or password not set, using URL as-is")
            return url, url
    return url, url


def setup_pypi(obfusctated_url: str, secured_url: str) -> None:
    logger.info("Calling pip config with %s", obfusctated_url)
    print(f"pip config being set for : {obfusctated_url}")
    subprocess.call(["pip", "config", "set", "global.index-url", secured_url])


def setup_uv(obfusctated_url: str, secured_url: str) -> None:
    logger.info("Setting up uv.config %s", obfusctated_url)
    print(f"uv configured at  ~/.config/uv/uv.toml : {obfusctated_url}")
    toml_content = f"""[[index]]
    name = "internal-proxy"
    url = "{secured_url}"
    default = true
    """
    uv_config_path = os.path.expanduser("~/.config/uv")
    os.makedirs(uv_config_path, exist_ok=True)

    # Write to file
    with open(os.path.join(uv_config_path, "uv.toml"), "w") as f:
        f.write(toml_content)


def main(url: str) -> None:
    secret_name = os.environ.get("SEEDFARMER_PYPI_MIRROR_SECRET", "NO_SECRET")
    # Backwards Compatibility
    if secret_name == "NO_SECRET":
        secret_name = os.environ.get("AWS_CODESEEDER_PYPI_MIRROR_SECRET", "NO_SECRET")
    elif secret_name == "NO_SECRET":
        secret_name = os.environ.get("AWS_CODESEEDER_MIRROR_SECRET", "NO_SECRET")
    username = None
    password = None
    if secret_name not in ["NO_SECRET"]:
        secret_name_key = secret_name.split("::")[0] if "::" in secret_name else secret_name
        key = secret_name.split("::")[1] if "::" in secret_name else "pypi"
        creds = get_secret(secret_name=secret_name_key)
        if key in creds.keys():
            username = creds[key]["username"] if creds[key].get("username") else None
            password = creds[key]["password"] if creds[key].get("password") else None

    secured_url, obfusctated_url = create_url(url, username, password)
    setup_pypi(obfusctated_url=obfusctated_url, secured_url=secured_url)
    setup_uv(obfusctated_url=obfusctated_url, secured_url=secured_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URL to evaluate")
    parser.add_argument("url", type=str, help="The url to set in pypi'")
    args = parser.parse_args()
    main(args.url)
