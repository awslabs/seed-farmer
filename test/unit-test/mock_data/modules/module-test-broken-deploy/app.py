#!/usr/bin/env python3

import json
import os

from aws_cdk import core
from infrastructure.ecs_stack import Fargate

# Load config
project_dir = os.path.dirname(os.path.abspath(__file__))

config_file = os.path.join(project_dir, "config.json")

with open(config_file) as json_file:
    config = json.load(json_file)

print(config)

image_name = config["image-name"]
stack_id = config["stack-id"]
ecr_repository_name = config["ecr-repository-name"]

cpu = config["cpu"]
memory_limit_mib = config["memory-limit-mib"]
timeout_minutes = config["timeout-minutes"]

default_environment_vars = config["environment-variables"]

app = core.App()

Fargate(
    app,
    stack_id,
    image_name=image_name,
    environment_vars=default_environment_vars,
    ecr_repository_name=ecr_repository_name,
    cpu=cpu,
    description="(SO9013) - Autonomous Vehicle Datalake-V1.0.0 - Template",
    memory_limit_mib=memory_limit_mib,
    timeout_minutes=timeout_minutes,
    env=core.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]),
)

app.synth()
