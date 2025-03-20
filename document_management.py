import streamlit as st
from database import upload_to_supabase, save_document_metadata, get_all_documents, delete_document

def upload_documents():
    st.title("Upload Documents")

    if st.session_state.get("user_logged_in", False):
        user = st.session_state.get("username", "Guest")

        # Select document type
        doc_type = st.selectbox("Select Document Type", ["ID Proof", "Address Proof", "Payroll Document", "Other"])
        
        if doc_type == "Other":
            doc_type = st.text_input("Enter Document Type")

        # Upload file
        uploaded_files = st.file_uploader("Upload your documents", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)
        
        if uploaded_files:
            for file in uploaded_files:
                file_url, error = upload_to_supabase(file, user, doc_type)
                
                if error:
                    st.error(f"Failed to upload {file.name}")
                    continue
                
                save_document_metadata(user, doc_type, file.name, file_url)
                st.success(f"Uploaded {file.name}")

    else:
        st.warning("Please sign in to upload documents.")

def fetch_documents():
    st.title("Fetch Documents")

    if st.session_state.get("user_logged_in", False):
        user = st.session_state.get("username", "Guest")

        # Fetch documents from Supabase
        user_docs = [doc for doc in get_all_documents() if doc["user"] == user]

        if user_docs:
            st.write("Uploaded Documents:")
            df = st.dataframe(user_docs)

            # Select document to delete
            doc_to_delete = st.selectbox("Select a document to delete", [doc["document_id"] for doc in user_docs])

            if st.button("Delete Document"):
                doc = next((d for d in user_docs if d["document_id"] == doc_to_delete), None)

                if doc:
                    delete_document(doc["document_id"], doc["user"], doc["type"], doc["filename"])
                    st.success(f"Deleted document {doc_to_delete}")
                    st.rerun()

        else:
            st.write("No documents found.")

    else:
        st.warning("Please sign in to fetch documents.")

