#!/bin/bash

# Check if two arguments are passed
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source-directory> <target-directory>"
    exit 1
fi

SOURCE_DIR=$1
TARGET_DIR=$2

# Loop through all files in the source directory
find "$SOURCE_DIR" -type f -exec basename {} \; | while read filename; do
    # Find the matching file in the target directory structure and replace it
    find "$TARGET_DIR" -type f -name "$filename" -exec cp -v "$SOURCE_DIR/$filename" {} \;
done
