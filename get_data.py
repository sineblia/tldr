import os
import boto3
from botocore import UNSIGNED
from botocore.client import Config
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Setup MongoDB
mongo_conn_string = os.environ['MONGO_CONN_STRING']
db_name = os.environ['DB_NAME']
collection_name = os.environ['COLLECTION_NAME']

client = MongoClient(mongo_conn_string, server_api=ServerApi('1'))
db = client[db_name]
collection = db[collection_name]

# Setup AWS S3 client
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
bucket_name = 'pmc-oa-opendata'
prefix = 'oa_comm/xml/all/'

# Set max number of files and batch size for insertion
MAX_FILES = 100000
BATCH_SIZE = 100

def process_files():
    processed_files = 0
    batch_data = []
    
    # Create an index on the 'filename' field if it doesn't exist for faster lookups
    collection.create_index('filename', unique=True)

    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    with tqdm(total=MAX_FILES, desc="Processing files") as pbar:
        for page in page_iterator:
            if processed_files >= MAX_FILES:
                break
            for obj in page['Contents']:
                key = obj['Key']
                # Check if the file is already in the database
                if collection.count_documents({'filename': key}) == 0:
                    response = s3.get_object(Bucket=bucket_name, Key=key)
                    xml_content = response['Body'].read()

                    # Append to batch data
                    batch_data.append({'filename': key, 'content': xml_content})
                    processed_files += 1

                    # If batch size is reached, insert into MongoDB
                    if len(batch_data) == BATCH_SIZE:
                        collection.insert_many(batch_data)
                        batch_data = []  # Reset the batch data list

                    pbar.update(1)

                    # Break if max files reached
                    if processed_files >= MAX_FILES:
                        break

            # Insert any remaining files in batch_data
            if batch_data:
                collection.insert_many(batch_data)

    print(f"Data collection complete. {processed_files} new files added.")

process_files()
print("Data collection complete.")