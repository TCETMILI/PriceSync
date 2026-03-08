FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (PyMuPDF ve benzeri kütüphaneler için gerekli olabilir)
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodları docker-compose ile volume üzerinden mount edileceği için
# burada COPY işlemi yapmıyoruz (geliştirme ortamı için).

CMD ["python", "main.py"]
