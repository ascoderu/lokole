#!/usr/bin/env bash

make $TARGET -e py_env=~/virtualenv/python$TRAVIS_PYTHON_VERSION
