import re


def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()