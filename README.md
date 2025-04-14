# GenAI-KYC: AI-Based Know Your Customer Automation System

GenAI-KYC is a full-stack AI-powered application built using **Streamlit**, **Google Gemini**, and **Supabase** to streamline the KYC process. It uses document upload, OCR, and LLM-based extraction to simplify data collection and verification.


## Project Purpose

This project automates and accelerates the Know Your Customer (KYC) process using:
- Document Upload & OCR
- AI-driven field extraction (Gemini API)
- Easy-to-use web UI (Streamlit)
- Data storage in Supabase


## Tech Stack

| Layer       | Technology Used                    |
|------------|-------------------------------------|
| Frontend   | Streamlit (Python)                  |
| AI         | Google Gemini (Generative AI)       |
| OCR        | Tesseract, PyMuPDF, PDFMiner        |
| Backend DB | Supabase (PostgreSQL + API)         |

## How to Run

### 1. Clone the Repository

git clone https://github.com/your-username/GenAI-KYC.git

cd GenAI-KYC

### 2. Install Dependencies

pip install -r requirements.txt

### 3. Add Tessseract to path

Install Tesseract:

Download from: https://github.com/UB-Mannheim/tesseract/wiki

Install to: C:\Program Files\Tesseract-OCR

Add to System PATH:

Go to System Environment Variables → Edit PATH → Add:

C:\Program Files\Tesseract-OCR

Verify in CMD:

tesseract --version

In Python:

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

### 4. Start the Application

streamlit run app.py
