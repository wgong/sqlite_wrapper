#!/bin/bash
cd build
ctest --output-on-failure
cd ../tests/python
python -m pytest
