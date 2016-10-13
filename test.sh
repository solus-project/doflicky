#!/bin/bash

pep8 doflicky/*.py main.py || exit 1
flake8 doflicky/*.py main.py || exit 1

