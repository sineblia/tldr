# Import library to extract data from XML file
import xml.etree.ElementTree as ET
import io
import os
import json
from pymongo import MongoClient
import re
import logging
import string
from dotenv import load_dotenv

load_dotenv()

BATCH_SIZE = 50

# MongoDB setup
mongo_conn_string = os.environ['MONGO_CONN_STRING']
db_name = os.environ['DB_NAME']
xml_collection_name = os.environ['XML_COLLECTION']
json_raw_collection_name = os.environ['JSON_RAW_COLLECTION']

client = MongoClient(mongo_conn_string)
db = client[db_name]
xml_collection = db[xml_collection_name]
json_raw_collection = db[json_raw_collection_name]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def document_already_processed(mongo_id, json_raw_collection):
    return json_raw_collection.count_documents({'original_id': mongo_id}, limit=1) > 0

def extract_information_from_xml(xml_content):
    """
    Parameters:
    xml_path (str): Path to the XML file.

    Returns:
    dict: A dictionary containing the extracted information, with separated abstract sub-layers.
    """
    try:
        # Parse the XML content
        root = ET.fromstring(xml_content)

        # Initialize a dictionary to hold the extracted information
        extracted_info = {
            'Title': '',
            'Abstract': {'Simple Summary': '', 'Detailed Abstract': ''},
            'Sections': [],
            'Keywords': []
        }

        # Extract Title
        title_element = root.find('.//article-title')
        if title_element is not None:
            extracted_info['Title'] = ''.join(title_element.itertext())

        # Extract Abstracts
        abstract_element = root.find('.//abstract')
        if abstract_element is not None:
            sec_elements = abstract_element.findall('.//sec')
            for sec in sec_elements:
                section_title = ''.join(sec.find('.//title').itertext()).strip() if sec.find('.//title') is not None else ""
                section_text = ''.join(sec.itertext()).strip()
                
                # Remove the section title from the beginning of the section text
                if section_text.startswith(section_title):
                    section_text = section_text[len(section_title):].strip()
                
                if 'simple summary' in section_title.lower():
                    extracted_info['Abstract']['Simple Summary'] = section_text
                else:
                    # Append other sections to the 'Detailed Abstract', removing repeated titles if present
                    if extracted_info['Abstract']['Detailed Abstract']:
                        extracted_info['Abstract']['Detailed Abstract'] += ' ' + section_text
                    else:
                        extracted_info['Abstract']['Detailed Abstract'] = section_text
            
        # Extract Keywords
        kwd_group_elements = root.findall('.//kwd-group')
        for kwd_group in kwd_group_elements:
            keywords = [kwd.text for kwd in kwd_group.findall('.//kwd')]
            extracted_info['Keywords'].extend(keywords)

        # Extract Sections
        sections = root.findall('.//body//sec')
        for sec in sections:
            section_title_element = sec.find('.//title')
            if section_title_element is not None:
                section_title = ''.join(section_title_element.itertext())
                # Remove the title element to avoid repetition in the content
                sec.remove(section_title_element)
            else:
                section_title = "No Title"
            
            # Extracting content after removing the title
            section_content = ''.join(sec.itertext()).strip()
            extracted_info['Sections'].append({
                'Title': section_title,
                'Content': section_content
            })

        return extracted_info
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def process_document(mongo_id, xml_collection):
    try:
            # Retrieve only the 'content' and 'filename' fields
            document = xml_collection.find_one({'_id': mongo_id}, {'content': 1, 'filename': 1})

            # Extract information from XML content
            extracted_info = extract_information_from_xml(document['content'])

            # Get the title (filename without the .xml extension)
            title = document['filename'].rsplit('.', 1)[0]

            # Insert the dictionary to the JSON_RAW_COLLECTION
            json_document = {
                'mongo_id': mongo_id,
                'title': title,
                'content': extracted_info,
            }
            return json_document
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None

batch_data = []
for document in xml_collection.find({}):
    if not document_already_processed(document['_id'], json_raw_collection):
        json_document = process_document(document['_id'], xml_collection)
        if json_document:
            batch_data.append(json_document)

            # When the batch size is reached, insert the documents into MongoDB
            if len(batch_data) >= BATCH_SIZE:
                json_raw_collection.insert_many(batch_data)
                logging.info(f"Batch of {len(batch_data)} documents inserted into {json_raw_collection_name}")
                batch_data = []  # Reset the batch for the next set of documents

# Insert any remaining documents that didn't make a full batch
if batch_data:
    json_raw_collection.insert_many(batch_data)
    logging.info(f"Final batch of {len(batch_data)} documents inserted into {json_raw_collection_name}")