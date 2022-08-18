#!/bin/bash

pytest test/unit-test/*.py -v --cov=seedfarmer --cov-report=html --cov-report=xml
