# Imports
import google.generativeai as genai
import time
import re

# Apply Gemini API Key

def extract_relations(sentences, relation_type, gemini_api_key, model_name="gemini-2.0-flash"):
    '''
    Extracts relations from sentences using Google Gemini API
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
<<<<<<< HEAD
'''
# Generate response to prompt
def get_gemini_completion(prompt, model_name="gemini-2.0-flash", max_tokens=200, temperature=0.2, top_p=1, top_k=32):
    # Initialize a generative model
    model = genai.GenerativeModel(model_name)

    # Configure the model with your desired parameters
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k
    )

    # Generate a response
    response = model.generate_content(prompt, generation_config=generation_config)

    return response.text.strip() if response.text else "No response received"

def main():
    # Sample Prompt
    prompt_text = """Given a sentence, extract all the Nouns.
sentence: Rob is an engineer at NASA and he lives in California.
extracted:"""

    # Feel free to modify the parameters below.
    # Documentation: https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini
    model_name = "gemini-2.0-flash"
    max_tokens = 100
    temperature = 0.2
    top_p = 1
    top_k = 32

    response_text = get_gemini_completion(prompt_text, model_name, max_tokens, temperature, top_p, top_k)
    print(response_text)

main()
'''
=======

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
>>>>>>> 9930d66604d629a37b9dc5628621caf1b1264bec
