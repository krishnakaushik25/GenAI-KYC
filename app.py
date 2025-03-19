import streamlit as st
from document_management import upload_documents, fetch_documents

# Page configuration
st.set_page_config(page_title="GenAI-KYC", layout="wide")

# Custom CSS for button styling
st.markdown(
    """
    <style>
        .sidebar .stButton>button {
            background-color: #4CAF50; /* Green */
            color: white;
            border-radius: 8px;
            box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.3);
            transition: 0.3s;
            width: 100%;
            font-size: 16px;
        }
        .sidebar .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 5px 5px 12px rgba(0, 0, 0, 0.4);
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "user_logged_in" not in st.session_state:
    st.session_state["user_logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

# Sidebar Navigation
st.sidebar.title("Navigation")

if st.sidebar.button("Home"):
    st.session_state["page"] = "home"

if not st.session_state["user_logged_in"]:
    if st.sidebar.button("Sign In"):
        st.session_state["page"] = "signin"
    if st.sidebar.button("Sign Up"):
        st.session_state["page"] = "signup"
else:
    if st.sidebar.button("Upload Documents"):
        st.session_state["page"] = "upload_documents"
    if st.sidebar.button("Fetch Documents"):
        st.session_state["page"] = "fetch_documents"
    if st.sidebar.button("Logout"):
        st.session_state["user_logged_in"] = False
        st.session_state["user_name"] = None
        st.session_state["page"] = "home"
        st.rerun()

# Page Navigation Logic
if st.session_state["page"] == "home":
    st.title("Welcome to KYC")
    user = st.session_state.get("username")
    st.write(f"This is the home page. Welcome {user}")

elif st.session_state["page"] == "signin":
    from login_page import login
    login()

elif st.session_state["page"] == "signup":
    from signup_page import sign_up
    sign_up()

elif st.session_state["page"] == "upload_documents":
    upload_documents()

elif st.session_state["page"] == "fetch_documents":
    fetch_documents()
