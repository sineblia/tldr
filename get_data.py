import os
import subprocess
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

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged. Successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client[db_name]
collection = db[collection_name]

# S3 bucket details
BUCKET = "s3://pmc-oa-opendata/oa_comm/xml/all/"
MAX_FILES = 100000  # Max number of files to process

# Function to process files
def process_files():
    marker = ''  # Start without a marker
    files_processed = 0

    with tqdm(total=MAX_FILES, desc="Processing files") as pbar:
        while files_processed < MAX_FILES:
            command = f"aws s3 ls {BUCKET} --no-sign-request {marker}"
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

            while True:
                line = proc.stdout.readline()
                if not line or files_processed >= MAX_FILES:
                    break
                file_list = line.decode('utf-8').strip()
                FILENAME = file_list.split()[-1]

                # Use aws s3 cp to copy the file content to stdout and capture it
                copy_command = f"aws s3 cp {BUCKET}{FILENAME} - --no-sign-request"
                file_proc = subprocess.run(copy_command, shell=True, stdout=subprocess.PIPE, text=True)

                xml_content = file_proc.stdout

                # Insert the XML content into MongoDB
                collection.insert_one({'filename': FILENAME, 'content': xml_content})

                files_processed += 1
                pbar.update(1)  # Update progress bar

                if files_processed >= MAX_FILES:
                    break

            # Set the last file processed as the marker for the next command
            marker = f"--start-after {FILENAME}"

process_files()
print("Upload completed.")
