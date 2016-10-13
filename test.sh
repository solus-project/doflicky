#!/bin/bash

pep8 ypkg-build doflicky/*.py main.py || exit 1
flake8 ypkg-build doflicky/*.py main.py || exit 1

