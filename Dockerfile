FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# tesseract-ocr-heb: PDF OCR fallback and image OCR both need Hebrew support
# (see docs/ARCHITECTURE.md); eng is included by tesseract-ocr by default.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-heb && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# unstructured's markdown/HTML partitioning (used by DirectoryLoader) needs
# this NLTK data (sentence tokenizer + POS tagger); not bundled with the pip
# package, and only surfaces at parse time, not at import time.
RUN python -m nltk.downloader punkt_tab averaged_perceptron_tagger_eng -d /usr/local/nltk_data

EXPOSE 8501

CMD ["sh", "-c", "python -c 'from vector_store import create_vector_store; create_vector_store()' && streamlit run app.py --server.address=0.0.0.0"]
