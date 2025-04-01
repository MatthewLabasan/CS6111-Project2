# CS6111-Project2
# Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
    - [Prerequisites](#prerequisits)
    - [Installation](#installation)
3. [Usage](#usage)
4. [Description of Project](#description-of-project)
    - [Internal Design](#internal-design)
        - [Notable External Libraries Used](#notable-external-libraries-used)

# Introduction
This project focuses on information extraction from web sources using two different approaches: a traditional multi-step pipeline with SpanBERT and a modern LLM-based method using Google Gemini. Our goal is to extract structured data from unstructured web text by iteratively expanding a seed query and retrieving relevant tuples.

By implementing the Iterative Set Expansion (ISE) algorithm, we:
- Retrieved and parsed web pages using Google Custom Search and Beautiful Soup.
- Preprocessed and annotated text with spaCy for named entity recognition.
- Extracted relations using either SpanBERT (fine-tuned for specific relations) or Google Gemini (a modern LLM-based approach).

This project reinforced our understanding of information extraction, specifically with the ISE algorithm, and gave us experience in implementing such algorithms with LLM's. This project was built for Project 2 of COMS6111 - Advanced Database Systems.

Developed by Matthew Labasan and Phoebe Tang.

# Getting Started
## Prerequisites
1. Python 3.10.1 or above
2. Install `wget` using `brew install wget`
    - Make sure to restart your terminal after this installation.
3. Google Custom Search Engine API Key
4. Google Search Engine Key
5. Google Gemini 2.0 Flash model (free tier) API Key

## Installation
1. Clone the repository  
  `git clone https://github.com/MatthewLabasan/CS6111-Project2.git`  
2. Move into the respository  
  `cd ./CS6111-Project2`  
3. Create a virtual environment and activate it  
    - `python3 -m venv dbproj`  
    - `source dbproj/bin/activate`  
4. Install requirements.txt
5. Install trained SpanBERT
  The SpanBERT classifier will be used to extract the following four types of relations from text documents:
    - Schools_Attended (internal name: per:schools_attended)
    - Work_For (internal name: per:employee_of)
    - Live_In (internal name: per:cities_of_residence)
    - Top_Member_Employees (internal name: org:top_members/employees)
  Run the following code to install it:  
    - `git clone https://github.com/Shreyas200188/SpanBERT`  
    - `cd SpanBERT`  
    - `pip3 install -r requirements.txt`  
    - `bash download_finetuned.sh`  
6. Remove this file from the SpanBERT repository  
  `rm spacy_help_functions.py`
7. Move these files in `/CS6111-Project2` into `/SpanBERT`  
    - `cd ..`  
    - `mv gemini_helper_6111.py ./SpanBERT`  
    - `mv project2.py ./SpanBERT`  
    - `mv spacy_help_functions.py ./SpanBERT`  
    - `cd SpanBERT`  

__Note__: For specific instructions on installation on a Google VM instance, view the [course website](https://www.cs.columbia.edu/~gravano/cs6111/Proj2/).

# Usage
1. Run & replace with your parameters, using a query in quotations: 
 `python3 project2.py [-spanbert|-gemini] <google api key> <google engine id> <google gemini api key> <r> <t> <q> <k>`
  - [-spanbert|-gemini] is either -spanbert or -gemini, to indicate which relation extraction method we are requesting>
  - <google api key> is your Google Custom Search Engine JSON API Key (see above)
  - <google engine id> is your Google Custom Search Engine ID (see above)
  - <google gemini api key> is your Google Gemini API key (see above)
  - <r> is an integer between 1 and 4, indicating the relation to extract: 1 is for Schools_Attended, 2 is for Work_For, 3 is for Live_In, and 4 is for Top_Member_Employees
  - <t> is a real number between 0 and 1, indicating the "extraction confidence threshold," which is the minimum extraction confidence that we request for the tuples in the output; t is ignored if we are specifying -gemini
  - <q> is a "seed query," which is a list of words in double quotes corresponding to a plausible tuple for the relation to extract (e.g., "bill gates microsoft" for relation Work_For)
  - <k> is an integer greater than 0, indicating the number of tuples that we request in the output
  - Example usage: python3 project2.py -gemini <google api key> <google engine id> <google gemini api key> 1 0.8 “Obama Columbia” 10

# Description of Project
## Internal Design
For a description of the internal design and SpanBERT / Gemini extraction methods, please see p.4-8 of our report [here](./transcripts/Project2_Report.pdf).
For sample transcrips and usage, please see our result transcripts for each LLM [here](./transcripts).

### Notable External Libraries Used
1. `googleapiclient`: For Google Search
2. `google.generativeai`: For using Google Gemini to extract relations
3. `time`: For spacing out timeouts to avoid rate limitation
4. `requests`: To fetch websites from URLs 
5. `BeautifulSoup`: For processing raw text from webpage to ignore HTML tags, images, and other content that would interfere with information extraction process
6. `re`: For using regular expressions to parse returned text
7. `spacy`: process and annotate text through linguistic analysis
8. `spanbert`: For extracting relations using bert
9. `spacy_help_functions`: Started functions via [SpanBERT](https://github.com/Shreyas200188/SpanBERT) repository. Modified for our project.