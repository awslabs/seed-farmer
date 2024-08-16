#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License").
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import os
from io import open
from typing import Dict

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
about: Dict[str, str] = {}
path = os.path.join(here, "seedfarmer", "__metadata__.py")
with open(file=path, mode="r", encoding="utf-8") as f:
    exec(f.read(), about)

with open("VERSION", "r") as version_file:
    version = version_file.read().strip()

with open("README.md", "r") as file:
    long_description = file.read()

setup(
    name=about["__title__"],
    version=version,
    author="AWS Professional Services",
    author_email="aws-proserve-opensource@amazon.com",
    url="https://github.com/awslabs/seed-farmer",
    project_urls={"Org Site": "https://aws.amazon.com/professional-services/"},
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=about["__license__"],
    packages=find_packages(include=["seed-farmer", "seedfarmer", "seedfarmer.*", "seed-farmer.*"]),
    keywords=["aws", "cdk"],
    python_requires=">=3.8,<3.13",
    install_requires=[
        "aws-codeseeder~=1.1.0",
        "cookiecutter>=2.1,<2.7",
        "pyhumps>=3.5,<3.9",
        "pydantic>=2.8.2,<2.9.0",
        "executor~=23.2",
        "typing-extensions>=4.6.3",
        "rich>=12.4,<13.8",
        "requests>=2.28,<2.33",
        "python-dotenv>=0.21,<1.1",
        "gitpython~=3.1.30",
        "gitignore-parser~=0.1.2",
        "pyyaml~=6.0.1",
        "urllib3~=1.26.17",
        "certifi>=2024.7.4,<2024.8.0",
        "packaging>=23.2,<25.0",
    ],
    entry_points={"console_scripts": ["seedfarmer = seedfarmer.__main__:main"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    include_package_data=True,
)
