#!/bin/bash
mkdir -p build
cd build
cmake ..
make
cd ../src/python
pip install -e .
