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
from gemini_helper_6111 import extract_relations, filter_sentences_by_entity_types

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

def main():
  """
  Main Extraction Method
  Args:
      1. Extraction Method (str): SpanBERT or Gemini
      2. GSAPI (str): Google Search API Key
      3. GSEID (str): Google Search Engine ID
      4. GEMINI API (str): Google Gemini API
      5. r (int): extraction relation
      6. t (float): confidence threshold (0-1)
      7. q (str): seed query
      8. k (int): number of tuples
  """
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
  extracted_tuples = defaultdict(lambda: -1) # Unsorted relations. Form: {(subj, relation, obj): confidence}
  iteration_count = 0
  previous_urls = set()
  current_query = q
  previous_queries = {q.lower()} # Standardize with lowercase

  # For SpanBERT
  if EXTRACTION_METHOD == "-spanbert":
    # Load pre-trained SpanBERT model & Extract
    spanbert = SpanBERT("./pretrained_spanbert")  
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
  readable_relation_names = {
    1: "Schools_Attended",
    2: "Work_For",
    3: "Live_In",
    4: "Top_Member_Employees"
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
  while len(X) <= k:
    # Get URLs from Google Search
    urls = []
    results = search(GSAPI, GSEID, current_query)['items']
    if results == None:
       print("Error: No results using given query.")
       sys.exit(0)
    for result in results:
      urls.append(result["link"])

    # Begin Extraction
    print(f"=========== Iteration: {iteration_count} - Query: {current_query} ===========")
    iteration_count += 1
    for index, url in enumerate(urls):
      if url not in previous_urls:
        print(f"URL ( {index + 1} / {len(urls)}): {url}")
        # Mark as processed
        previous_urls.add(url)

        # Get Website Text
        print("\tFetching text from url ...")
        try:
          response = requests.get(url, timeout=10)
          soup = BeautifulSoup(response.text, 'html.parser')
          raw_text = soup.get_text()

          # Remove extra chars and spaces
          raw_text = raw_text.strip()
          raw_text = re.sub(r'\s+', ' ', raw_text)
          # raw_text = raw_text.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ').replace('\xa0', ' ')
          raw_text = raw_text.replace('\n', ' ').replace('\xa0', ' ')

          # Trim
          if len(raw_text) > 10000:
            print(f"\tTrimming webpage content from {len(raw_text)} to 10000 characters")
            raw_text = raw_text[0:10000]
          print(f"\tWebpage length (num characters): {len(raw_text)}")

        except Exception as e: # Bad request, timeout, etc.
          print(f"Retrieval Error for {url[0:25]}... : {e}")
          print("skipping url...")
          continue
        
        # Apply spacy model to raw text (to split to sentences, tokenize, extract entities etc.)
        try:
          print("\tAnnotating the webpage using spacy...")
          nlp = spacy.load("en_core_web_lg")  
          doc = nlp(raw_text)  
        except Exception as e: 
          print(f"Spacy Error for {url[0:25]}... : {e}")
        
        if EXTRACTION_METHOD == "-spanbert":
          res = extract_relations(doc, spanbert, relation_of_interest, entities_of_interest, t)
          
          # Add to extracted dict. Result in form {(subj, relation, obj): confidence}
          for result in res:
            if res[result] > extracted_tuples[result]:
              extracted_tuples[result] = res[result] # Keep higher confidence, or add if not seen before.

          # Add to sorted list
          result = set(extracted_tuples.items())
          X = (sorted(result, key=lambda x: x[1], reverse=True))
          
        elif EXTRACTION_METHOD == "-gemini":
          '''
           if -gemini is specified, identify all the tuples that have been extracted and add 
           them to set X (we do not receive extraction confidence values from the Google Gemini API,
             so feel free to hard-code in a value of 1.0 for the confidence value for all 
             Gemini-extracted tuples).

              If -gemini is specified, your output can have the tuples in any order (if you have more 
              than k tuples, then you can return an arbitrary subset of k tuples). (Alternatively, 
              you can return all of the tuples in X, not just the top-k such tuples; 
              this is what the reference implementation does.)

              Otherwise, select from X a tuple y such that (1) y has not been used for querying yet 
              and (2) if -spanbert is specified, y has an extraction confidence that is highest among
                the tuples in X that have not yet been used for querying. (You can break ties
                arbitrarily.) Create a query q from tuple y by just concatenating the attribute values
                  together, and go to Step 2. If no such y tuple exists, then stop. (ISE has 
                  "stalled" before retrieving k high-confidence tuples.)

          '''

          print("\tExtracting relations using Google Gemini...")
          sentences = doc.sents
          eligible_sentences = filter_sentences_by_entity_types(sentences, r)
          if eligible_sentences:
            gemini_results = extract_relations(eligible_sentences, r, GEMINI_API)
            for result in gemini_results:
              extracted_tuples[result] = 1

            result = set(extracted_tuples.items())
            print(f"\tFound {len(gemini_results)} relations in this webpage")
            X.update(result)
            print(f"Overall size of entities: {len(X)}")
          else:
             print(f"No sentences with required entity types found for relation type {r}")

      else:
        print(f"URL ( {index} / {len(urls)}): {url}")
        print(f"\t Already seen. Skipping...")

    # Get new query
    if len(X) < k:
      if EXTRACTION_METHOD == "-spanbert":
        found_new = False
        for relation in X: 
          new_q = f"{relation[0][0]} {relation[0][2]}"
          if new_q.lower() not in previous_queries:
            current_query = new_q 
            previous_queries.add(new_q.lower())
            found_new = True
            break
        if not found_new:
           print('ISE has "stalled" before retrieving k high-confidence tuples.')
           break

      if EXTRACTION_METHOD == "-gemini":
          found_new = False
          for relation in X:
            new_q = f"{relation[0][0]} {relation[0][2]}"
            if new_q.lower() not in previous_queries:
                current_query = new_q
                previous_queries.append(new_q)
                found_new = True
                break
          if not found_new:
                  print('ISE has "stalled" before retrieving k high-confidence tuples.')
                  break
          
  # Return top-k Tuples
  if EXTRACTION_METHOD == "-spanbert":
    print(f"\n================== TOP-{k} SPANBERT RELATIONS for {relation_of_interest} ( Total Found: {len(X)} ) =================")
    for i, relation in enumerate(X[:k]):
      print(f"Confidence: {relation[1]:.8f} \t\t\t| Subject: {relation[0][0]} \t\t\t| Object: {relation[0][2]}")

  if EXTRACTION_METHOD == "-gemini":
    print(f"\n================== TOP-{k} GEMINI RELATIONS for {relation_of_interest} ( Total Found: {len(X)} ) =================")
    result_count = min(len(X), k)
    print(f"Returning top {result_count} relations:")
        
    for i in range(result_count):
        relation = X[i]
        print(f"Confidence: {relation[1]:.1f} \t\t| Subject: {relation[0][0]} \t\t| Object: {relation[0][2]}")

  print(f"Total # of iterations = {iteration_count}")

if __name__ == "__main__":
  main()
