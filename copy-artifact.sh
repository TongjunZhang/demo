#!/bin/sh
# Make '/volume' directory structured for shared output (Local, Azure, Etc.)
mkdir -m777 -p /volume/distributions/
cp -R /package /src
(
cd /src/package ||exit
zip -r ../project.zip .
)
zip -g project.zip lambda_function.py
cp /src/project.zip /volume/distributions/project.zip
# Ensure volume is accessible
chmod -R 777 /volume
