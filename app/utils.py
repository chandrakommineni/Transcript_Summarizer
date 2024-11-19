import os
from dotenv import load_dotenv
import docx
from win32com.client import Dispatch

def load_env_variables():
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise EnvironmentError("Google API Key not found in .env file.")
    return google_api_key

# Function to log number of input and output tokens
def log_tokens(input_text: str, output_text: str):
    input_tokens = len(input_text.split())
    output_tokens = len(output_text.split())
    return input_tokens, output_tokens

# Function to read DOC file content
def read_doc_file(file):
    word = Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(file.name)
    text = doc.Range().Text
    doc.Close()
    word.Quit()
    return text