# ReportGen: AI-Powered LaTeX Report Generator

ReportGen is a powerful tool that leverages Large Language Models (LLMs) like Google's Gemini API and Retrieval Augmented Generation (RAG) to automatically generate professional LaTeX reports from user queries. It features a user-friendly Angular frontend and a robust FastAPI backend.

## Features

*   **AI-Powered Content Generation:** Uses Gemini API for generating report sections (Introduction, Main Content, Conclusion, Bibliography, Appendices).
*   **Retrieval Augmented Generation (RAG):** Enhances factual accuracy by retrieving relevant information from a knowledge base (powered by ChromaDB and Sentence Transformers).
*   **LaTeX Output:** Produces high-quality, professional `.tex` documents.
*   **PDF Compilation:** Includes functionality to compile the generated `.tex` file into a PDF using MiKTeX (or another LaTeX distribution).
*   **Customizable Reports:** Users can specify title, authors, mentors, university, date, primary color, and an optional logo.
*   **User-Uploaded Figures:** Allows users to upload a figure and caption to be included in the report.
*   **Multi-Agent Architecture:** Modular design with specialized agents for different parts of the report (TOC, Cover, Main Content, etc.).
*   **Modern Tech Stack:**
    *   **Frontend:** Angular
    *   **Backend:** FastAPI (Python)
    *   **LLM:** Google Gemini API
    *   **Vector Database (RAG):** ChromaDB
    *   **Embeddings (RAG):** Sentence Transformers
    *   **LaTeX Distribution (for compilation):** MiKTeX (or similar like TeX Live)

## Getting Started

### Prerequisites

*   Python 3.9+
*   Node.js and npm (for Angular frontend)
*   A LaTeX distribution installed (e.g., MiKTeX for Windows, TeX Live for Linux/macOS) and `pdflatex` added to your system's PATH.
*   A Google Gemini API Key.

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/ReportGen.git
    cd ReportGen/backend
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You'll need to create a `requirements.txt` file - see below)*
4.  **Set up environment variables:**
    Create a `.env` file in the `backend/` directory (this file is ignored by Git):
    ```env
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    # Optional: If your RAG PDF folder or ChromaDB path is different from defaults
    # PDF_FOLDER="data/your_pdfs"
    # CHROMA_DB_PATH="custom_embeddings_db"
    ```
5.  **Run the RAG data ingestion script (if you have one):**
    *(Describe how to ingest data for RAG if applicable, e.g., `python src/ingest_data.py`)*
6.  **Start the FastAPI server:**
    ```bash
    uvicorn main_api:app --host 0.0.0.0 --port 5000 --reload
    ```

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend 
    ```
    (Assuming you are in `ReportGen/backend` from previous step, otherwise `cd ReportGen/frontend`)
2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```
3.  **Run the Angular development server:**
    ```bash
    ng serve
    ```
    The application will be accessible at `http://localhost:4200`.

## Usage

1.  Ensure both the backend and frontend servers are running.
2.  Open your browser and navigate to `http://localhost:4200`.
3.  Fill in the report details in the form:
    *   Report Title
    *   Topic/Description (This is the main prompt for the AI)
    *   Authors, Mentors, Date, University
    *   Upload an optional logo.
    *   Upload an optional figure and provide a caption.
    *   Choose a primary color for the report.
    *   Optionally disable RAG.
4.  Click "Generate My Report!".
5.  The generated PDF (or `.tex` file if PDF compilation fails) will be downloaded by your browser.
 
