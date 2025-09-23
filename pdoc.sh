#!/bin/sh

# Make '/volume' directory structured for shared output (Local, Azure, Etc.)

mkdir -m777 -p /volume/doc/

#run powershell script to create __init__.py files

initFilePath="__init__.py"
if [ $(find ./src -type f -name "*.py" | wc -l) -gt 0 ]; then
  if [ ! -f "$initFilePath" ]; then
    touch "$initFilePath"
    echo "Created init file in src folder"
  fi
  subFolders=$(find ./src -type d)
  for folder in $subFolders; do
    initFilePath="$folder/__init__.py"
    if [ ! -f "$initFilePath" ]; then
      touch "$initFilePath"
      echo "Created init file in Subfolder $folder"
    fi
  done
fi

# Installing pdoc and generating documentation
/usr/local/bin/python -m pip install --upgrade pip

pip3 install pdoc3

pip3 list

cd src

pdoc --html . -f --skip-errors

# Copy over generated test results, coverage, and classes
cp -r html/src/. /volume/doc

# Ensure volume is accessible
chmod -R 777 /volume
