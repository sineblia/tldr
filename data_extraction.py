# Import library to extract data from XML file
import xml.etree.ElementTree as ET
import os
import pandas as pd

import xml.etree.ElementTree as ET

"""
    Extracts data from an XML file and returns it as a dictionary.

    Args:
        file (str): The path to the XML file.

    Returns:
        dict: A dictionary containing the extracted data.
"""
def extract_data(file):
    # Create a dictionary to store the data
    data = {}
    # Parse the XML file
    tree = ET.parse(file)
    # Get the root of the XML file
    root = tree.getroot()

    # Initialize abstract data
    data['abstract'] = {}

    # Initialize body data
    data['body'] = []

    # Extract title and abstract
    article_meta = root.find('.//article-meta')
    if article_meta is not None:
        title_group = article_meta.find('title-group')
        data['title'] = title_group.find('article-title').text if title_group is not None else None

        abstract_section = article_meta.find('abstract')
        if abstract_section is not None:
            for section in abstract_section.findall('sec'):
                section_title = section.find('title').text if section.find('title') is not None else ''
                section_text = section.find('p').text if section.find('p') is not None else ''
                if 'simple summary' in section_title.lower():
                    data['abstract']['simple_summary'] = section_text
                elif 'abstract' in section_title.lower():
                    data['abstract']['abstract'] = section_text

    # Extract body sections
    body_section = root.find('body')
    if body_section is not None:
        for sec in body_section.findall('sec'):
            section_data = {
                'title': sec.find('title').text if sec.find('title') is not None else None,
                'content': [p.text for p in sec.findall('p') if p.text]
            }
            data['body'].append(section_data)

    # Extract references
    references_section = root.find('.//ref-list')
    if references_section is not None:
        data['references'] = [ET.tostring(reference, encoding='unicode') for reference in references_section.findall('ref')]

    # Return the extracted data
    return data

# Extract data from the XML files
# Create a list to store the data
data = []
# Get the path of the XML files
path = './data'

# Get the list of the XML files
files = os.listdir(path)

# Loop through the XML files
for file in files:
    # Extract data from the XML file
    data.append(extract_data(path + '/' + file))