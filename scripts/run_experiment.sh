#!/bin/sh
set -eu
python -m crypto_bench preflight
python -m crypto_bench validate
python -m crypto_bench run --category all
