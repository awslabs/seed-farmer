#!/bin/bash

pytest test/unit-test/test_cli_arg.py -v --cov=seedfarmer --cov-report=html --cov-report=xml
