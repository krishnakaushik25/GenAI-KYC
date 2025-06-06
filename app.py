import streamlit as st
from document_management import upload_documents, fetch_documents
from process import process_documents  # Import the process function
import supabase
from kyc import know_your_customer
from see_user_docs import see_user_documents
from database import supabase_client
from easy_kyc import easy_kyc

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
            width: 100% !important; /* ✅ Ensures button fills sidebar width */
            height: 50px; /* ✅ Adjusts button height for better visibility */
            font-size: 16px;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .sidebar .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 5px 5px 12px rgba(0, 0, 0, 0.4);
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Ensure session state variables exist
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "user_logged_in" not in st.session_state:
    st.session_state["user_logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

def get_logged_in_user():
    """Fetch the logged-in user's details from session state."""
    return st.session_state.get("username")

def is_admin(username):
    """Check if the user exists in the 'admin' table."""
    if username:
        print(f"Checking if '{username}' exists in admin table...")  # Debug print
        response = supabase_client.table("admin").select("username").eq("username", username).execute()
        print("Response from Supabase:", response)  # Debug print
        return len(response.data) > 0  # True if found, False if empty
    return False

# Get logged-in user ID from session state
username = get_logged_in_user()
is_admin_user = is_admin(username) if username else False  # ✅ Avoids calling with None

# Sidebar Navigation
st.sidebar.title("Navigation")

if st.sidebar.button("Home", use_container_width=True):
    st.session_state["page"] = "home"

if not st.session_state["user_logged_in"]:
    if st.sidebar.button("Sign In", use_container_width=True):
        st.session_state["page"] = "signin"
    if st.sidebar.button("Sign Up", use_container_width=True):
        st.session_state["page"] = "signup"
else:
    st.sidebar.write(f"Logged in as **{st.session_state['username']}**")

    if st.sidebar.button("Upload Documents", use_container_width=True):
        st.session_state["page"] = "upload_documents"
    if st.sidebar.button("Fetch Documents", use_container_width=True):
        st.session_state["page"] = "fetch_documents"

    if is_admin_user:
        if st.sidebar.button("See All User Documents (admin)", use_container_width=True):
            st.session_state["page"] = "see_user_documents"
        if st.sidebar.button("Generate KYC Details", use_container_width=True):
            st.session_state["page"] = "know_your_customer"
        if st.sidebar.button("Easy KYC", use_container_width=True):
            st.session_state["page"] = "KYC"

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state["user_logged_in"] = False
        st.session_state["username"] = None
        st.session_state["page"] = "home"
        st.rerun()

# Page Navigation Logic
if st.session_state["page"] == "home":
    st.title("Welcome to KYC")
    st.write(f"This is the home page. Welcome {st.session_state.get('username')}!")

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

elif st.session_state["page"] == "see_user_documents":
    see_user_documents()

elif st.session_state["page"] == "know_your_customer":
    know_your_customer()

elif st.session_state["page"] == "KYC":
    easy_kyc()
