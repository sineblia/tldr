#!/bin/bash

# This script is used for text mining and processing.
# It defines the BUCKET variable which represents the S3 bucket path for the input files.
# The DESTINATION variable represents the local directory where the processed files will be stored.
BUCKET="s3://pmc-oa-opendata/oa_comm/xml/all/"
DESTINATION="./pmc-test/"


# Retrieves the list of files in the AWS S3 bucket, copies the first 100 files to a specified destination,
# and performs the copy operation without requiring a sign request.
aws s3 ls ${BUCKET} --no-sign-request | head -100 | while read -r line; do
   FILENAME=$(echo $line | awk '{print $4}')
   aws s3 cp ${BUCKET}${FILENAME} ${DESTINATION}${FILENAME} --no-sign-request
done
