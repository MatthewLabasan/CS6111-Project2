# Imports
import google.generativeai as genai
import time
import re

def extract_relations(sentences, relation_type, gemini_api_key, model_name="gemini-2.0-flash"):
    '''
    Extracts relations from sentences using Google Gemini API
    
    Args:
        sentences: List of sentences (spacy)
        relation_type: Integer representing relation type (1-4)
        gemini_api_key: API key for Gemini
        model_name: Model name to use (default: gemini-2.0-flash)
    
    Returns:
        Dictionary of extracted relations
    '''

    genai.configure(api_key = gemini_api_key)
    model = genai.GenerativeModel(model_name)

    relation_names = {
        1: "Schools_Attended",
        2: "Work_For",
        3: "Live_In", 
        4: "Top_Member_Employees"
    }

    relation_name = relation_names[relation_type]
    extracted_relations = {}

    for sentence in sentences:
        time.sleep(5)
        try:
            prompt = f"""Extract '{relation_name}' relations from the following sentence. 
            Sentence: "{sentence.text}"

            For the relation '{relation_name}':
            - If relation type is Schools_Attended: Extract all (PERSON, ORGANIZATION) pairs where the PERSON attended the ORGANIZATION as a school.
            - If relation type is Work_For: Extract all (PERSON, ORGANIZATION) pairs where the PERSON works for the ORGANIZATION.
            - If relation type is Live_In: Extract all (PERSON, LOCATION) pairs where the PERSON lives in the LOCATION.
            - If relation type is Top_Member_Employees: Extract all (ORGANIZATION, PERSON) pairs where the PERSON is a top member or employee of the ORGANIZATION.

            Provide the output in JSON format like this:
            {{
            "relations": [
                {{"subject": "subject_name", "object": "object_name"}}
            ]
            }}

            If no relations are found, return an empty list: {{"relations": []}}
            
            Please ignore common nouns such as (he, she, city, company, etc.) when extracting
            Only consider proper nouns such as Charles, Google, San Francisco, etc.
            please make sure to return just the JSON with no additional comment or text
            """
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            import json
            try:
                data = json.loads(response_text)  
            except json.JSONDecodeError as e:
                json_str = extract_json_from_text(response_text)
                if json_str:
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        print(f"\t\tError parsing extracted JSON: {e}")
                        print(f"\t\tExtracted JSON: {json_str}")
                        continue
                else:
                    print(f"\t\tCould not find valid JSON in response")
                    print(f"\t\tResponse text: {response_text}")
                    continue
            
            for relation in data.get("relations", []):
                subject = relation.get("subject")
                obj = relation.get("object")
                
                if subject and obj:
                    relation_tuple = (subject, relation_name, obj)
                    extracted_relations[relation_tuple] = 1.0
        except Exception as e:
            print(f"\t\tError calling Gemini API: {e}")
            if "429" in str(e) or "500" in str(e):
                print("\t\tHit rate limit or server error, waiting 10 seconds...")
                time.sleep(10)
    
    return extracted_relations

def extract_json_from_text(text):
    """
    Extracts JSON data from text that might contain explanations and other content.
    """
    # JSON patterns between triple backticks
    json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(json_pattern, text, re.DOTALL)
    
    if match:
        return match.group(1)
    
    return None


def filter_sentences_by_entity_types(sentences, relation_type):
    """
    Filters sentences to include only those with the required entity types for the relation
    
    Parameters:
    - sentences: spaCy sentences
    - relation_type: Integer representing relation type (1-4)
    
    Returns:
    - List of eligible sentences
    """
    eligible_sentences = []
    
    required_entities = {
        1: {"PERSON", "ORG"},
        2: {"PERSON", "ORG"},
        3: {"PERSON", "GPE", "LOC"},
        4: {"ORG", "PERSON"}
    }
    
    for sentence in sentences:
        entity_types = set()
        for ent in sentence.ents:
            entity_types.add(ent.label_)
        
        if relation_type == 3: # lives in
            if "PERSON" in entity_types and ("GPE" in entity_types or "LOC" in entity_types):
                eligible_sentences.append(sentence)
        else:
            entities = required_entities[relation_type]
            for entity in entities:
                if entity not in entity_types:
                    continue

            eligible_sentences.append(sentence)
    
    return eligible_sentences