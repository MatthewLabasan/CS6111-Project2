import sys
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import spacy
from spacy_help_functions import extract_relations, get_entities, create_entity_pairs
from spanbert import SpanBERT 
from itertools import permutations
import re
from collections import defaultdict

def search(GSAPI, GSEID, query) -> dict:
  """
  Call Google API.
  Source: https://github.com/googleapis/google-api-python-client/blob/main/samples/customsearch/main.py
  
  Args:
      GSAPI (str): Google Search API Key
      GSEID (str): Google Search Engine ID
      query (str): Desired query

  Returns:
      res (dict): Dictionary of 10 results
  """
  
  service = build(
        "customsearch", "v1", developerKey=GSAPI
    )
  
  try:
    res = (
        service.cse()
        .list(
            q=query,
            cx=GSEID,
        )
        .execute()
    )
  except Exception as e:
        print("Error fetching search results:")
        print(e)
        return []
  
  return res

def add_urls(results, urls):
  """
  Takes URL's from Google search() results and adds it to a dictionary.
  
  Args:
      results (dict): Google Search results
      urls (dict): URL dictionary in form {"actual_url": Boolean (processed or not)}
  """
  for result in results:
    if result["link"] not in urls:
      urls[result["link"]] = False

def main():
  # Get arguments
  try:
    EXTRACTION_METHOD = sys.argv[1]
    GSAPI = sys.argv[2]
    GSEID = sys.argv[3] 
    GEMINI_API = sys.argv[4]
    r = int(sys.argv[5]) # Relation to extract (1 to 4)
    t = float(sys.argv[6]) # Extraction confidence threshold (between 0 - 1)
    q = sys.argv[7] # Seed query
    k = int(sys.argv[8]) # Number of tuples to return (greater than 0)

    if EXTRACTION_METHOD not in ["-spanbert", "-gemini"]:
        raise ValueError("Invalid extraction method. Use '-spanbert' or '-gemini'.")
    if not (0 <= t <= 1):
        raise ValueError("Threshold (t) must be a float between 0 and 1.")
    if k <= 0:
        raise ValueError("Number of tuples (k) must be greater than 0.")
    if r not in [1, 2, 3, 4]:
        raise ValueError("Relation (r) must be one of: 1 (Schools_Attended), 2 (Work_For), 3 (Live_In), 4 (Top_Member_Employees).")
  except (IndexError, ValueError) as e:
    print(f"Error: {e}")
    print("Usage: python3 project2.py [-spanbert|-gemini] <google api key> <google engine id> <google gemini api key> <r> <t> <q> <k>\n")
    sys.exit(1)
  except Exception as e:
    print("Usage: python3 project2.py [-spanbert|-gemini] <google api key> <google engine id> <google gemini api key> <r> <t> <q> <k>\n")
    sys.exit(1)
  
  X = set() # Set of sorted relations. SpanBERT Form: {((subj, relation, obj), confidence)}
  extracted_tuples = defaultdict(lambda: -1) # Unsorted relations. For SpanBERT use. Form: {(subj, relation, obj): confidence}
  iteration_count = 0
  urls = dict()
  current_query = q
  previous_queries = [q]

  # For SpanBERT
  relation_types = {
    1: ("PERSON", "ORGANIZATION"),
    2: ("PERSON", "ORGANIZATION"),
    3: ("PERSON", "LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"),
    4: ("ORGANIZATION", "PERSON") 
  }
  internal_relation_names = {
    1: "per:schools_attended",
    2: "per:employee_of",
    3: "per:cities_of_residence",
    4: "org:top_members/employees"
  }
  entities_of_interest = relation_types[r]
  relation_of_interest = internal_relation_names[r]

  # Print Google Search
  print(f"""Parameters:
  {'Client key:':<12} = {GSAPI}
  {'Engine key:':<12} = {GSEID}
  {'Gemini key:':<12} = {GEMINI_API}
  {'Mehod:':<12} = {EXTRACTION_METHOD}
  {'Relation:':<12} = {r}
  {'Threshold:':<12} = {t}
  {'Query:':<12} = {q}
  {'# of Tuples:':<12} = {k}
  Loading necessary libraries; This should take a minute or so ...
  """)

  # Iteration Loop
  while len(X) < k:
    # Get URLs from Google Search
    results = search(GSAPI, GSEID, current_query)['items']
    if results == None:
       print("Error: No results using given query.")
       sys.exit(0)
    add_urls(results, urls)

    # Begin Extraction
    print(f"=========== Iteration: {iteration_count + 1} - Query: {current_query} ===========")
    for index, url in enumerate(urls):
      if urls[url] == False:
        print(f"URL ( {index + 1} / {len(urls)}): {url}")
      
        # Get Website Text
        print("\tFetching text from url ...")
        try:
          response = requests.get(url, timeout=10)
          soup = BeautifulSoup(response.text, 'html.parser')
          raw_text = soup.get_text()

          # Remove extra chars and spaces
          raw_text = raw_text.strip()
          raw_text = re.sub(r'\s+', ' ', raw_text)
          raw_text = raw_text.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ').replace('\xa0', ' ')

          # Trim
          if len(raw_text) > 10000:
            print(f"\tTrimming webpage content from {len(raw_text)} to 10000 characters")
            raw_text = raw_text[0:10000]
          print(f"\tWebpage length (num characters): {len(raw_text)}")

        except Exception as e: # Bad request, timeout, etc.
          print(f"Retrieval Error for {url[0:25]}... : {e}")
          continue
        
        # Apply spacy model to raw text (to split to sentences, tokenize, extract entities etc.)
        try:
          print("\tAnnotating the webpage using spacy...")
          nlp = spacy.load("en_core_web_lg")  
          doc = nlp(raw_text)  
        except Exception as e: 
          print(f"Spacy Error for {url[0:25]}... : {e}")
        
        if EXTRACTION_METHOD == "-spanbert":
          # Load pre-trained SpanBERT model & Extract
          spanbert = SpanBERT("./pretrained_spanbert")  
          res = extract_relations(doc, spanbert, relation_of_interest, entities_of_interest, t)
          
          # Add to extracted dict. Result in form {(subj, relation, obj): confidence}
          for result in res:
            if res[result] > extracted_tuples[result]:
              extracted_tuples[result] = res[result] # Keep higher confidence, or add if not seen before.

          # Add to sorted list
          result = set(extracted_tuples.items())
          X = (sorted(result, key=lambda x: x[1], reverse=True))
          
        if EXTRACTION_METHOD == "-gemini":
          # TODO
          sentences = doc.sents
  
    # Get new query
    if len(X) < k:
      if EXTRACTION_METHOD == "-spanbert":
        for relation in X:
          new_q = f"{relation[0][0]} {relation[0][2]}"
          if new_q not in previous_queries:
            previous_queries.add(new_q)
            break
        # No new query extracted
        print('ISE has "stalled" before retrieving k high-confidence tuples.')
        break

      if EXTRACTION_METHOD == "-gemini":
          # TODO
          break
  
  # Return top-k Tuples
  if EXTRACTION_METHOD == "-spanbert":
    print(f"\n================== ALL RELATIONS for {relation_of_interest} ( {len(res)} ) =================")
    for relation in X:
      print(f"Confidence: {relation[1]:.8f} \t| Subject: {relation[0][0]} \t| Object: {relation[0][2]}")

  if EXTRACTION_METHOD == "-gemini":
    # TODO
    exit()

if __name__ == "__main__":
  main()