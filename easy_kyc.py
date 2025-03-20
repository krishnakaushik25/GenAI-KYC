import streamlit as st
from database import supabase_client
import google.generativeai as genai
import os

# Configure Gemini API from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Load Gemini model
model = genai.GenerativeModel(model_name="gemini-1.5-pro")


def fetch_usernames():
    """Fetch unique usernames from the kyc_data table."""
    response = supabase_client.table("kyc_data").select("username").execute()
    if response.data:
        return list(set(entry["username"] for entry in response.data))
    return []


def fetch_extracted_text(username):
    """Fetch all extracted_data for a given username."""
    response = supabase_client.table("kyc_data").select("extracted_data").eq("username", username).execute()
    return [entry["extracted_data"] for entry in response.data] if response.data else []


def generate_ai_response(user_input, kyc_texts):
    """Use Gemini-1.5-Pro to chat with the KYC data."""
    combined_text = "\n".join(kyc_texts)
    prompt = f"User's KYC Information:\n{combined_text}\n\nUser Query: {user_input}\n\nAnswer:"

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, "text") else "I'm unable to generate a response."
    except Exception as e:
        return f"Error in AI response: {str(e)}"


def easy_kyc():
    """Streamlit UI for Easy KYC."""
    st.title("🔍 Easy KYC - AI Chatbot for KYC Data")

    # Ensure conversation history exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Step 1: Select a username
    usernames = fetch_usernames()
    if not usernames:
        st.warning("No user data available.")
        return

    selected_user = st.selectbox("Select a user:", usernames)

    # Step 2: Fetch extracted text
    if selected_user:
        kyc_texts = fetch_extracted_text(selected_user)

        if not kyc_texts:
            st.warning("No extracted text found for this user.")
            return

        # Display extracted text preview
        with st.expander("📜 View Extracted KYC Data"):
            for idx, text in enumerate(kyc_texts, start=1):
                st.text_area(f"Document {idx}", text, height=100)

        # Step 3: Chatbot Interaction
        st.subheader("💬 AI-Powered KYC Assistant")

        # Display message history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # User input field
        user_query = st.chat_input("Ask about this user's KYC details...")

        if user_query:
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": user_query})

            # Get AI response
            ai_response = generate_ai_response(user_query, kyc_texts)

            # Add AI response to session state
            st.session_state.messages.append({"role": "bot", "content": ai_response})

            # Display the latest AI response
            with st.chat_message("bot"):
                st.markdown(ai_response)
