#!/bin/bash

rm -rf dist

uv build

# Log in
aws codeartifact login \
    --tool twine \
    --repository python-repository \
    --domain aws-codeseeder-refactor \
    --domain-owner 616260033377 \
    --region us-east-1

# Delete the seedfarmer package
aws codeartifact delete-package \
  --domain aws-codeseeder-refactor \
  --repository python-repository \
  --format pypi \
  --package seed-farmer \
  --region us-east-1



twine upload --repository codeartifact dist/*