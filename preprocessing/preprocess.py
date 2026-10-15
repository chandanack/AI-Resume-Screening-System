import pdfplumber
from docx import Document
import re


def extract_text_from_pdf(file_path):
    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


def extract_text_from_docx(file_path):
    text = ""

    document = Document(file_path)

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def clean_text(text):
    text = text.lower()

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    text = text.strip()

    return text


def tokenize_text(text):
    tokens = text.split()

    return tokens