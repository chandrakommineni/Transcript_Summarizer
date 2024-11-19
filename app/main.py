import streamlit as st
import os
import logging
from templates import templates
from ai_handlers import AIHandler
from utils import load_env_variables, log_tokens, read_doc_file
import google.generativeai as genai
import docx

# Configure logger
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load environment variables
google_api_key = load_env_variables()

# Configure Google Generative AI
genai.configure(api_key=google_api_key)

# Initialize AI handler
ollama_base_url = "http://uatml1.itrans.int:11434/"
ollama_model = "llama3.1"
ai_handler = AIHandler(ollama_base_url, ollama_model)

# Streamlit page configuration
st.set_page_config(
    page_title="IntelliTrans Meeting Summary",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar: Template Selection
with st.sidebar:
    st.image("assets/IntelliTrans.png", use_container_width=True)
    st.subheader("1. Select Meeting Type")
    meeting_type = st.selectbox(
        "Choose Template",
        options=list(templates.keys()),
        format_func=lambda x: f"{templates[x]['icon']} {x}"
    )
    st.info(templates[meeting_type]["description"], icon="ℹ️")

    # Sidebar: AI Model Selection
    st.subheader("2. Choose AI Model")
    model_choice = st.radio(
        "Select Processing Engine",
        options=["Gemini Pro", "Ollama"],
        format_func=lambda x: f"{'' if x == 'Ollama' else '✨'} {x}"
    )

    # Sidebar: Transcript Input
    st.subheader("3. Input Transcript")
    input_method = st.radio("Choose input method", options=["Upload File", "Paste Text"])
    if input_method == "Upload File":
        uploaded_file = st.file_uploader("", type=["txt", "docx", "doc"])
    else:
        transcript_text = st.text_area("Paste your transcript here", height=200)

# Main Content Area
st.title("Meeting Summary Generator")
if st.button("Generate Summary", key="generate_btn"):
    transcript = ""
    if uploaded_file is not None:
        # Handle uploaded file
        if uploaded_file.type == "text/plain":
            transcript = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            transcript = "".join(paragraph.text for paragraph in doc.paragraphs)
        elif uploaded_file.type == "application/msword":
            try:
                transcript = read_doc_file(uploaded_file)
            except Exception as e:
                st.error(f"Error processing DOC file: {e}")
                logging.error(f"Error reading DOC file: {e}")
        else:
            st.error("Unsupported file format. Please upload a TXT, DOCX, or DOC file.")
            logging.warning(f"User uploaded unsupported file type: {uploaded_file.type}")
    else:
        transcript = transcript_text.strip()

    if transcript:
        with st.spinner("Processing your transcript..."):
            prompt = templates[meeting_type]["prompt"]
            # Choose AI Model
            if model_choice == "Gemini Pro":
                response = ai_handler.generate_summary_gemini(transcript, prompt)
            else:
                response = ai_handler.generate_summary_ollama(transcript, prompt)
            
            # Log number of tokens
            input_tokens, output_tokens = log_tokens(transcript, response)

        st.subheader("📋 Meeting Summary")
        st.write(response)
        st.download_button("Download Summary", response, file_name="summary.txt", mime="text/plain")
        
        logging.info(f"Summary generated. Input tokens: {input_tokens}, Output tokens: {output_tokens}")

        # Feedback Section
        st.subheader("Feedback")
        feedback = st.text_input("Provide your feedback here")
        print(f'feedback : {feedback}' )

        # Use session state for rating
        if "rating" not in st.session_state:
            st.session_state.rating = 3  # Default rating value

        st.session_state.rating = st.slider("Rate the quality of the summary", 1, 5, st.session_state.rating)

        # Show current feedback and rating on screen for debugging
        st.write(f"Your Feedback: {feedback}")
        st.write(f"Your Rating: {st.session_state.rating}")
        print('after rating')

        # Submit Feedback Button
        if st.button("Submit Feedback", key="feedback_btn"):
            if feedback.strip():  # Check if feedback is not empty
                st.success("Thank you for your feedback!")
                logging.info(f"User feedback: {feedback}, Rating: {st.session_state.rating}")
            else:
                st.warning("Please provide a transcript to process.")
                logging.warning("User did not provide a transcript.")