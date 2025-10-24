#!/bin/bash

echo "Hello, World!"

echo "File content:"
cat random-file.txt

echo "Create file" > output.txt

echo "FLUTTER_TAR_PATH=$(pwd)/edgeocr.tar.gz" >> $GITHUB_OUTPUT
