from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials are missing. Check your .env file.")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "kyc-documents"  # Name of the storage bucket


# Function to upload file to Supabase Storage
def upload_to_supabase(file, user, doc_type):
    file_name = f"{user}/{doc_type}/{file.name}"

    # Read file as binary
    file_content = file.getvalue()

    # Upload file to Supabase Storage
    response = supabase_client.storage.from_(BUCKET_NAME).upload(file_name, file_content)

    if response is None:
        return None, "Error uploading file to Supabase"

    # Get public URL of uploaded file
    file_url = supabase_client.storage.from_(BUCKET_NAME).get_public_url(file_name)

    return file_url, None


# Function to generate unique document ID
def generate_document_id():
    docs = get_all_documents()
    
    if not docs:
        return "DOC001"
    
    last_doc_id = sorted(docs, key=lambda x: x["document_id"], reverse=True)[0]["document_id"]
    
    last_number = int(last_doc_id.replace("DOC", ""))
    new_id = f"DOC{last_number + 1:03d}"
    
    return new_id


# Function to save document metadata in Supabase Database
def save_document_metadata(user, doc_type, file_name, file_url):
    doc_id = generate_document_id()  # Generate unique ID

    data = {
        "document_id": doc_id,
        "user": user,
        "type": doc_type,
        "filename": file_name,
        "url": file_url,
        "timestamp": "now()"
    }

    response = supabase_client.table("documents").insert(data).execute()

    # 🔹 Correct way to check for errors
    if response.data is None:  # If there's no data, something went wrong
        return None, "Error saving document metadata to database"

    return doc_id, None

# Function to retrieve all documents from Supabase
def get_all_documents():
    response = supabase_client.table("documents").select("*").execute()
    return response.data if response.data else []

def download_file_from_supabase(document_id):
    """Download file from Supabase storage and return file bytes."""
    try:
        response = supabase_client.storage.from_("documents").download(document_id)
        return response  # Returns file bytes
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

# Function to delete a document from Supabase
def delete_document(doc_id, user, doc_type, filename):
    file_path = f"{user}/{doc_type}/{filename}"

    # Delete file from Supabase Storage
    storage_response = supabase_client.storage.from_("kyc-documents").remove([file_path])

    # 🔹 Correct way to check for errors
    if isinstance(storage_response, list) and len(storage_response) > 0 and "error" in storage_response[0]:
        return False, f"Error deleting file from storage: {storage_response[0]['error']}"

    # Remove document metadata from Supabase Database
    response = supabase_client.table("documents").delete().eq("document_id", doc_id).execute()

    if hasattr(response, "error") and response.error:
        return False, f"Error deleting document from database: {response.error.message}"

    return True, None

def get_all_documents():
    """Fetch all documents from the database."""
    response = supabase_client.table("documents").select("*").execute()

    if response and hasattr(response, 'data') and response.data is not None:
        return response.data  # Ensure it returns a list
    
    return []  # Return an empty list if no data is found
