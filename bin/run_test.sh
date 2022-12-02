#!/usr/bin/env bash
tag=$1
echo "============================= Running tests with $tag ============================="
pytest -x --html=./reports/"$tag".html --self-contained-html --show-capture=stdout -vv -rP test_files/ -m "$tag"
echo "============================= Test run with $tag finished ========================="