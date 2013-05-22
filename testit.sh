#!/bin/bash

cd gics
export PYTHONPATH=lib/
python -m unittest discover t/ '*_test.py'

