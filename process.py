import streamlit as st
import google.generativeai as genai
from PIL import Image, UnidentifiedImageError
import pytesseract
import pdfplumber
import io
import os
import json
import re
from database import get_all_documents, download_file_from_supabase

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Fixed closing parenthesis issue

# Initialize the Gemini model
GEMINI_MODEL = genai.GenerativeModel("gemini-1.5-pro")


def extract_text_from_file(file_path, file_extension):
    """Extracts text from images (PNG/JPEG), PDFs, or text files."""

    file_extension = file_extension.lower()

    try:
        if file_extension in ["png", "jpg", "jpeg"]:  # Process Image Files
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)  # OCR for text extraction
            return extracted_text.strip()

        elif file_extension == "pdf":  # Process PDFs
            extracted_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() + "\n"
            return extracted_text.strip()

        elif file_extension in ["txt", "csv"]:  # Process Plain Text Files
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip()

        else:
            return "Unsupported file type: " + file_extension

    except UnidentifiedImageError:
        return f"Error: Cannot identify image file {file_path}"
    except Exception as e:
        return f"Error processing {file_path}: {str(e)}"


def analyze_text(text):
    """Analyzes extracted text using Gemini AI and ensures JSON output."""

    model = genai.GenerativeModel("gemini-1.5-pro")

    # Modify the prompt to explicitly request a structured JSON response
    prompt = f"""
    Extract personal details (name, address, DOB, phone number, etc.) from the text.
    Ensure the response is a valid JSON object with the following keys: 
    - name
    - address
    - dob
    - phone_number

    Text: 
    {text}

    Example JSON output:
    {{
        "name": "John Doe",
        "address": "123 Main St, City, Country",
        "dob": "1990-01-01",
        "phone_number": "+1234567890"
    }}

    Important: 
    - Do not include any explanations.
    - Do not wrap the JSON in triple backticks or markdown.
    - Ensure the response is **valid JSON only**.
    """

    response = model.generate_content(prompt)

    # Ensure the response is a string
    raw_output = response.text if response else ""

    # Remove triple backticks and markdown artifacts
    cleaned_output = re.sub(r"```json\n|\n```", "", raw_output).strip()

    try:
        # Parse JSON
        extracted_data = json.loads(cleaned_output)
    except json.JSONDecodeError:
        extracted_data = {"error": "Invalid JSON response from Gemini", "raw_output": raw_output}

    return extracted_data
def process_documents():
    st.title("Process Documents with AI")

    if st.session_state.get("user_logged_in", False):
        user = st.session_state.get("username", "Guest")

        # Fetch user's documents from Supabase
        user_docs = [doc for doc in get_all_documents() if doc["user"] == user]

        if user_docs:
            st.write("Select documents for processing:")
            selected_docs = st.multiselect("Choose documents", [doc["filename"] for doc in user_docs])

            if selected_docs and st.button("Extract Info"):
                extracted_texts = []

                for doc in user_docs:
                    if doc["filename"] in selected_docs:
                        file_data = download_file_from_supabase(doc["document_id"])  # Fetch file
                        file_path = io.BytesIO(file_data)

                        extracted_text = extract_text_from_file(file_path, doc["filename"].split(".")[-1])
                        extracted_texts.append(extracted_text)

                combined_text = "\n".join(extracted_texts)
                response = analyze_text(combined_text)  # Call Gemini API

                st.write("### Extracted Information:")
                st.json(response)

        else:
            st.write("No documents found.")

    else:
        st.warning("Please sign in to process documents.")
