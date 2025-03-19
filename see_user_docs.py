import streamlit as st
import pandas as pd
from database import get_all_documents

def see_user_documents():
    st.title("View User Documents")

    if st.session_state.get("user_logged_in", False):
        # Fetch all documents from the database table
        all_documents = get_all_documents()

        if not all_documents or isinstance(all_documents, type(None)):
            st.warning("No documents found.")
            return

        # Convert the document data into a DataFrame
        df = pd.DataFrame(all_documents)

        # Ensure required columns exist
        required_columns = {"document_id", "user", "type", "filename", "url", "timestamp"}
        if not required_columns.issubset(df.columns):
            st.warning(f"Missing columns: Expected {required_columns}, found {set(df.columns)}")
            return

        # Modify the "url" column to display clickable links with text
        df["url"] = df["url"].apply(lambda link: f'<a href="{link}" target="_blank">View Document</a>')

        # Display the table with clickable links
        st.write("### All Documents")
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    else:
        st.warning("Please sign in to view documents.")
