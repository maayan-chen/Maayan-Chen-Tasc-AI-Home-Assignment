FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# unstructured's markdown/HTML partitioning (used by DirectoryLoader) needs
# this NLTK data (sentence tokenizer + POS tagger); not bundled with the pip
# package, and only surfaces at parse time, not at import time.
RUN python -m nltk.downloader punkt_tab averaged_perceptron_tagger_eng -d /usr/local/nltk_data

CMD ["sh", "-c", "python -c 'from vector_store import create_vector_store; create_vector_store()' && tail -f /dev/null"]
