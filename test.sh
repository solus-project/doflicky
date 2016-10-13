#!/bin/bash

pep8 doflicky/*.py doflicky-ui || exit 1
flake8 doflicky/*.py doflicky-ui || exit 1

