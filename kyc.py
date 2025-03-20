import pytesseract
from PIL import Image
import streamlit as st
import json
import tempfile
import os
import io
import pymupdf
fitz = pymupdf
from pdfminer.high_level import extract_text
import requests
from dotenv import load_dotenv
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Document, Settings, SimpleDirectoryReader, VectorStoreIndex
from database import supabase_client  # Ensure this is properly configured

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
llm = Gemini(api_key=GEMINI_API_KEY)
embed_model = GeminiEmbedding(api_key=GEMINI_API_KEY)
Settings.embed_model = embed_model

# Set Tesseract OCR Path
pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\\tesseract.exe"

# Supabase bucket name
BUCKET_NAME = "kyc-documents"


def list_users():
    """Fetches user folders inside the 'kyc-documents' bucket."""
    response = supabase_client.storage.from_(BUCKET_NAME).list()
    if response:
        return [folder["name"] for folder in response if folder["name"] != ".emptyFolder"]
    return []


def list_subfolders(username):
    """Lists subfolders inside a user's folder (e.g., 'Address Proof', 'ID Proof')."""
    response = supabase_client.storage.from_(BUCKET_NAME).list(username + "/")
    if response:
        return [folder["name"] for folder in response if folder["name"] != ".emptyFolder"]
    return []


def list_files_in_subfolders(username, subfolders):
    """Fetches all actual files inside the selected subfolders."""
    files_to_process = []
    for folder in subfolders:
        folder_path = f"{username}/{folder}/"
        response = supabase_client.storage.from_(BUCKET_NAME).list(folder_path)
        if response:
            for file in response:
                files_to_process.append(f"{folder}/{file['name']}")  # Store relative path
    return files_to_process


def download_file(username, file_path):
    """Downloads a file from the selected user's subfolder in Supabase Storage."""
    full_path = f"{username}/{file_path}"
    file_url = supabase_client.storage.from_(BUCKET_NAME).get_public_url(full_path)

    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name, file_url  # Return local file path and file URL
    else:
        raise Exception(f"Failed to download file: {file_url}")


def extract_text_from_image(file_path):
    """Extracts text from an image file."""
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text.strip()


def extract_text_from_pdf(file_path):
    """Extract text from a PDF. Uses pdfminer.six for digital PDFs and Tesseract OCR for scanned PDFs."""
    try:
        # Try extracting text normally
        text = extract_text(file_path).strip()
        if text:
            return text  # ✅ Return if text is found

        # If no text is found, apply OCR using PyMuPDF
        doc = fitz.open(file_path)
        ocr_text = []

        for page in doc:
            pix = page.get_pixmap()  # Render page as an image
            img = Image.open(io.BytesIO(pix.tobytes("png"))) # Convert to PIL image
            ocr_text.append(pytesseract.image_to_string(img))  # Perform OCR

        extracted_text = "\n".join(ocr_text).strip()
        return extracted_text if extracted_text else "No extractable text found in the PDF."

    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"


def process_selected_documents(username, file_list):
    """Processes selected documents for a user."""
    for file_name in file_list:
        local_file_path, file_url = download_file(username, file_name)
        file_extension = file_name.split(".")[-1].lower()

        st.write(f"📂 Processing: {file_name} (Type: {file_extension})")  # Debug log

        if file_extension in ["png", "jpg", "jpeg", "tiff", "bmp", "webp"]:
            extracted_text = extract_text_from_image(local_file_path)
            document_type = "image"
        elif file_extension == "pdf":
            extracted_text = extract_text_from_pdf(local_file_path)  # ✅ Calls correct function
            document_type = "pdf"
        else:
            st.error(f"❌ Unsupported file format: {file_name}")
            continue  # Skip unsupported files

        save_kyc_data(username, document_type, extracted_text, file_url)
        st.success(f"✅ {file_name} processed successfully!")
        st.subheader(f"Extracted Data from {file_name}:")
        st.write(extracted_text)



def save_kyc_data(username, document_type, extracted_data, file_url):
    """Saves extracted KYC details into Supabase."""
    data = {
        "username": username,
        "document_type": document_type,
        "extracted_data": json.dumps(extracted_data),
        "original_file_url": file_url,
    }
    response = supabase_client.table("kyc_data").insert(data).execute()
    return response


def know_your_customer():
    st.title("Know Your Customer (KYC)")

    # **Step 1: Select User Folder**
    users = list_users()
    if not users:
        st.warning("No users found in the database.")
        return

    selected_user = st.selectbox("Select a User", users)

    if selected_user:
        # **Step 2: Select Multiple Folders**
        subfolders = list_subfolders(selected_user)
        if not subfolders:
            st.warning(f"No folders found inside {selected_user}.")
            return

        selected_folders = st.multiselect("Select Folders", subfolders)

        if selected_folders:
            # **Step 3: Fetch all actual files inside selected folders**
            files_to_process = list_files_in_subfolders(selected_user, selected_folders)

            if not files_to_process:
                st.warning("No files found inside selected folders.")
                return

            if st.button("Process Documents"):
                process_selected_documents(selected_user, files_to_process)
