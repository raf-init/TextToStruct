# TextToStruct
A Python-based project that leverages prompt engineering with Gemini to extract structured data from unstructured PDF files using a defined schema and convert it into certain formats for semantic interoperability and advanced data analysis.

![Python](https://img.shields.io/badge/python-3.x-blue)
![Contributions](https://img.shields.io/badge/contributions-welcome-brightgreen)

## Features
- Extract text from unstructured PDF files.
- Leverage Gemini AI for ontology-based prompt engineering.
- Convert structured data to JSON/TTL format for semantic analysis.
- Fully customizable and extensible with other ontologies.

---

## Getting Started

### Prerequisites
- Python 3.x
- Install dependencies:
  `pip install pdfplumber`
  `pip install google-generativeai`
  `pip install rdflib`

### Running the Project
1. Clone this repository:
   ```bash
   git clone https://github.com/raf-init/TextToStruct.git
2. Navigate to the project directory:
   ```bash
   cd TextToStruct
3. Run the main script:
   ```
   python main.py
---

## Tech Stack
- Python 3.x
- RDFLib for ontology parsing
- pdfplumber for PDF text extraction
- GenAI for AI-driven prompt engineering

## Folder Structure Example
```
project/
│
├── d2kg.owl              # Your ontology file
├── main.py               # Main script to run
├── file1.pdf             # First .pdf to process
├── file2.pdf             # Second .pdf to process
├── file1.tll             # First .ttl output
├── file2.ttl             # Second .ttl output
├── file1.json            # First .json output
├── file2.json            # Second .json output
```

## Roadmap
- [x] Add support for other file formats (e.g., JSON, CSV).
- [x] Use also the imported ontologies and not only the main ontology.
- [ ] Add a web interface for easier user interaction.
