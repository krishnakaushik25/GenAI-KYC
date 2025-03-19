import pytesseract
from PIL import Image
import pandas as pd
import tempfile
import json
import streamlit as st
from database import supabase_client
from dotenv import load_dotenv
import os
import requests
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Document, Settings, SimpleDirectoryReader, VectorStoreIndex


# Configure Gemini API
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = Gemini(api_key=GEMINI_API_KEY)
embed_model = GeminiEmbedding(api_key=GEMINI_API_KEY)
Settings.embed_model = embed_model

pytesseract.pytesseract.tesseract_cmd="C:\Program Files\Tesseract-OCR\\tesseract.exe"

def download_file(file_url):
    """Downloads a file from a Supabase storage URL and saves it locally."""
    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False)  # Create a temporary file
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name  # Return local path of the downloaded file
    else:
        raise Exception(f"Failed to download file: {file_url}")

def extract_text_from_image(file_url):
    """Downloads an image from Supabase and extracts text using OCR."""
    local_file_path = download_file(file_url)
    image = Image.open(local_file_path)
    text = pytesseract.image_to_string(image)
    return text.strip()

def extract_data_from_pdf(file_url):
    """Downloads a PDF from Supabase and extracts structured text using LlamaIndex."""
    local_file_path = download_file(file_url)
    documents = SimpleDirectoryReader(input_files=[local_file_path]).load_data()
    index = VectorStoreIndex.from_documents(documents, llm=llm, embed_model=embed_model)

    query_engine = index.as_query_engine(llm=llm)
    response = query_engine.query("Extract key details such as Name, DOB, Address.")

    return response.response

def process_existing_documents():
    """Fetches all documents from the database and processes them."""
    response = supabase_client.table("documents").select("*").execute()

    if response.data:
        for doc in response.data:
            file_url = doc["url"]
            file_name = doc["filename"]
            file_extension = file_name.split(".")[-1].lower()  # Extract file type from filename
            username = doc["user"]  # Assuming "user" is stored instead of "username"

            if file_extension in ["png", "jpg", "jpeg", "tiff", "bmp", "webp"]:
                extracted_text = extract_text_from_image(file_url)
                document_type = "image"
            elif file_extension == "pdf":
                extracted_text = extract_data_from_pdf(file_url)
                document_type = "pdf"
            else:
                continue  # Skip unsupported file types

            # ✅ Fix: Pass all required arguments
            save_kyc_data(username, document_type, extracted_text, file_url)

def save_kyc_data(username, document_type, extracted_data, file_url):
    """Saves extracted KYC details into the Supabase database."""
    data = {
        "username": username,
        "document_type": document_type,
        "extracted_data": json.dumps(extracted_data),
        "original_file_url": file_url
    }

    response = supabase_client.table("kyc_data").insert(data).execute()
    return response

def fetch_all_usernames():
    """Fetches all unique usernames from the KYC database."""
    response = supabase_client.table("kyc_data").select("username").execute()
    if response.data:
        return list(set([entry["username"] for entry in response.data]))  # Get unique usernames
    return []

def fetch_user_kyc_details(username):
    """Fetches KYC details of a selected user."""
    response = supabase_client.table("kyc_data").select("*").eq("username", username).execute()
    if response.data:
        return response.data
    return []

def generate_summary(extracted_data):
    """Uses Gemini API to summarize extracted KYC details."""
    prompt = f"Summarize the following KYC data:\n{extracted_data}"
    response = llm.complete(prompt)
    return response.text

def know_your_customer():
    st.title("Know Your Customer (KYC)")

    # Fetch all usernames
    usernames = fetch_all_usernames()

    if not usernames:
        st.warning("No KYC data found.")
        return

    # Dropdown to select a user
    selected_user = st.selectbox("Select a User", usernames)

    if selected_user:
        # Fetch and display user's KYC details
        kyc_details = fetch_user_kyc_details(selected_user)

        if kyc_details:
            unique_entries = {json.dumps(entry, sort_keys=True) for entry in kyc_details}  # Remove duplicates

            for entry_json in unique_entries:
                entry = json.loads(entry_json)  # Convert back to dictionary
                
                st.subheader(f"Details for {selected_user}")
                st.write(f"**Document Type:** {entry['document_type']}")
                st.write(f"**Extracted Data:** {entry['extracted_data']}")
                st.write(f"[View Original Document]({entry['original_file_url']})")

                # Generate and display summary using Gemini API
                summary = generate_summary(entry["extracted_data"])
                st.subheader("Gemini AI Summary:")
                st.write(summary)

        else:
            st.warning("No details found for this user.")

