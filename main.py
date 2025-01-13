import os
import json
import pdfplumber
import google.generativeai as genai
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef

# Configure API key for genai
myApiKey = "your_api_key_here"

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    extracted_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            extracted_text += page.extract_text() + "\n"
    return extracted_text

# Save data to corresponding JSON file
def save_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        if isinstance(data, dict):
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            f.write(data)

# Save data to corresponding TTL file
def save_to_ttl_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(data)

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

    """

    try:
        response = model.generate_content(prompt.format(document_text=text))
    except Exception as e:
        print("Error querying LLM:", e)
        return {}

    return response

# (TTL) Query LLM for structured data
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

    """

    try:
        response = model.generate_content(prompt.format(document_text=text))
    except Exception as e:
        print("Error querying LLM:", e)
        structured_data = {}

    return response

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

        # Log the raw response for debugging
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
        # Handle unexpected errors
        print(f"Unexpected error extracting JSON data: {e}")
        return {}
    
# Extract TTL data from the LLM response
def extract_ttl_from_response(response):
    try:
        # Initialize variable to store TTL data
        ttl_data = ""

        # Check for 'candidates' in response
        if hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            ttl_data += part.text

        # Clean Markdown syntax like ```ttl if present
        if ttl_data.startswith("```ttl") and ttl_data.endswith("```"):
            ttl_data = ttl_data[6:-3].strip()

        return ttl_data

    except Exception as e:
        print("Error extracting TTL data from response:", e)
        return ""

def process_pdfs_in_directory(directory, ontology):
    # Iterate through all files in the specified directory
    for filename in os.listdir(directory):
        # Check if the file is a PDF
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            
            # Extract text from the PDF
            print(f"Processing: {filename}")
            text = extract_text_from_pdf(pdf_path)
            
            # Query the LLM for JSON structured data
            structured_data_json = query_llm_for_json_structured_data(text, ontology)

            # Query the LLM for TTL structured data
            structured_data_ttl = query_llm_for_ttl_structured_data(text, ontology)

            # Extract JSON data from the response
            json_data = extract_json_from_response(structured_data_json)

            # Extract TTL data from the response
            ttl_data = extract_ttl_from_response(structured_data_ttl)

            # Save the JSON data to a file if it exists
            if json_data:
                # Generate a dynamic output filename based on the PDF name
                output_filename = f"{os.path.splitext(filename)[0]}.json"
                output_path = os.path.join(directory, output_filename)
                
                save_to_file(json_data, output_path)
                print(f"JSON data saved to {output_path}")
            else:
                print(f"No JSON data extracted for {filename}")

            # Save the TTL data to a file if it exists
            if ttl_data:
                # Generate a dynamic output filename based on the PDF name
                output_filename = f"{os.path.splitext(filename)[0]}.ttl"
                output_path = os.path.join(directory, output_filename)
                
                save_to_ttl_file(ttl_data, output_path)
                print(f"TTL data saved to {output_path}")
            else:
                print(f"No TTL data extracted for {filename}")

# Function to load an ontology and extract its classes and properties
def extract_ontology_schema(graph):
    ontology_schema = {
        "classes": [],
        "properties": []
    }

    # Extract classes
    for s, p, o in graph.triples((None, RDF.type, OWL.Class)):
        ontology_schema["classes"].append(str(s))

    # Extract Object Properties
    for s, p, o in graph.triples((None, RDF.type, OWL.ObjectProperty)):
        ontology_schema["properties"].append(str(s))

    # Extract Data Properties
    for s, p, o in graph.triples((None, RDF.type, OWL.DatatypeProperty)):
        ontology_schema["properties"].append(str(s))

    return ontology_schema

# Function to load an ontology from a URL or file
def load_ontology(file):
    graph = Graph()
    graph.parse(file, format='xml')
    return graph

# Function to process imports and extract classes and properties
def extract_schema_from_imports(graph):
    all_schema = extract_ontology_schema(graph)  # Extract from the main ontology

    # Process the imported ontologies
    for _, _, import_uri in graph.triples((None, OWL.imports, None)):
        import_uri = str(import_uri)
        print(f"Processing import: {import_uri}")
        try:
            imported_graph = load_ontology(import_uri)
            imported_schema = extract_ontology_schema(imported_graph)
            
            # Merge classes and properties from the imported ontology
            all_schema["classes"].extend(imported_schema["classes"])
            all_schema["properties"].extend(imported_schema["properties"])
        except Exception as e:
            print(f"Failed to load or parse {import_uri}: {str(e)}")

    return all_schema

# Main function
def main():
    # Load main ontology
    main_ontology = "d2kg.owl" 
    graph = load_ontology(main_ontology)

    # Extract schema (classes and properties) from the main ontology and its imports
    ontology_schema = extract_schema_from_imports(graph)

    # Start processing the pdf files
    process_pdfs_in_directory("path\\to\\pdf\\directory\\", ontology_schema)
    
# Entry point for the script
if __name__ == "__main__":
    main()
