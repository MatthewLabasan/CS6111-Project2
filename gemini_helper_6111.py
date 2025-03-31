# Imports
import google.generativeai as genai
import time

# Apply Gemini API Key
GEMINI_API_KEY = ''  # Substitute your own key here
genai.configure(api_key=GEMINI_API_KEY)

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
        time.sleep(3)
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
            """
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            import json
            try:
                data = json.loads(response_text)
                for relation in data.get("relations", []):
                    subject = relation.get("subject")
                    obj = relation.get("object")
                    
                    if subject and obj:
                        relation_tuple = (subject, relation_name, obj)
                        extracted_relations[relation_tuple] = 1.0
                        
            except json.JSONDecodeError as e:
                print(f"\t\tError parsing Gemini response as JSON: {e}")
                print(f"\t\tResponse text: {response_text}")
                
        except Exception as e:
            print(f"\t\tError calling Gemini API: {e}")
            if "429" in str(e) or "500" in str(e):
                print("\t\tHit rate limit or server error, waiting 10 seconds...")
                time.sleep(10)
    
    return extracted_relations

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
