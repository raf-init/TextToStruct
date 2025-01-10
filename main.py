import os
import json
import pdfplumber
import google.generativeai as genai
from rdflib import Graph, Namespace, RDF, RDFS, OWL

# Configure API key for genai
myApiKey = "your_api_key_here"

# Load and parse OWL Ontology
def load_ontology(ontology_file):
    g = Graph()
    g.parse(ontology_file, format="xml")

    ontology_schema = {
        "classes": [],
        "properties": []
    }

    for s, p, o in g.triples((None, RDF.type, OWL.Class)):
        ontology_schema["classes"].append(str(s))

    for s, p, o in g.triples((None, RDF.type, OWL.ObjectProperty)):
        ontology_schema["properties"].append(str(s))

    return ontology_schema

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    extracted_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            extracted_text += page.extract_text() + "\n"
    return extracted_text

# Query LLM for structured data
def query_llm_for_ttl_structured_data(text, ontology):
    genai.configure(api_key=myApiKey)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Construct a prompt with instructions
    prompt = f"""
    Based on the following ontology schema, extract structured data from the provided text and format the output in Turtle (TTL) format.

    Ontology classes: {ontology['classes']}
    Ontology properties: {ontology['properties']}

    Text:
    {text}

    Provide the output in Turtle format:
    """

    try:
        response = model.generate_content(prompt.format(document_text=text))
    except Exception as e:
        print("Error querying LLM:", e)
        structured_data = {}

    return response

# (JSON) Query LLM for structured data
def query_llm_for_json_structured_data(text, ontology):
    genai.configure(api_key=myApiKey)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Construct a prompt with instructions
    prompt = f"""
    Based on the following ontology schema, extract structured data from the provided text and format the output in JSON format.

    Ontology classes: {ontology['classes']}
    Ontology properties: {ontology['properties']}

    Text:
    {text}

    Provide the output in JSON format:
    """

    try:
        response = model.generate_content(prompt.format(document_text=text))
    except Exception as e:
        print("Error querying LLM:", e)
        return {}

    return response
    
# Extract Turtle data from the LLM response
def extract_turtle_from_response(response):
    try:
        # Initialize variable to store Turtle data
        turtle_data = ""

        # Check for 'candidates' in response
        if hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            turtle_data += part.text

        # Clean Markdown syntax like ```ttl if present
        if turtle_data.startswith("```ttl") and turtle_data.endswith("```"):
            turtle_data = turtle_data[6:-3].strip()

        return turtle_data

    except Exception as e:
        print("Error extracting Turtle data from response:", e)
        return ""
        
# Extract JSON data from the LLM response
def extract_json_from_response(response):
    try:
        # Initialize variable to store JSON data
        json_data = ""

        # Check if the response contains candidates
        if hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            json_data += part.text  # Collect text content

        # Log the raw response for debugging if empty
        if not json_data.strip():
            print("Debug: Response is empty or missing expected content.")
            return {}

        print("Debug: Raw response content:", json_data)

        # Remove Markdown syntax like ```json if present
        if json_data.startswith("```json") and json_data.endswith("```"):
            json_data = json_data[7:-3].strip()

        # Clean up any stray characters or whitespace outside JSON
        json_data = json_data.strip()

        # Attempt to parse JSON
        try:
            parsed_data = json.loads(json_data)
            print("Debug: Parsed JSON successfully.")
            return parsed_data
        except json.JSONDecodeError as inner_error:
            # Log error and debug further
            print(f"Error during JSON decoding: {inner_error}")
            print("Debug: Attempting to locate valid JSON...")
            
            # Attempt to extract valid JSON using regex
            import re
            match = re.search(r"{.*}", json_data, re.DOTALL)
            if match:
                valid_json = match.group(0)
                return json.loads(valid_json)
            else:
                print("Debug: Could not find valid JSON structure.")
                return {}

    except Exception as e:
        # Handle unexpected errors gracefully
        print(f"Unexpected error extracting JSON data: {e}")
        return {}
        
# Save data to corresponding file
def save_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(data)

# Save data to corresponding file
def save_to_json_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        if isinstance(data, dict):
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            f.write(data)

# TTL process of PDF file
def process_pdfs_in_directory(directory, ontology):
    # Iterate through all files in the specified directory
    for filename in os.listdir(directory):
        # Check if the file is a PDF
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            
            # Extract text from the PDF
            print(f"Processing: {filename}")
            text = extract_text_from_pdf(pdf_path)
            
            # Query the LLM for structured data
            structured_data = query_llm_for_structured_data(text, ontology)
            
            # Extract Turtle data from the response
            turtle_data = extract_turtle_from_response(structured_data)
            
            # Save the Turtle data to a file if it exists
            if turtle_data:
                # Generate a dynamic output filename based on the PDF name
                output_filename = f"{os.path.splitext(filename)[0]}.ttl"
                output_path = os.path.join(directory, output_filename)
                
                save_to_file(turtle_data, output_path)
                print(f"Turtle data saved to {output_path}")
            else:
                print(f"No Turtle data extracted for {filename}")

# JSON process of PDF file
def json_process_pdfs_in_directory(directory, ontology):
    # Iterate through all files in the specified directory
    for filename in os.listdir(directory):
        # Check if the file is a PDF
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            
            # Extract text from the PDF
            print(f"Processing: {filename}")
            text = extract_text_from_pdf(pdf_path)
            
            # Query the LLM for structured data
            structured_data = query_llm_for_json_structured_data(text, ontology)
            
            # Extract Turtle data from the response
            json_data = extract_json_from_response(structured_data)
            
            # Save the Turtle data to a file if it exists
            if json_data:
                # Generate a dynamic output filename based on the PDF name
                output_filename = f"{os.path.splitext(filename)[0]}.json"
                output_path = os.path.join(directory, output_filename)
                
                save_to_json_file(json_data, output_path)
                print(f"JSON data saved to {output_path}")
            else:
                print(f"No JSON data extracted for {filename}")
                
# Main function
def main():
    ontology_file = "d2kg.owl"  # Path to the ontology file
    pdf_directory = "path_to_your_pdf_directory"  # Path to the directory containing PDFs

    # Load ontology
    ontology = load_ontology(ontology_file)
    print("Ontology loaded successfully.")

    # Process PDFs in the specified directory
    process_pdfs_in_directory(pdf_directory, ontology)
    json_process_pdfs_in_directory(pdf_directory, ontology)
    
# Entry point for the script
if __name__ == "__main__":
    main()
