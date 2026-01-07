FROM python:3.11-slim

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Download VADER lexicon once at build time (so container runs offline)
RUN python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

COPY app.py /app/app.py
COPY prepare_data.py /app/prepare_data.py

EXPOSE 8050
CMD ["python", "app.py"]
