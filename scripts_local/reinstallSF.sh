#!/bin/bash


uv build
uv tool install dist/seed_farmer-6.2.0.dev0-py3-none-any.whl --force

#uv tool uninstall seed_farmer