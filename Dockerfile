FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Ajoute le pack de langue français
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils tesseract-ocr tesseract-ocr-fra gcc libpq-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "rh_project.wsgi:application", "--bind", "0.0.0.0:8000"]
