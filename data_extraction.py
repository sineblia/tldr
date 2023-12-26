# Import library to extract data from XML file
import xml.etree.ElementTree as ET
import os
import pandas as pd

"""
    Function to extract data from XML file
    Input: XML file
    Output: Dataframe
    The XML file contains the following information:
    - article-meta: this section contains metadata on the article
    - body: this section contains the body of the article, divided into sections ('sec')
    - back: this section contains the references of the article
    We need to extract informations from these sections
"""

def extract_data(file):
    # Create a dictionary to store the data
    data = {}
    # Parse the XML file
    tree = ET.parse(file)
    # Get the root of the XML file
    root = tree.getroot()
    
    # Get the article-meta section
    article_meta = root.find('.//article-meta')
    # Get the title of the article
    title = None
    if article_meta is not None:
        title_group = article_meta.find('title-group')
        if title_group is not None:
            title = title_group.find('article-title').text if title_group.find('article-title') is not None else None
    
    # Get the abstract of the article, considering it may have multiple sections
    abstract = ""
    abstract_section = article_meta.find('abstract') if article_meta is not None else None
    if abstract_section is not None:
        for sec in abstract_section.findall('sec'):
            # Append each section's text to the abstract
            sec_text = ET.tostring(sec, encoding='unicode', method='text')
            abstract += sec_text + " "
    
    # Get the body of the article
    body = ""
    body_section = root.find('body')
    if body_section is not None:
        for sec in body_section.findall('sec'):
            # Convert each section to string and append to the body text
            body += ET.tostring(sec, encoding='unicode', method='text') + " "
    
    # Get the references of the article
    references = []
    references_section = root.find('.//ref-list')
    if references_section is not None:
        references = [ET.tostring(reference, encoding='unicode') for reference in references_section.findall('ref')]
    
    # Store the data into the dictionary
    data['title'] = title
    data['abstract'] = abstract.strip()  # Remove any leading/trailing whitespace
    data['body'] = body.strip()  # Remove any leading/trailing whitespace
    data['references'] = references
    
    # Return the dictionary
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


